from __future__ import annotations

from cv_engine.tracking.base import Detection
from cv_engine.tracking.norfair import NorfairAdapter


def _bbox(cx: float, cy: float, size: float = 10.0) -> tuple[float, float, float, float]:
    half = size / 2.0
    return cx - half, cy - half, size, size


def test_norfair_unique_ids_same_frame():
    tracker = NorfairAdapter(distance_threshold=30.0)
    detections = [
        Detection(frame=0, bbox=_bbox(100.0, 100.0)),
        Detection(frame=0, bbox=_bbox(140.0, 100.0)),
        Detection(frame=1, bbox=_bbox(102.0, 101.0)),
        Detection(frame=1, bbox=_bbox(138.0, 99.0)),
    ]

    tracked = tracker.track(detections)
    frame_one = [det for det in tracked if det.frame == 1]

    assert {det.track_id for det in frame_one} == {1, 2}

    ordered = sorted(frame_one, key=lambda det: det.bbox[0])
    assert ordered[0].track_id == 1
    assert ordered[1].track_id == 2


def test_norfair_persistence_across_frames():
    tracker = NorfairAdapter(distance_threshold=35.0)
    detections = [
        Detection(frame=0, bbox=_bbox(50.0, 75.0)),
        Detection(frame=0, bbox=_bbox(90.0, 75.0)),
        Detection(frame=1, bbox=_bbox(54.0, 78.0)),
        Detection(frame=1, bbox=_bbox(94.0, 77.0)),
        Detection(frame=2, bbox=_bbox(58.0, 80.0)),
        Detection(frame=2, bbox=_bbox(98.0, 79.0)),
    ]

    tracked = tracker.track(detections)
    frames: dict[int, list[int]] = {}
    for det in tracked:
        frames.setdefault(det.frame, []).append(det.track_id)

    for frame, ids in frames.items():
        assert sorted(ids) == [1, 2], f"frame {frame} ids were {ids}"


def test_norfair_unmatched_starts_new_track():
    tracker = NorfairAdapter(distance_threshold=20.0)
    detections = [
        Detection(frame=0, bbox=_bbox(0.0, 0.0)),
        Detection(frame=1, bbox=_bbox(100.0, 100.0)),
    ]

    tracked = tracker.track(detections)
    ids = [det.track_id for det in tracked]

    assert ids == [1, 2]
