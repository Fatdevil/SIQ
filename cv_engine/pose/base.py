from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Keypoint:
    name: str
    x: float
    y: float


@dataclass(frozen=True)
class PoseFrame:
    frame: int
    keypoints: Sequence[Keypoint]


@dataclass(frozen=True)
class PoseSummary:
    shoulder_tilt_deg: float
    pelvis_tilt_deg: float
    tempo_ratio: float


class PoseAdapter:
    name: str = "base"

    def extract(self, frames: Iterable[PoseFrame]) -> PoseSummary:
        raise NotImplementedError
