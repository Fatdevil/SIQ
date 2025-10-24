from __future__ import annotations

from typing import Sequence

from cv_engine.pose.base import Keypoint


def tilt_between(keypoints: Sequence[Keypoint], a_name: str, b_name: str) -> float:
    from cv_engine.pose.utils import compute_tilt

    return compute_tilt(keypoints, (a_name, b_name))
