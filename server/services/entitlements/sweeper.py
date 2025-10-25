from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from server.models import Entitlement
from .store import EntitlementStore


class EntitlementExpirySweeper:
    """Apply expiry policies to persisted entitlements."""

    def __init__(self, store: EntitlementStore) -> None:
        self._store = store

    def sweep(self, *, now: datetime | None = None) -> List[Entitlement]:
        current = now or datetime.now(timezone.utc)
        updated: List[Entitlement] = []
        for entitlement in list(self._store.iter_all()):
            target_status = entitlement.status
            revoked_at = entitlement.revoked_at

            if entitlement.revoked_at and entitlement.status != "revoked":
                target_status = "revoked"
            elif entitlement.status == "active":
                expires_at = entitlement.expires_datetime()
                if expires_at and expires_at <= current:
                    target_status = "expired"

            if target_status != entitlement.status:
                refreshed = entitlement.update(
                    status=target_status,  # type: ignore[arg-type]
                    source=entitlement.source,
                    expires_at=entitlement.expires_at,
                    last_verified_at=entitlement.last_verified_at,
                    revoked_at=revoked_at,
                    source_status=entitlement.source_status,
                    meta=entitlement.meta,
                )
                self._store.upsert(refreshed)
                updated.append(refreshed)
        return updated


__all__ = ["EntitlementExpirySweeper"]
