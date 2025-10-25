from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from cv_engine.tracking.base import TrackedDetection


@dataclass(frozen=True)
class ImpactResult:
    frame: int
    confidence: float


def _iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    inter_x1 = max(ax, bx)
    inter_y1 = max(ay, by)
    inter_x2 = min(ax + aw, bx + bw)
    inter_y2 = min(ay + ah, by + bh)
    if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
        return 0.0
    intersection = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    union = aw * ah + bw * bh - intersection
    if union <= 0:
        return 0.0
    return intersection / union


def detect_impact(ball: Sequence[TrackedDetection], club: Sequence[TrackedDetection], fps: float) -> ImpactResult:
    if not ball or not club or fps <= 0:
        return ImpactResult(frame=0, confidence=0.0)
    ball_by_frame = {}
    for det in ball:
        ball_by_frame.setdefault(det.frame, []).append(det)
    club_by_frame = {}
    for det in club:
        club_by_frame.setdefault(det.frame, []).append(det)

    candidate_frame = None
    best_score = 0.0
    for frame in sorted(set(ball_by_frame.keys()) & set(club_by_frame.keys())):
        overlaps = [_iou(bd.bbox, cd.bbox) for bd in ball_by_frame[frame] for cd in club_by_frame[frame]]
        if not overlaps:
            continue
        mean_overlap = sum(overlaps) / len(overlaps)
        if mean_overlap > best_score:
            best_score = mean_overlap
            candidate_frame = frame

    if candidate_frame is None:
        return ImpactResult(frame=0, confidence=0.0)

    post_frame = candidate_frame + 1
    separation = 0.0
    if post_frame in ball_by_frame and post_frame in club_by_frame:
        post_overlaps = [
            _iou(bd.bbox, cd.bbox) for bd in ball_by_frame[post_frame] for cd in club_by_frame[post_frame]
        ]
        separation = 1.0 - sum(post_overlaps) / len(post_overlaps) if post_overlaps else 1.0

    confidence = min(1.0, best_score * 0.7 + separation * 0.3)
    return ImpactResult(frame=candidate_frame, confidence=confidence)
