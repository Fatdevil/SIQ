from __future__ import annotations

from datetime import datetime, timedelta, timezone

from server.models import Entitlement
from server.services.entitlements.service import EntitlementService
from server.services.entitlements.store import EntitlementStore
from server.services.entitlements.sweeper import EntitlementExpirySweeper


def _iso_delta(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat().replace("+00:00", "Z")


def test_sweeper_marks_expired_entitlements(tmp_path) -> None:
    store = EntitlementStore(tmp_path / "entitlements.json")
    entitlement = Entitlement.new(
        user_id="sweep-user",
        product_id="pro",
        status="active",
        source="mock",
        expires_at=_iso_delta(-1),
    )
    store.upsert(entitlement)

    sweeper = EntitlementExpirySweeper(store)
    updated = sweeper.sweep(now=datetime.now(timezone.utc))

    assert updated
    assert updated[0].status == "expired"
    persisted = store.get("sweep-user", "pro")
    assert persisted is not None
    assert persisted.status == "expired"


def test_sweeper_marks_revoked_entitlements(tmp_path) -> None:
    store = EntitlementStore(tmp_path / "entitlements.json")
    entitlement = Entitlement.new(
        user_id="revoked-user",
        product_id="pro",
        status="active",
        source="mock",
        expires_at=_iso_delta(5),
        revoked_at=_iso_delta(-2),
    )
    store.upsert(entitlement)

    sweeper = EntitlementExpirySweeper(store)
    updated = sweeper.sweep(now=datetime.now(timezone.utc))

    assert updated
    assert updated[0].status == "revoked"
    persisted = store.get("revoked-user", "pro")
    assert persisted is not None
    assert persisted.status == "revoked"
    assert persisted.revoked_at == entitlement.revoked_at


def test_service_runs_sweep_and_uses_cron(tmp_path, monkeypatch) -> None:
    store_path = tmp_path / "service-entitlements.json"
    monkeypatch.setenv("ENTITLEMENTS_STORE_PATH", str(store_path))
    monkeypatch.setenv("SWEEP_CRON", "30 2 * * *")
    store = EntitlementStore(store_path)
    entitlement = Entitlement.new(
        user_id="service-user",
        product_id="pro",
        status="active",
        source="mock",
        expires_at=_iso_delta(-1),
    )
    store.upsert(entitlement)

    service = EntitlementService(store)
    results = service.run_expiry_sweep(now=datetime.now(timezone.utc))

    assert results
    assert results[0].status == "expired"
    assert service.sweep_cron == "30 2 * * *"
