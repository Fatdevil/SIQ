from __future__ import annotations

import hashlib
import hmac
import hashlib
import hmac
import importlib
import json
import sys
import time
from typing import Iterator

import pytest

from fastapi import HTTPException
from fastapi.testclient import TestClient

from server.services.entitlements.service import EntitlementService
from server.services.entitlements.store import EntitlementStore


MODULES_TO_RELOAD = [
    "server.services.entitlements.store",
    "server.services.entitlements.service",
    "server.services.entitlements.webhooks",
    "server.services.entitlements.providers",
    "server.services.entitlements.providers.apple",
    "server.services.entitlements.providers.google",
    "server.services.entitlements.providers.stripe",
    "server.services.entitlements.providers.utils",
    "server.services.entitlements.providers.metrics",
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
    webhook_path = tmp_path / "webhooks.json"
    monkeypatch.setenv("ENTITLEMENTS_STORE_PATH", str(store_path))
    monkeypatch.setenv("WEBHOOK_EVENTS_STORE_PATH", str(webhook_path))
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
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
        "id": "evt_test_123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "metadata": {"userId": "stripe-user", "productId": "pro"},
            }
        },
    }
    body = json.dumps(event_payload, separators=(",", ":"), sort_keys=True)
    timestamp = str(int(time.time()))
    signature = hmac.new(
        b"whsec_test",
        f"{timestamp}.{body}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    headers = {
        "Stripe-Signature": f"t={timestamp},v1={signature}",
    }
    response = client.post("/stripe/webhook", json=event_payload, headers=headers)
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
        "id": "evt_missing_metadata",
        "type": "checkout.session.completed",
        "data": {"object": {"id": "cs_test_missing", "metadata": None}},
    }
    body = json.dumps(event, separators=(",", ":"), sort_keys=True).encode("utf-8")
    timestamp = str(int(time.time()))
    signature = hmac.new(
        b"whsec_test",
        f"{timestamp}.{body.decode('utf-8')}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    with pytest.raises(HTTPException) as exc:
        service.process_stripe_checkout(
            event,
            headers={"Stripe-Signature": f"t={timestamp},v1={signature}"},
            raw_body=body,
        )
    assert exc.value.status_code == 400


def test_stripe_webhook_non_dict_metadata_returns_none(tmp_path) -> None:
    store = EntitlementStore(tmp_path / "entitlements.json")
    service = EntitlementService(store)
    event = {
        "id": "evt_invalid_metadata",
        "type": "checkout.session.completed",
        "data": {"object": {"id": "cs_test_invalid", "metadata": "not-a-dict"}},
    }
    body = json.dumps(event, separators=(",", ":"), sort_keys=True).encode("utf-8")
    timestamp = str(int(time.time()))
    signature = hmac.new(
        b"whsec_test",
        f"{timestamp}.{body.decode('utf-8')}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    with pytest.raises(HTTPException) as exc:
        service.process_stripe_checkout(
            event,
            headers={"Stripe-Signature": f"t={timestamp},v1={signature}"},
            raw_body=body,
        )
    assert exc.value.status_code == 400


def test_stripe_webhook_idempotent(client: TestClient) -> None:
    event_payload = {
        "id": "evt_dupe_1",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_dupe",
                "metadata": {"userId": "dupe-user", "productId": "pro"},
            }
        },
    }
    body = json.dumps(event_payload, separators=(",", ":"), sort_keys=True)
    timestamp = str(int(time.time()))
    signature = hmac.new(
        b"whsec_test",
        f"{timestamp}.{body}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    headers = {
        "Stripe-Signature": f"t={timestamp},v1={signature}",
    }
    first = client.post("/stripe/webhook", json=event_payload, headers=headers)
    assert first.status_code == 200
    assert first.json()["status"] == "ok"

    second = client.post("/stripe/webhook", json=event_payload, headers=headers)
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"

    listing = client.get("/me/entitlements", params={"userId": "dupe-user"})
    entitlements = listing.json()["entitlements"]
    assert len(entitlements) == 1


def test_feature_blocked_requires_feature(client: TestClient) -> None:
    response = client.post(
        "/billing/events/feature-blocked",
        json={},
        headers={"x-user-id": "user-1"},
    )
    assert response.status_code == 422


def test_feature_blocked_emits_telemetry(monkeypatch, client: TestClient) -> None:
    events: list[tuple[str, dict[str, str] | None]] = []

    def _capture(event: str, data: dict[str, str] | None = None) -> None:
        events.append((event, data or {}))

    monkeypatch.setattr("server.routes.billing.emit_telemetry", _capture)

    response = client.post(
        "/billing/events/feature-blocked",
        json={"feature": "coach_personas"},
        headers={"x-user-id": "user-2"},
    )
    assert response.status_code == 200
    assert events[-1][0] == "feature_blocked"
    assert events[-1][1]["feature"] == "coach_personas"
    assert events[-1][1]["userId"] == "user-2"


def test_restore_click_emits_event(monkeypatch, client: TestClient) -> None:
    events: list[tuple[str, dict[str, str] | None]] = []

    def _capture(event: str, data: dict[str, str] | None = None) -> None:
        events.append((event, data or {}))

    monkeypatch.setattr("server.routes.billing.emit_telemetry", _capture)

    response = client.post(
        "/billing/receipt",
        json={
            "provider": "mock",
            "payload": {
                "mode": "restore",
                "productId": "pro",
                "receipt": "RESTORE-1",
            },
        },
        headers={"x-user-id": "restorer"},
    )
    assert response.status_code == 200
    assert any(event == "restore_clicked" for event, _ in events)


def test_restore_event_endpoint_logs(monkeypatch, client: TestClient) -> None:
    events: list[tuple[str, dict[str, str] | None]] = []

    def _capture(event: str, data: dict[str, str] | None = None) -> None:
        events.append((event, data or {}))

    monkeypatch.setattr("server.routes.billing.emit_telemetry", _capture)

    response = client.post(
        "/billing/events/restore",
        json={"provider": "stripe"},
        headers={"x-user-id": "web-user"},
    )
    assert response.status_code == 200
    assert events[-1][0] == "restore_clicked"
    assert events[-1][1]["provider"] == "stripe"
    assert events[-1][1]["userId"] == "web-user"
