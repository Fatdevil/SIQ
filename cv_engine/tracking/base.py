from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

BBox = Tuple[float, float, float, float]


@dataclass(frozen=True)
class Detection:
    frame: int
    bbox: BBox


@dataclass(frozen=True)
class TrackedDetection(Detection):
    track_id: int


class TrackerAdapter:
    """Base tracker adapter interface."""

    name: str = "base"

    def track(self, detections: Sequence[Detection]) -> List[TrackedDetection]:
        """Returns tracked detections with stable track IDs."""
        raise NotImplementedError


def group_by_frame(tracks: Iterable[TrackedDetection]) -> List[Tuple[int, List[TrackedDetection]]]:
    grouped: List[Tuple[int, List[TrackedDetection]]] = []
    current_frame: int | None = None
    current_list: List[TrackedDetection] = []
    for detection in sorted(tracks, key=lambda d: (d.frame, d.track_id)):
        if current_frame is None:
            current_frame = detection.frame
        if detection.frame != current_frame:
            grouped.append((current_frame, current_list))
            current_frame = detection.frame
            current_list = []
        current_list.append(detection)
    if current_frame is not None:
        grouped.append((current_frame, current_list))
    return grouped
