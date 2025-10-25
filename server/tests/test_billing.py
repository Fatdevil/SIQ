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


def test_receipt_sets_pro_and_entitlements_return_pro(client: TestClient) -> None:
    response = client.post(
        "/billing/receipt",
        json={
            "userId": "user-pro",
            "platform": "ios",
            "receipt": "PRO-123",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["tier"] == "pro"
    assert payload["entitlements"]["pro"] is True

    entitlements_response = client.get("/me/entitlements", params={"userId": "user-pro"})
    assert entitlements_response.status_code == 200
    data = entitlements_response.json()
    assert data["tier"] == "pro"
    assert data["features"]["AI_PERSONAS"] is True


def test_receipt_sets_elite_and_entitlements_return_elite(client: TestClient) -> None:
    response = client.post(
        "/billing/receipt",
        json={
            "userId": "user-elite",
            "platform": "android",
            "receipt": "ELITE-xyz",
        },
    )
    assert response.status_code == 200
    assert response.json()["tier"] == "elite"

    entitlements_response = client.get("/me/entitlements", params={"userId": "user-elite"})
    assert entitlements_response.status_code == 200
    entitlements = entitlements_response.json()["entitlements"]
    assert entitlements["elite"] is True


def test_demo_route_rejects_free_and_allows_pro(client: TestClient) -> None:
    free_response = client.get("/entitlements/demo-pro", params={"userId": "user-free"})
    assert free_response.status_code == 403

    upgrade_response = client.post(
        "/billing/receipt",
        json={"userId": "user-free", "platform": "ios", "receipt": "PRO-okay"},
    )
    assert upgrade_response.status_code == 200

    allowed_response = client.get("/entitlements/demo-pro", params={"userId": "user-free"})
    assert allowed_response.status_code == 200
    assert allowed_response.json()["ok"] is True


def test_restore_mode_returns_existing_entitlements(client: TestClient) -> None:
    # Nothing stored yet – restore returns the default free entitlements.
    restore_response = client.post(
        "/billing/receipt",
        json={"userId": "user-restore", "platform": "ios", "mode": "restore"},
    )
    assert restore_response.status_code == 200
    payload = restore_response.json()
    assert payload["tier"] == "free"
    assert payload["entitlements"]["pro"] is False

    # Upgrade to pro and ensure restore returns the stored tier.
    client.post(
        "/billing/receipt",
        json={"userId": "user-restore", "platform": "ios", "receipt": "PRO-555"},
    )

    restored = client.post(
        "/billing/receipt",
        json={"userId": "user-restore", "platform": "ios", "mode": "restore"},
    )
    assert restored.status_code == 200
    restored_payload = restored.json()
    assert restored_payload["tier"] == "pro"
