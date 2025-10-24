from __future__ import annotations

import os
from typing import Literal, Sequence

from .base import Detection, TrackerAdapter, TrackedDetection
from .bytetrack import ByteTrackAdapter
from .norfair import NorfairAdapter

TrackerName = Literal["bytetrack", "norfair", "identity"]


class IdentityTracker(TrackerAdapter):
    name = "identity"

    def track(self, detections: Sequence[Detection]) -> list[TrackedDetection]:
        return [
            TrackedDetection(frame=det.frame, bbox=det.bbox, track_id=index)
            for index, det in enumerate(sorted(detections, key=lambda d: (d.frame, d.bbox)), start=1)
        ]


def create_tracker(name: TrackerName | None = None) -> TrackerAdapter:
    tracker_name = (name or os.getenv("GOLFIQ_TRACKER") or "bytetrack").lower()
    if tracker_name == "bytetrack":
        return ByteTrackAdapter()
    if tracker_name == "norfair":
        return NorfairAdapter()
    if tracker_name == "identity":
        return IdentityTracker()
    raise ValueError(f"Unsupported tracker backend: {tracker_name}")
