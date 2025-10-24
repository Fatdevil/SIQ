from __future__ import annotations

import math
from typing import Iterable, Sequence, Tuple

from .base import Keypoint, PoseFrame


def _lookup(keypoints: Sequence[Keypoint], name: str) -> Keypoint | None:
    for kp in keypoints:
        if kp.name == name:
            return kp
    return None


def compute_tilt(keypoints: Sequence[Keypoint], pair: Tuple[str, str]) -> float:
    a = _lookup(keypoints, pair[0])
    b = _lookup(keypoints, pair[1])
    if a is None or b is None:
        return 0.0
    dx = b.x - a.x
    dy = b.y - a.y
    if dx == 0 and dy == 0:
        return 0.0
    angle = math.degrees(math.atan2(dy, dx))
    return angle


def compute_tempo(frames: Iterable[PoseFrame]) -> float:
    frames_list = list(frames)
    if len(frames_list) < 2:
        return 0.0
    start_frame = frames_list[0].frame
    impact_frame = frames_list[-1].frame
    backswing = (impact_frame - start_frame) * 0.6
    downswing = (impact_frame - start_frame) * 0.4
    if downswing == 0:
        return 0.0
    return backswing / downswing
