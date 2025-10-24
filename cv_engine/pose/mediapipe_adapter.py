from __future__ import annotations

from typing import Iterable

from .base import Keypoint, PoseAdapter, PoseFrame, PoseSummary
from .utils import compute_tilt, compute_tempo


class MediapipePoseAdapter(PoseAdapter):
    name = "mediapipe"

    def extract(self, frames: Iterable[PoseFrame]) -> PoseSummary:
        frames_list = list(frames)
        if not frames_list:
            return PoseSummary(shoulder_tilt_deg=0.0, pelvis_tilt_deg=0.0, tempo_ratio=0.0)
        shoulder_tilts = [compute_tilt(frame.keypoints, ("left_shoulder", "right_shoulder")) for frame in frames_list]
        pelvis_tilts = [compute_tilt(frame.keypoints, ("left_hip", "right_hip")) for frame in frames_list]
        tempo = compute_tempo(frames_list)
        return PoseSummary(
            shoulder_tilt_deg=sum(shoulder_tilts) / len(shoulder_tilts),
            pelvis_tilt_deg=sum(pelvis_tilts) / len(pelvis_tilts),
            tempo_ratio=tempo,
        )
