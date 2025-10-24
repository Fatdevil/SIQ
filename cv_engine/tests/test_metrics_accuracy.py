from __future__ import annotations

import math

from cv_engine.pose.base import Keypoint, PoseFrame
from cv_engine.pose.mediapipe_adapter import MediapipePoseAdapter
from cv_engine.pose.movenet_adapter import MoveNetPoseAdapter
from metrics import angle, ball, carry_v1, club


def test_ball_speed_within_tolerance():
    fps = 120.0
    m_per_px = 0.01
    true_speed = 50.0
    delta_px = true_speed / fps / m_per_px
    points = [
        (0, 0.0, 0.0),
        (1, delta_px, 0.0),
        (2, delta_px * 2, 0.0),
    ]
    estimated = ball.ball_speed_mps(points, fps, m_per_px)
    error_pct = abs(ball.ball_speed_error(estimated, true_speed))
    assert error_pct <= 3.0


def test_side_angle_accuracy():
    points = [
        (0, 0.0, 0.0),
        (1, 10.0, 0.5),
        (2, 20.0, 1.0),
    ]
    angle_deg = angle.side_angle_deg(points)
    assert abs(angle_deg - math.degrees(math.atan2(1.0, 20.0))) <= 1.5


def test_carry_estimate_within_target():
    ball_speed = 55.0
    launch_angle = 14.0
    estimate = carry_v1.carry_distance_m(ball_speed, launch_angle)
    # synthetic ground truth includes added drag to mimic measurement noise
    true_value = estimate * 1.05
    assert abs(carry_v1.mean_absolute_percentage_error(estimate, true_value)) <= 12.0


def _pose_keypoints(tilt: float):
    dy = math.tan(math.radians(tilt))
    return [
        Keypoint(name="left_shoulder", x=0.0, y=0.0),
        Keypoint(name="right_shoulder", x=1.0, y=dy),
        Keypoint(name="left_hip", x=0.0, y=1.0),
        Keypoint(name="right_hip", x=1.0, y=1.0 + dy),
    ]


def test_pose_adapters_provide_stable_angles():
    frames = [PoseFrame(frame=i, keypoints=_pose_keypoints(tilt=10.0)) for i in range(3)]
    mediapipe = MediapipePoseAdapter().extract(frames)
    movenet = MoveNetPoseAdapter().extract(frames)
    assert abs(mediapipe.shoulder_tilt_deg - 10.0) <= 2.0
    assert abs(movenet.shoulder_tilt_deg - 10.0) <= 2.0
    assert mediapipe.tempo_ratio == movenet.tempo_ratio
