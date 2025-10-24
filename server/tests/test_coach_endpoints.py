from __future__ import annotations

from server.main import app
from server.testing import TestClient


def test_chat_missing_userid_returns_422() -> None:
    client = TestClient(app)
    payload = {"message": "hi there", "persona": "Pro"}
    response = client.post("/coach/chat", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body.get("status") == "error"
    assert "userId" in body.get("reason", "")


def test_chat_unknown_persona_returns_422() -> None:
    client = TestClient(app)
    payload = {"userId": "user-unknown", "message": "hi", "persona": "UNKNOWN"}
    response = client.post("/coach/chat", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body.get("status") == "error"
    assert "unknown persona" in body.get("reason", "").lower()


def test_weekly_summary_bad_lastN_returns_422() -> None:
    client = TestClient(app)
    payload = {"userId": "weekly-user", "persona": "Pro", "lastN": 0}
    response = client.post("/coach/weekly-summary", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body.get("status") == "error"


def test_weekly_summary_unknown_persona_returns_422() -> None:
    client = TestClient(app)
    payload = {"userId": "weekly-user-2", "persona": "Nope", "lastN": 5}
    response = client.post("/coach/weekly-summary", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body.get("status") == "error"
    assert "unknown persona" in body.get("reason", "").lower()


def test_chat_happy_path_returns_ok() -> None:
    client = TestClient(app)
    payload = {"userId": "happy-user", "message": "Hello Coach!", "persona": "Pro"}
    response = client.post("/coach/chat", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body.get("status") == "ok"
    assert body.get("reply")
