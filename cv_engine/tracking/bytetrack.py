from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence

from .base import BBox, Detection, TrackerAdapter, TrackedDetection


@dataclass
class _TrackState:
    bbox: BBox
    last_frame: int
    misses: int = 0

    def update(self, frame: int, bbox: BBox) -> None:
        self.bbox = bbox
        self.last_frame = frame
        self.misses = 0

    def step(self) -> None:
        self.misses += 1


class ByteTrackAdapter(TrackerAdapter):
    name = "bytetrack"

    def __init__(self, max_missed: int = 3, distance_threshold: float = 60.0) -> None:
        self._max_missed = max_missed
        self._distance_threshold = distance_threshold

    @staticmethod
    def _center(bbox: BBox) -> tuple[float, float]:
        x, y, w, h = bbox
        return x + w / 2.0, y + h / 2.0

    @staticmethod
    def _distance(a: BBox, b: BBox) -> float:
        ax, ay = ByteTrackAdapter._center(a)
        bx, by = ByteTrackAdapter._center(b)
        return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5

    def track(self, detections: Sequence[Detection]) -> List[TrackedDetection]:
        tracks: Dict[int, _TrackState] = {}
        active_ids: set[int] = set()
        results: List[TrackedDetection] = []
        next_track_id = 1
        sorted_detections = sorted(detections, key=lambda d: (d.frame, d.bbox))
        current_frame = None
        for det in sorted_detections:
            if det.frame != current_frame:
                # advance frame for all tracks
                for track_id, state in list(tracks.items()):
                    if state.last_frame != det.frame:
                        state.step()
                        if state.misses > self._max_missed:
                            tracks.pop(track_id)
                active_ids.clear()
                current_frame = det.frame

            matched_id = None
            best_distance = self._distance_threshold
            for track_id, state in tracks.items():
                if state.misses > self._max_missed:
                    continue
                if track_id in active_ids:
                    continue
                distance = self._distance(state.bbox, det.bbox)
                if distance < best_distance:
                    best_distance = distance
                    matched_id = track_id
            if matched_id is None:
                matched_id = next_track_id
                tracks[matched_id] = _TrackState(det.bbox, det.frame)
                next_track_id += 1
            else:
                tracks[matched_id].update(det.frame, det.bbox)
            active_ids.add(matched_id)
            results.append(TrackedDetection(frame=det.frame, bbox=det.bbox, track_id=matched_id))
        return results
