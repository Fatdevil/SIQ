from __future__ import annotations

import hashlib
import hmac
import importlib
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Iterator

import pytest

from fastapi import HTTPException
from fastapi.testclient import TestClient

from server.services.entitlements.service import EntitlementService
from server.services.entitlements.store import EntitlementStore


MODULES_TO_RELOAD = [
    "server.services.entitlements.store",
    "server.services.entitlements.config",
    "server.services.entitlements.service",
    "server.services.entitlements.sweeper",
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


def stripe_sig_header(secret: str, raw: bytes, ts: str | None = None) -> str:
    timestamp = ts or str(int(time.time()))
    digest = hmac.new(secret.encode("ascii"), timestamp.encode("ascii") + b"." + raw, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


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
    assert data["grace"] is False

    listing = client.get("/me/entitlements", params={"userId": "user-free"})
    assert listing.status_code == 200
    entitlements = listing.json()["entitlements"]
    assert len(entitlements) == 1
    assert entitlements[0]["productId"] == "pro"
    assert entitlements[0]["grace"] is False

    allowed = client.get("/entitlements/demo-pro", params={"userId": "user-free"})
    assert allowed.status_code == 200
    body = allowed.json()
    assert body["ok"] is True
    assert body["grace"] is False


def test_entitlement_grace_allows_recent_verification(client: TestClient) -> None:
    from server.security import entitlements as ent_security

    service = ent_security.get_service()
    grace_user = "grace-user"
    service.store.grant(
        user_id=grace_user,
        product_id="pro",
        status="expired",
        source="mock",
        expires_at=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat().replace("+00:00", "Z"),
    )

    allowed = client.get("/entitlements/demo-pro", params={"userId": grace_user})
    assert allowed.status_code == 200
    assert allowed.json() == {"ok": True, "grace": True}


def test_entitlement_revoked_blocks_access(client: TestClient) -> None:
    from server.security import entitlements as ent_security

    service = ent_security.get_service()
    revoked_user = "revoked-user"
    service.store.grant(
        user_id=revoked_user,
        product_id="pro",
        status="revoked",
        source="mock",
        expires_at=None,
    )

    denied = client.get("/entitlements/demo-pro", params={"userId": revoked_user})
    assert denied.status_code == 403


def test_entitlement_grace_expires_after_window(client: TestClient) -> None:
    from server.security import entitlements as ent_security

    service = ent_security.get_service()
    stale_user = "stale-user"
    entitlement = service.store.grant(
        user_id=stale_user,
        product_id="pro",
        status="expired",
        source="mock",
        expires_at=None,
    )
    stale_verified = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat().replace("+00:00", "Z")
    refreshed = entitlement.update(
        status="expired",
        source=entitlement.source,
        expires_at=entitlement.expires_at,
        last_verified_at=stale_verified,
        revoked_at=None,
        source_status=entitlement.source_status,
        meta=entitlement.meta,
    )
    service.store.upsert(refreshed)

    denied = client.get("/entitlements/demo-pro", params={"userId": stale_user})
    assert denied.status_code == 403


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
    raw_body = json.dumps(event_payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    timestamp = str(int(time.time()))
    headers = {
        "Stripe-Signature": stripe_sig_header("whsec_test", raw_body, timestamp),
        "Content-Type": "application/json",
    }
    response = client.post("/stripe/webhook", data=raw_body, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    entitlement = body["entitlement"]
    assert entitlement["productId"] == "pro"

    listing = client.get("/me/entitlements", params={"userId": "stripe-user"})
    assert listing.status_code == 200
    entitlements = listing.json()["entitlements"]
    assert entitlements[0]["productId"] == "pro"
    assert entitlements[0]["grace"] is False


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
    with pytest.raises(HTTPException) as exc:
        service.process_stripe_checkout(
            event,
            headers={"Stripe-Signature": stripe_sig_header("whsec_test", body, timestamp)},
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
    with pytest.raises(HTTPException) as exc:
        service.process_stripe_checkout(
            event,
            headers={"Stripe-Signature": stripe_sig_header("whsec_test", body, timestamp)},
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
    raw_body = json.dumps(event_payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    timestamp = str(int(time.time()))
    headers = {
        "Stripe-Signature": stripe_sig_header("whsec_test", raw_body, timestamp),
        "Content-Type": "application/json",
    }
    first = client.post("/stripe/webhook", data=raw_body, headers=headers)
    assert first.status_code == 200
    assert first.json()["status"] == "ok"

    second = client.post("/stripe/webhook", data=raw_body, headers=headers)
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"

    listing = client.get("/me/entitlements", params={"userId": "dupe-user"})
    entitlements = listing.json()["entitlements"]
    assert len(entitlements) == 1


def test_restore_endpoint_reverifies_entitlement(client: TestClient) -> None:
    response = client.post(
        "/billing/restore",
        json={
            "provider": "mock",
            "platform_specific_payload": {"productId": "pro", "receipt": "PRO-RESTORE"},
        },
        headers={"x-user-id": "restore-user"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["productId"] == "pro"
    assert body["status"] == "active"
    assert body["grace"] is False


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
