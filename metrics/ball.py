from __future__ import annotations

from typing import Sequence, Tuple


Point = Tuple[int, float, float]


def meters_per_pixel(ref_len_m: float, ref_len_px: float) -> float:
    if ref_len_px == 0:
        return 0.0
    return ref_len_m / ref_len_px


def ball_speed_mps(points: Sequence[Point], fps: float, m_per_px: float) -> float:
    if len(points) < 2 or fps <= 0:
        return 0.0
    total_distance = 0.0
    total_time = 0.0
    for (frame_a, ax, ay), (frame_b, bx, by) in zip(points[:-1], points[1:]):
        if frame_b == frame_a:
            continue
        distance_px = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
        total_distance += distance_px
        total_time += (frame_b - frame_a) / fps
    if total_time == 0:
        return 0.0
    return total_distance * m_per_px / total_time


def ball_speed_error(estimated: float, ground_truth: float) -> float:
    if ground_truth == 0:
        return 0.0
    return (estimated - ground_truth) / ground_truth * 100.0
