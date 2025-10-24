from __future__ import annotations

from typing import Sequence, Tuple

Point = Tuple[int, float, float]


def club_speed_pre_impact(points: Sequence[Point], impact_frame: int, fps: float, m_per_px: float) -> float:
    relevant = [p for p in points if p[0] <= impact_frame]
    if len(relevant) < 2 or fps <= 0:
        return 0.0
    last_two = sorted(relevant, key=lambda p: p[0])[-2:]
    (frame_a, ax, ay), (frame_b, bx, by) = last_two
    if frame_b == frame_a:
        return 0.0
    distance_px = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
    delta_t = (frame_b - frame_a) / fps
    if delta_t == 0:
        return 0.0
    return distance_px * m_per_px / delta_t
