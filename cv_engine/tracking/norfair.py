from __future__ import annotations

from typing import Dict, List, Sequence

from .base import BBox, Detection, TrackerAdapter, TrackedDetection


class NorfairAdapter(TrackerAdapter):
    name = "norfair"

    def __init__(self, smoothing: float = 0.7, distance_threshold: float = 80.0) -> None:
        self._smoothing = smoothing
        self._distance_threshold = distance_threshold

    @staticmethod
    def _center(bbox: BBox) -> tuple[float, float]:
        x, y, w, h = bbox
        return x + w / 2.0, y + h / 2.0

    def track(self, detections: Sequence[Detection]) -> List[TrackedDetection]:
        """Track detections with a greedy assignment while preventing per-frame id reuse."""

        tracks: Dict[int, tuple[float, float]] = {}
        last_frame: Dict[int, int] = {}
        results: List[TrackedDetection] = []
        next_track_id = 1
        active_ids: set[int] = set()
        current_frame: int | None = None

        def _sorted_key(det: Detection) -> tuple[int, float, float, float, float]:
            x, y, w, h = det.bbox
            return det.frame, x, y, w, h

        for det in sorted(detections, key=_sorted_key):
            if current_frame != det.frame:
                current_frame = det.frame
                active_ids = set()

            cx, cy = self._center(det.bbox)
            best_id = None
            best_distance = self._distance_threshold
            for track_id, center in sorted(tracks.items()):
                if track_id in active_ids:
                    continue
                distance = ((center[0] - cx) ** 2 + (center[1] - cy) ** 2) ** 0.5
                if distance <= best_distance:
                    best_distance = distance
                    best_id = track_id

            if best_id is None:
                best_id = next_track_id
                tracks[best_id] = (cx, cy)
                next_track_id += 1
            else:
                last_center = tracks[best_id]
                smoothed = (
                    last_center[0] * self._smoothing + cx * (1 - self._smoothing),
                    last_center[1] * self._smoothing + cy * (1 - self._smoothing),
                )
                tracks[best_id] = smoothed

            active_ids.add(best_id)
            last_frame[best_id] = det.frame
            results.append(TrackedDetection(frame=det.frame, bbox=det.bbox, track_id=best_id))

            # cleanup old tracks occasionally
            stale_ids = [track_id for track_id, frame in last_frame.items() if det.frame - frame > 5]
            for stale_id in stale_ids:
                tracks.pop(stale_id, None)
                last_frame.pop(stale_id, None)
        return results
