from __future__ import annotations

import math
from typing import List, Tuple

import pytest

from metrics import angle, ball, carry_v1

np = pytest.importorskip("numpy")

Point = Tuple[int, float, float]


def _synthetic_ball_path(fps: float, frame_count: int, v0_mps: float, launch_angle_deg: float) -> List[Point]:
    frames = np.arange(frame_count, dtype=float)
    t = frames / fps
    launch_rad = math.radians(launch_angle_deg)
    v0_x = v0_mps * math.cos(launch_rad)
    v0_y = v0_mps * math.sin(launch_rad)
    g = 9.81

    x_m = v0_x * t
    y_m = v0_y * t - 0.5 * g * t**2 + 2.0  # keep coordinates positive

    m_per_px = 0.01
    x_px = x_m / m_per_px
    y_px = y_m / m_per_px

    return [
        (int(frame), float(x), float(y))
        for frame, x, y in zip(frames.tolist(), x_px.tolist(), y_px.tolist())
    ]


@pytest.mark.smoke
def test_backview_metrics_smoke() -> None:
    fps = 120.0
    ref_len_m = 1.0
    ref_len_px = 100.0
    expected_speed = 38.0
    expected_carry = 38.0

    track = _synthetic_ball_path(fps=fps, frame_count=6, v0_mps=38.0, launch_angle_deg=12.0)
    m_per_px = ball.meters_per_pixel(ref_len_m, ref_len_px)

    ball_speed_mps = ball.ball_speed_mps(track, fps=fps, m_per_px=m_per_px)
    side_angle_deg = angle.side_angle_deg(track)
    carry_est_m = carry_v1.carry_distance_m(ball_speed_mps, side_angle_deg)

    assert abs(ball_speed_mps - expected_speed) <= 0.5
    assert abs(side_angle_deg) <= 1.5
    assert abs(carry_est_m - expected_carry) <= 12.0
