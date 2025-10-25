from __future__ import annotations

import importlib
import sys
from typing import Iterator

import pytest

from fastapi.testclient import TestClient

from server.services.entitlements.service import EntitlementService
from server.services.entitlements.store import EntitlementStore


MODULES_TO_RELOAD = [
    "server.services.entitlements.store",
    "server.services.entitlements.service",
    "server.security.entitlements",
    "server.services.telemetry",
    "server.routes.billing",
    "server.main",
]


def _reload_modules() -> None:
    for module_name in MODULES_TO_RELOAD:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        else:  # pragma: no cover - module may not be imported yet
            importlib.import_module(module_name)


@pytest.fixture()
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    store_path = tmp_path / "entitlements.json"
    monkeypatch.setenv("ENTITLEMENTS_STORE_PATH", str(store_path))
    _reload_modules()

    from server import main as server_main

    test_client = TestClient(server_main.app)
    yield test_client


def test_receipt_flow_grants_entitlement_and_lists(client: TestClient) -> None:
    unauth = client.get("/entitlements/demo-pro", params={"userId": "user-free"})
    assert unauth.status_code == 403

    response = client.post(
        "/billing/receipt",
        json={"provider": "mock", "payload": {"productId": "pro", "receipt": "PRO-123"}},
        headers={"x-user-id": "user-free"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["productId"] == "pro"
    assert data["status"] == "active"

    listing = client.get("/me/entitlements", params={"userId": "user-free"})
    assert listing.status_code == 200
    entitlements = listing.json()["entitlements"]
    assert len(entitlements) == 1
    assert entitlements[0]["productId"] == "pro"

    allowed = client.get("/entitlements/demo-pro", params={"userId": "user-free"})
    assert allowed.status_code == 200
    assert allowed.json()["ok"] is True


def test_stripe_webhook_grants_entitlement(client: TestClient) -> None:
    event_payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "metadata": {"userId": "stripe-user", "productId": "pro"},
            }
        },
    }
    response = client.post("/stripe/webhook", json=event_payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    entitlement = body["entitlement"]
    assert entitlement["productId"] == "pro"

    listing = client.get("/me/entitlements", params={"userId": "stripe-user"})
    assert listing.status_code == 200
    entitlements = listing.json()["entitlements"]
    assert entitlements[0]["productId"] == "pro"


def test_stripe_webhook_missing_metadata_returns_none(tmp_path) -> None:
    store = EntitlementStore(tmp_path / "entitlements.json")
    service = EntitlementService(store)
    event = {
        "type": "checkout.session.completed",
        "data": {"object": {"id": "cs_test_missing", "metadata": None}},
    }
    assert service.process_stripe_checkout(event) is None


def test_stripe_webhook_non_dict_metadata_returns_none(tmp_path) -> None:
    store = EntitlementStore(tmp_path / "entitlements.json")
    service = EntitlementService(store)
    event = {
        "type": "checkout.session.completed",
        "data": {"object": {"id": "cs_test_invalid", "metadata": "not-a-dict"}},
    }
    assert service.process_stripe_checkout(event) is None
