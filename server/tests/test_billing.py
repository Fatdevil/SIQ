from __future__ import annotations

import importlib
from typing import Iterator

import pytest

from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    store_path = tmp_path / "users.json"
    monkeypatch.setenv("BILLING_STORE_PATH", str(store_path))

    from server.services.billing import store as billing_store
    from server.services.billing import mock_verifier
    from server.security import entitlements
    from server.routes import billing as billing_routes
    from server import main as server_main

    importlib.reload(billing_store)
    importlib.reload(mock_verifier)
    importlib.reload(entitlements)
    importlib.reload(billing_routes)
    importlib.reload(server_main)

    test_client = TestClient(server_main.app)
    yield test_client


def test_verify_sets_pro_and_status_returns_pro(client: TestClient) -> None:
    response = client.post(
        "/billing/verify",
        json={"userId": "user-pro", "platform": "ios", "receipt": "PRO-123"},
    )
    assert response.status_code == 200
    assert response.json()["tier"] == "pro"

    status_response = client.get("/billing/status", params={"userId": "user-pro"})
    assert status_response.status_code == 200
    data = status_response.json()
    assert data["tier"] == "pro"
    assert data["provider"] == "mock"
    assert data["expiresAt"] is not None


def test_verify_sets_elite_and_status_returns_elite(client: TestClient) -> None:
    response = client.post(
        "/billing/verify",
        json={"userId": "user-elite", "platform": "android", "receipt": "ELITE-xyz"},
    )
    assert response.status_code == 200
    assert response.json()["tier"] == "elite"

    status_response = client.get("/billing/status", params={"userId": "user-elite"})
    assert status_response.status_code == 200
    assert status_response.json()["tier"] == "elite"


def test_demo_route_rejects_free_and_allows_pro(client: TestClient) -> None:
    free_response = client.get("/entitlements/demo-pro", params={"userId": "user-free"})
    assert free_response.status_code == 403

    upgrade_response = client.post(
        "/billing/verify",
        json={"userId": "user-free", "platform": "ios", "receipt": "PRO-okay"},
    )
    assert upgrade_response.status_code == 200

    allowed_response = client.get("/entitlements/demo-pro", params={"userId": "user-free"})
    assert allowed_response.status_code == 200
    assert allowed_response.json()["ok"] is True
