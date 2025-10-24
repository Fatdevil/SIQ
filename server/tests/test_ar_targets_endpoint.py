from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

import pytest

from server.main import app, telemetry_broker, target_run_store
from server.testing import TestClient


@contextmanager
def ar_targets_enabled() -> Iterator[None]:
    previous_enabled = os.getenv("AR_TARGETS")
    previous_mode = os.getenv("AR_TARGETS_MODE")
    os.environ["AR_TARGETS"] = "1"
    os.environ["AR_TARGETS_MODE"] = "apriltag"
    try:
        yield
    finally:
        if previous_enabled is None:
            os.environ.pop("AR_TARGETS", None)
        else:
            os.environ["AR_TARGETS"] = previous_enabled
        if previous_mode is None:
            os.environ.pop("AR_TARGETS_MODE", None)
        else:
            os.environ["AR_TARGETS_MODE"] = previous_mode


@pytest.fixture(autouse=True)
def reset_store() -> Iterator[None]:
    telemetry_broker.events.clear()
    target_run_store._runs.clear()  # type: ignore[attr-defined]
    yield
    telemetry_broker.events.clear()
    target_run_store._runs.clear()  # type: ignore[attr-defined]


def _sample_hit_payload() -> dict[str, object]:
    return {
        "runId": "session-001",
        "targetId": "range-a",
        "hitPoint2D": [128.0, 256.0],
        "hitPoint3D": [0.1, 1.2, 3.4],
        "score": 87.5,
    }


def test_score_hit_records_summary_and_telemetry() -> None:
    client = TestClient(app)
    with ar_targets_enabled():
        response = client.post("/score/hit", json=_sample_hit_payload())

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["mode"] == "apriltag"
    assert data["run"]["totalHits"] == 1
    assert data["run"]["totalScore"] == 87.5
    assert len(telemetry_broker.events) == 1
    event = telemetry_broker.events[0]
    assert event["channel"] == "telemetry" or event["channel"] == "ar.targets.hit"
    assert event["targetId"] == "range-a"


def test_score_hit_disabled_flag_returns_disabled_status() -> None:
    client = TestClient(app)
    os.environ.pop("AR_TARGETS", None)
    os.environ.pop("AR_TARGETS_MODE", None)

    response = client.post("/score/hit", json=_sample_hit_payload())
    assert response.status_code == 200
    assert response.json()["status"] == "disabled"


@pytest.mark.parametrize(
    "payload",
    [
        {"runId": "1", "targetId": "t", "hitPoint2D": [1.0], "hitPoint3D": [0, 0, 0], "score": 10},
        {"runId": "1", "targetId": "t", "hitPoint2D": [1.0, 2.0], "hitPoint3D": [0, 0], "score": 10},
    ],
)
def test_score_hit_invalid_payload_returns_error(payload: dict[str, object]) -> None:
    client = TestClient(app)
    with ar_targets_enabled():
        response = client.post("/score/hit", json=payload)

    assert response.status_code == 500
    assert "Invalid" in response.json()["detail"] or "must contain" in response.json()["detail"]
