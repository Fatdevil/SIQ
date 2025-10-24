from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

from cv_engine.metrics import detect_impact
from cv_engine.pose.base import Keypoint as PoseKeypoint, PoseFrame
from cv_engine.pose.mediapipe_adapter import MediapipePoseAdapter
from cv_engine.pose.movenet_adapter import MoveNetPoseAdapter
from cv_engine.tracking.base import Detection, TrackedDetection
from cv_engine.tracking.factory import create_tracker
from metrics import angle, ball, carry_v1, club
from server.testing import MiniAPI

app = MiniAPI()


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
    ball_tracks = tracker.track(_to_detections(request.ball))
    club_tracks = tracker.track(_to_detections(request.club))

    impact = detect_impact(ball_tracks, club_tracks, request.fps)
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

    pose_frames = _to_pose_frames(request.pose)
    pose_adapter = MediapipePoseAdapter() if os.getenv("GOLFIQ_POSE", "mediapipe") == "mediapipe" else MoveNetPoseAdapter()
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

    return {
        "ballSpeedMps": round(ball_speed, 3),
        "clubSpeedMps": round(club_speed, 3),
        "sideAngleDeg": round(side_angle, 3),
        "carryEstM": round(carry, 3),
        "quality": quality,
        "sourceHints": source_hints,
    }
