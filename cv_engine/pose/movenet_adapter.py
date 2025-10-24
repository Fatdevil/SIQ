from __future__ import annotations

from typing import Iterable

from .base import PoseAdapter, PoseFrame, PoseSummary
from .utils import compute_tilt, compute_tempo


class MoveNetPoseAdapter(PoseAdapter):
    name = "movenet"

    def extract(self, frames: Iterable[PoseFrame]) -> PoseSummary:
        frames_list = list(frames)
        if not frames_list:
            return PoseSummary(shoulder_tilt_deg=0.0, pelvis_tilt_deg=0.0, tempo_ratio=0.0)
        # MoveNet is more sensitive to jitter; use median tilts for stability
        shoulder_values = sorted(
            compute_tilt(frame.keypoints, ("left_shoulder", "right_shoulder")) for frame in frames_list
        )
        pelvis_values = sorted(
            compute_tilt(frame.keypoints, ("left_hip", "right_hip")) for frame in frames_list
        )
        mid = len(shoulder_values) // 2
        shoulder_tilt = shoulder_values[mid]
        pelvis_tilt = pelvis_values[mid]
        tempo = compute_tempo(frames_list)
        return PoseSummary(
            shoulder_tilt_deg=shoulder_tilt,
            pelvis_tilt_deg=pelvis_tilt,
            tempo_ratio=tempo,
        )
