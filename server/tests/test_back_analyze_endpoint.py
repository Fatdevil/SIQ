from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import pytest

from opentelemetry import trace

from server.main import BackAnalyzeRequest, _to_detections, app, create_tracker
from server.testing import TestClient
from siq.observability import FRAME_INFERENCE_HISTOGRAM


client = TestClient(app)
GOLDEN_DIR = Path(__file__).resolve().parents[2] / "tests" / "goldens"


def _track_series(start_x: float, delta: float) -> list[dict]:
    return [
        {"frame": i, "bbox": [start_x + i * delta, 0.0, 5.0, 5.0]} for i in range(3)
    ]


def _default_payload() -> dict:
    return {
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


@pytest.fixture(autouse=True)
def reset_observability() -> Iterable[None]:
    trace.reset()
    FRAME_INFERENCE_HISTOGRAM.reset()
    yield
    trace.reset()
    FRAME_INFERENCE_HISTOGRAM.reset()


def test_back_analyze_returns_metrics_fields():
    payload = _default_payload()
    response = client.post("/cv/back/analyze", json=payload, headers={"x-cv-source": "mock"})
    assert response.status_code == 200, response.text
    data = response.json()
    for key in ["ballSpeedMps", "clubSpeedMps", "sideAngleDeg", "carryEstM", "quality", "sourceHints"]:
        assert key in data
    assert data["quality"]["fps"] is True
    assert data["sourceHints"]["tracker"] in {"bytetrack", "norfair", "identity"}


def test_back_analyze_emits_spans_and_metrics():
    payload = _default_payload()
    response = client.post("/cv/back/analyze", json=payload, headers={"x-cv-source": "mock"})
    assert response.status_code == 200, response.text

    spans = trace.get_finished_spans()
    span_names = {span.name for span in spans}
    for expected in {"cv.pipeline", "cv.detect", "cv.track", "cv.impact", "cv.metrics"}:
        assert expected in span_names

    pipeline_span = next(span for span in spans if span.name == "cv.pipeline")
    assert pipeline_span.attributes["cv.pipeline.duration_ms"] > 0
    assert pipeline_span.attributes["cv.pipeline.frame_count"] >= 1

    assert FRAME_INFERENCE_HISTOGRAM.records, "frame_inference_ms histogram should record values"
    value, attributes = FRAME_INFERENCE_HISTOGRAM.records[-1]
    assert value > 0
    assert attributes["cv.frame_count"] >= 1


def test_back_analyze_matches_goldens():
    payload = _default_payload()
    response = client.post("/cv/back/analyze", json=payload, headers={"x-cv-source": "mock"})
    assert response.status_code == 200, response.text
    data = response.json()

    golden_metrics = json.loads((GOLDEN_DIR / "back_analyze_metrics.json").read_text())
    for key, expected_value in golden_metrics.items():
        assert data[key] == pytest.approx(expected_value, abs=1e-3)

    golden_grid = _load_pgm(GOLDEN_DIR / "ball_path.pgm")
    actual_grid = _render_ball_heatmap(payload)
    assert len(actual_grid) == len(golden_grid)
    assert len(actual_grid[0]) == len(golden_grid[0])

    max_diff = max(
        abs(a - b)
        for row_actual, row_golden in zip(actual_grid, golden_grid)
        for a, b in zip(row_actual, row_golden)
    )
    assert max_diff <= 0


def _render_ball_heatmap(payload: dict, size: int = 8) -> list[list[int]]:
    request = BackAnalyzeRequest.from_dict(payload)
    tracker = create_tracker("identity")
    ball_tracks = tracker.track(_to_detections(request.ball))

    points = [
        (t.bbox[0] + t.bbox[2] / 2.0, t.bbox[1] + t.bbox[3] / 2.0)
        for t in sorted(ball_tracks, key=lambda x: x.frame)
    ]

    if not points:
        return [[0 for _ in range(size)] for _ in range(size)]

    xs = [pt[0] for pt in points]
    ys = [pt[1] for pt in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    def normalize(value: float, min_val: float, max_val: float) -> float:
        if abs(max_val - min_val) < 1e-9:
            return 0.5
        return (value - min_val) / (max_val - min_val)

    grid = [[0 for _ in range(size)] for _ in range(size)]
    for x, y in points:
        u = normalize(x, min_x, max_x)
        v = 1.0 - normalize(y, min_y, max_y)
        col = max(0, min(size - 1, int(round(u * (size - 1)))))
        row = max(0, min(size - 1, int(round(v * (size - 1)))))
        grid[row][col] += 1

    max_count = max(max(row) for row in grid)
    max_count = max(max_count, 1)

    return [
        [int(round(pixel / max_count * 255)) for pixel in row]
        for row in grid
    ]


def _load_pgm(path: Path) -> list[list[int]]:
    with path.open("r") as fp:
        header = fp.readline().strip()
        if header != "P2":
            raise ValueError("Unsupported PGM format")
        line = fp.readline().strip()
        while line.startswith("#"):
            line = fp.readline().strip()
        width, height = map(int, line.split())
        max_value = int(fp.readline().strip())
        values = []
        for line in fp:
            values.extend(int(val) for val in line.strip().split())
    grid = [values[i * width : (i + 1) * width] for i in range(height)]
    if max_value != 255:
        grid = [
            [int(round(pixel / max_value * 255)) for pixel in row]
            for row in grid
        ]
    return grid
