from __future__ import annotations

import math

GRAVITY = 9.80665
DEFAULT_ALPHA_V = 0.82
DEFAULT_DRAG = 0.015


def carry_distance_m(ball_speed_mps: float, launch_angle_deg: float, alpha_v: float = DEFAULT_ALPHA_V, drag: float = DEFAULT_DRAG) -> float:
    if ball_speed_mps <= 0:
        return 0.0
    launch_rad = math.radians(launch_angle_deg)
    effective_speed = ball_speed_mps * alpha_v * (1 - drag)
    return (effective_speed ** 2 * math.sin(2 * launch_rad)) / GRAVITY


def mean_absolute_percentage_error(estimate: float, truth: float) -> float:
    if truth == 0:
        return 0.0
    return abs(estimate - truth)
