from __future__ import annotations

import os
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Dict, List, Optional

from cv_engine.metrics import detect_impact
from cv_engine.pose.base import Keypoint as PoseKeypoint, PoseFrame
from cv_engine.pose.mediapipe_adapter import MediapipePoseAdapter
from cv_engine.pose.movenet_adapter import MoveNetPoseAdapter
from cv_engine.tracking.base import Detection, TrackedDetection
from cv_engine.tracking.factory import create_tracker
from metrics import angle, ball, carry_v1, club
from opentelemetry import trace
from fastapi import HTTPException, status

from server.schemas.coach import (
    CoachChatBody,
    CoachWeeklySummaryBody,
    ValidationError as CoachValidationError,
)
from server.testing import MiniAPI
from server import ar_targets
from server.routes import billing as billing_routes
from server.security.entitlements import require_entitlement
from server.services.telemetry import emit as emit_telemetry
from siq.coach import (
    CoachChatRequest,
    CoachResponder,
    PersonaProfile,
    PersonaPreferenceStore,
    PersonaRegistry,
    RunHistory,
    WeeklySummaryJob,
)
from siq.observability import cv_stage, record_frame_inference

app = MiniAPI()


def _register_get(path: str):
    def decorator(func):
        app.routes[("GET", path)] = func
        return func

    return decorator


def _call_handler(
    method: str,
    path: str,
    *,
    json: Dict[str, Any] | None = None,
    query: Dict[str, Any] | None = None,
    headers: Dict[str, Any] | None = None,
):
    handler = app.routes.get((method.upper(), path))
    if handler is None:
        raise KeyError("route not registered")
    if method.upper() == "GET":
        return handler(query or {}, headers or {})
    return handler(json or {}, headers or {})


app.get = _register_get  # type: ignore[attr-defined]


def _app_call_handler(method: str, path: str, json=None, query=None, headers=None):
    return _call_handler(method, path, json=json, query=query, headers=headers)


app.call_handler = _app_call_handler  # type: ignore[attr-defined]

telemetry_broker = ar_targets.TelemetryBroker()
target_run_store = ar_targets.TargetRunStore()

_persona_registry = PersonaRegistry()
_persona_store = PersonaPreferenceStore(_persona_registry)
coach_responder = CoachResponder(
    preferences=_persona_store,
    registry=_persona_registry,
)
run_history = RunHistory()
weekly_summary_job = WeeklySummaryJob(run_history, registry=_persona_registry)

_TRACER = trace.get_tracer("siq.cv")


def _resolve_persona_or_422(user_id: str, persona_alias: str | None) -> PersonaProfile:
    try:
        if persona_alias:
            return _persona_store.set_preference(user_id, str(persona_alias))
        return _persona_store.get_preference(user_id)
    except ValueError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"status": "error", "reason": "unknown persona"},
        )

@dataclass
class TrackPoint:
    frame: int
    bbox: List[float]

    @classmethod
    def from_dict(cls, payload: Dict[str, float | int]) -> "TrackPoint":
        return cls(frame=int(payload["frame"]), bbox=list(payload["bbox"]))


@dataclass
class PoseKeypointModel:
    name: str
    x: float
    y: float

    @classmethod
    def from_dict(cls, payload: Dict[str, float | str]) -> "PoseKeypointModel":
        return cls(name=str(payload["name"]), x=float(payload["x"]), y=float(payload["y"]))


@dataclass
class PoseFrameModel:
    frame: int
    keypoints: List[PoseKeypointModel]

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "PoseFrameModel":
        return cls(
            frame=int(payload["frame"]),
            keypoints=[PoseKeypointModel.from_dict(kp) for kp in payload.get("keypoints", [])],
        )


@dataclass
class BackAnalyzeRequest:
    fps: float
    shutter_us: Optional[float]
    ref_len_m: float
    ref_len_px: float
    ball: List[TrackPoint]
    club: List[TrackPoint]
    pose: List[PoseFrameModel]
    homography: Optional[List[List[float]]]

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "BackAnalyzeRequest":
        return cls(
            fps=float(payload.get("fps", 0.0)),
            shutter_us=float(payload["shutter_us"]) if payload.get("shutter_us") is not None else None,
            ref_len_m=float(payload.get("ref_len_m", 0.0)),
            ref_len_px=float(payload.get("ref_len_px", 0.0)),
            ball=[TrackPoint.from_dict(tp) for tp in payload.get("ball", [])],
            club=[TrackPoint.from_dict(tp) for tp in payload.get("club", [])],
            pose=[PoseFrameModel.from_dict(frame) for frame in payload.get("pose", [])],
            homography=payload.get("homography"),
        )


def _to_detections(points: List[TrackPoint]) -> List[Detection]:
    return [Detection(frame=p.frame, bbox=tuple(p.bbox)) for p in points]


def _to_pose_frames(frames: List[PoseFrameModel]) -> List[PoseFrame]:
    return [
        PoseFrame(frame=f.frame, keypoints=[PoseKeypoint(name=kp.name, x=kp.x, y=kp.y) for kp in f.keypoints])
        for f in frames
    ]


@app.post("/cv/back/analyze")
def analyze_back_view(payload: Dict[str, object], headers: Dict[str, str]) -> Dict[str, object]:
    request = BackAnalyzeRequest.from_dict(payload)
    tracker = create_tracker()
    total_start = perf_counter()

    with _TRACER.start_as_current_span("cv.pipeline") as pipeline_span:
        pipeline_span.set_attribute("cv.pipeline.fps", request.fps)
        pipeline_span.set_attribute("cv.pipeline.tracker", tracker.name)

        with cv_stage("detect") as detect_span:
            ball_detections = _to_detections(request.ball)
            club_detections = _to_detections(request.club)
            detect_span.set_attribute("cv.detect.ball_count", len(ball_detections))
            detect_span.set_attribute("cv.detect.club_count", len(club_detections))

        with cv_stage("track") as track_span:
            ball_tracks = tracker.track(ball_detections)
            club_tracks = tracker.track(club_detections)
            track_span.set_attribute("cv.track.ball_tracks", len(ball_tracks))
            track_span.set_attribute("cv.track.club_tracks", len(club_tracks))

        with cv_stage("impact") as impact_span:
            impact = detect_impact(ball_tracks, club_tracks, request.fps)
            impact_span.set_attribute("cv.impact.frame", impact.frame)
            impact_span.set_attribute("cv.impact.confidence", impact.confidence)

        with cv_stage("metrics") as metrics_span:
            m_per_px = ball.meters_per_pixel(request.ref_len_m, request.ref_len_px)

            def to_points(tracks: List[TrackedDetection]):
                return [
                    (t.frame, t.bbox[0] + t.bbox[2] / 2.0, t.bbox[1] + t.bbox[3] / 2.0)
                    for t in sorted(tracks, key=lambda x: x.frame)
                ]

            ball_points = to_points(ball_tracks)
            club_points = to_points(club_tracks)

            ball_speed = ball.ball_speed_mps(ball_points, request.fps, m_per_px)
            club_speed = club.club_speed_pre_impact(club_points, impact.frame, request.fps, m_per_px)
            side_angle = angle.side_angle_deg(ball_points)
            carry = carry_v1.carry_distance_m(ball_speed, side_angle)

            metrics_span.set_attribute("cv.metrics.ball_speed_mps", ball_speed)
            metrics_span.set_attribute("cv.metrics.club_speed_mps", club_speed)
            metrics_span.set_attribute("cv.metrics.side_angle_deg", side_angle)
            metrics_span.set_attribute("cv.metrics.carry_est_m", carry)

            pose_frames = _to_pose_frames(request.pose)
            pose_adapter = (
                MediapipePoseAdapter()
                if os.getenv("GOLFIQ_POSE", "mediapipe") == "mediapipe"
                else MoveNetPoseAdapter()
            )
            pose_summary = pose_adapter.extract(pose_frames)

            quality = {
                "fps": request.fps >= 90,
                "shutter": (request.shutter_us or 0) <= 1500 if request.shutter_us else True,
                "ref_len": request.ref_len_m > 0 and request.ref_len_px > 0,
                "tracking": len(ball_tracks) > 0 and len(club_tracks) > 0,
            }

            source_hints = {
                "tracker": tracker.name,
                "pose": pose_adapter.name,
                "impactFrame": str(impact.frame),
                "cvSource": headers.get("x-cv-source", "mock"),
                "tempoRatio": f"{pose_summary.tempo_ratio:.2f}",
                "shoulderTiltDeg": f"{pose_summary.shoulder_tilt_deg:.2f}",
                "pelvisTiltDeg": f"{pose_summary.pelvis_tilt_deg:.2f}",
            }

            pipeline_span.set_attribute("cv.pipeline.pose_adapter", pose_adapter.name)

        total_duration_ms = (perf_counter() - total_start) * 1000.0
        frame_count = max(len(request.ball), len(request.club), 1)
        pipeline_span.set_attribute("cv.pipeline.frame_count", frame_count)
        pipeline_span.set_attribute("cv.pipeline.duration_ms", total_duration_ms)
        record_frame_inference(total_duration_ms, frame_count)

        return {
            "ballSpeedMps": round(ball_speed, 3),
            "clubSpeedMps": round(club_speed, 3),
            "sideAngleDeg": round(side_angle, 3),
            "carryEstM": round(carry, 3),
            "quality": quality,
            "sourceHints": source_hints,
        }


@app.post("/coach/chat")
def coach_chat(payload: Dict[str, object], headers: Dict[str, str]) -> Dict[str, object]:
    try:
        body = CoachChatBody.parse_obj(payload)
    except CoachValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"status": "error", "reason": str(exc)},
        )

    persona_profile = _resolve_persona_or_422(body.userId, body.persona)

    try:
        request_payload: Dict[str, object] = {
            "userId": body.userId,
            "message": body.message,
        }
        if body.persona is not None:
            request_payload["persona"] = body.persona
        if body.history is not None:
            request_payload["history"] = body.history
        request = CoachChatRequest.from_dict(request_payload)
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"status": "error", "reason": str(exc) or "invalid payload"},
        )

    response = coach_responder.reply(request)
    response.setdefault("persona", persona_profile.label)
    return response


@app.post("/coach/weekly-summary")
def coach_weekly_summary(payload: Dict[str, object], headers: Dict[str, str]) -> Dict[str, object]:
    try:
        body = CoachWeeklySummaryBody.parse_obj(payload)
    except CoachValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"status": "error", "reason": str(exc)},
        )

    persona_profile = _resolve_persona_or_422(body.userId, body.persona)

    try:
        summary = weekly_summary_job.summarize(body.userId, persona_profile.key, body.lastN)
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"status": "error", "reason": str(exc) or "invalid request"},
        )

    return {"status": "ok", "persona": persona_profile.label, "summary": summary}


@app.post("/score/hit")
def record_target_hit(payload, headers):
    if not ar_targets.is_enabled():
        return {"status": "disabled", "reason": "AR targets disabled"}

    hit = ar_targets.parse_hit_payload(payload)
    summary = target_run_store.add_hit(hit)

    telemetry_broker.emit("ar.targets.hit", {
        "targetId": hit.target_id,
        "hitPoint2D": list(hit.hit_point_2d),
        "hitPoint3D": list(hit.hit_point_3d),
        "score": hit.score,
        "runId": hit.run_id,
    })

    return {
        "status": "ok",
        "mode": ar_targets.mode(),
        "run": summary.to_dict(),
    }


@app.post("/ws/telemetry")
def post_telemetry(payload, headers):
    return telemetry_broker.emit("telemetry", payload)


billing_routes.register(app)


@app.get("/entitlements/demo-pro")
def entitlements_demo_pro(query, headers):
    user_id = (query or {}).get("userId")
    if not user_id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"status": "error", "reason": "userId required"},
        )
    try:
        require_entitlement("pro")(user_id, headers)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {"reason": str(exc)}
        emit_telemetry(
            "blocked",
            {
                "userId": user_id,
                "productId": "pro",
                "reason": detail.get("reason", "requires pro"),
            },
        )
        raise
    return {"ok": True}
