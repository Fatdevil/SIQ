from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


def is_enabled() -> bool:
    return os.getenv("AR_TARGETS", "0") == "1"


def mode() -> str:
    requested = os.getenv("AR_TARGETS_MODE", "apriltag").lower()
    return requested if requested in {"apriltag", "image", "plane"} else "apriltag"


@dataclass
class HitRecord:
    run_id: str
    target_id: str
    hit_point_2d: Tuple[float, float]
    hit_point_3d: Tuple[float, float, float]
    score: float

    def to_dict(self) -> Dict[str, object]:
        return {
            "runId": self.run_id,
            "targetId": self.target_id,
            "hitPoint2D": list(self.hit_point_2d),
            "hitPoint3D": list(self.hit_point_3d),
            "score": self.score,
        }


@dataclass
class TargetRunSummary:
    run_id: str
    hits: List[HitRecord] = field(default_factory=list)

    @property
    def total_score(self) -> float:
        return sum(hit.score for hit in self.hits)

    def add_hit(self, hit: HitRecord) -> None:
        self.hits.append(hit)

    def to_dict(self) -> Dict[str, object]:
        last_hit = self.hits[-1].to_dict() if self.hits else None
        return {
            "runId": self.run_id,
            "totalHits": len(self.hits),
            "totalScore": round(self.total_score, 3),
            "lastHit": last_hit,
        }


class TargetRunStore:
    def __init__(self) -> None:
        self._runs: Dict[str, TargetRunSummary] = {}

    def add_hit(self, hit: HitRecord) -> TargetRunSummary:
        summary = self._runs.setdefault(hit.run_id, TargetRunSummary(run_id=hit.run_id))
        summary.add_hit(hit)
        return summary

    def get_summary(self, run_id: str) -> TargetRunSummary | None:
        return self._runs.get(run_id)


class TelemetryBroker:
    def __init__(self) -> None:
        self.events: List[Dict[str, object]] = []

    def emit(self, channel: str, payload: Dict[str, object]) -> Dict[str, object]:
        event = {"channel": channel, **payload}
        self.events.append(event)
        return event


def parse_hit_payload(payload: Dict[str, object]) -> HitRecord:
    try:
        run_id = str(payload["runId"])
        target_id = str(payload["targetId"])
        hit_point_2d = tuple(float(v) for v in payload["hitPoint2D"])
        hit_point_3d = tuple(float(v) for v in payload["hitPoint3D"])
        score = float(payload["score"])
    except KeyError as exc:  # pragma: no cover - surfaced in tests
        raise ValueError(f"Missing required key: {exc.args[0]}")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid hit payload: {exc}") from exc

    if len(hit_point_2d) != 2:
        raise ValueError("hitPoint2D must contain exactly 2 values")
    if len(hit_point_3d) != 3:
        raise ValueError("hitPoint3D must contain exactly 3 values")

    return HitRecord(
        run_id=run_id,
        target_id=target_id,
        hit_point_2d=(hit_point_2d[0], hit_point_2d[1]),
        hit_point_3d=(hit_point_3d[0], hit_point_3d[1], hit_point_3d[2]),
        score=score,
    )
