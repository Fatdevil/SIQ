from __future__ import annotations

from cv_engine.tracking.base import Detection
from cv_engine.tracking.bytetrack import ByteTrackAdapter
from cv_engine.tracking.factory import IdentityTracker
from cv_engine.tracking.norfair import NorfairAdapter


def _synthetic_series():
    frames = []
    # object moves diagonally, disappears at frame 3
    positions = {
        0: (0.0, 0.0, 10.0, 10.0),
        1: (5.0, 5.0, 10.0, 10.0),
        2: (10.0, 10.0, 10.0, 10.0),
        4: (20.0, 20.0, 10.0, 10.0),
        5: (25.0, 25.0, 10.0, 10.0),
    }
    for frame, bbox in positions.items():
        frames.append(Detection(frame=frame, bbox=bbox))
    return frames


def test_bytetrack_stable_ids_across_gap():
    tracker = ByteTrackAdapter(max_missed=2, distance_threshold=50.0)
    tracked = tracker.track(_synthetic_series())
    ids = {det.track_id for det in tracked}
    assert len(ids) == 1
    assert [det.track_id for det in tracked][-1] == list(ids)[0]


def test_norfair_stable_ids_across_gap():
    tracker = NorfairAdapter(distance_threshold=70.0)
    tracked = tracker.track(_synthetic_series())
    ids = {det.track_id for det in tracked}
    assert len(ids) == 1


def test_identity_assigns_unique_ids():
    tracker = IdentityTracker()
    tracked = tracker.track(_synthetic_series())
    assert len({det.track_id for det in tracked}) == len(tracked)
