from __future__ import annotations

from server.main import app
from server.testing import TestClient


client = TestClient(app)


def _track_series(start_x: float, delta: float) -> list[dict]:
    return [
        {"frame": i, "bbox": [start_x + i * delta, 0.0, 5.0, 5.0]} for i in range(3)
    ]


def test_back_analyze_returns_metrics_fields():
    payload = {
        "fps": 120,
        "ref_len_m": 1.0,
        "ref_len_px": 100.0,
        "ball": _track_series(0.0, 4.0),
        "club": _track_series(-2.0, 4.5),
        "pose": [
            {
                "frame": i,
                "keypoints": [
                    {"name": "left_shoulder", "x": 0.0, "y": 0.0},
                    {"name": "right_shoulder", "x": 1.0, "y": 0.1},
                    {"name": "left_hip", "x": 0.0, "y": 1.0},
                    {"name": "right_hip", "x": 1.0, "y": 1.1},
                ],
            }
            for i in range(3)
        ],
    }
    response = client.post("/cv/back/analyze", json=payload, headers={"x-cv-source": "mock"})
    assert response.status_code == 200, response.text
    data = response.json()
    for key in ["ballSpeedMps", "clubSpeedMps", "sideAngleDeg", "carryEstM", "quality", "sourceHints"]:
        assert key in data
    assert data["quality"]["fps"] is True
    assert data["sourceHints"]["tracker"] in {"bytetrack", "norfair", "identity"}
