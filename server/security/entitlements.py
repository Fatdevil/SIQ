from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status

from server.models import Entitlement
from server.services.entitlements import EntitlementService
from server.services.entitlements.config import get_grace_days

_service = EntitlementService()


@dataclass(slots=True)
class EntitlementAccess:
    entitlement: Entitlement
    grace: bool = False


def require_entitlement(product_id: str):
    normalized = product_id.lower()

    def _dependency(userId: str | None = None, headers: dict | None = None):
        user_id = userId
        if headers and not user_id:
            user_id = headers.get("x-user-id") or headers.get("X-User-Id")
        if not user_id:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"status": "error", "reason": "userId required"},
            )
        entitlement = _service.store.get(str(user_id), normalized)
        if entitlement is None:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail={"status": "error", "reason": f"requires {normalized}"},
            )

        if entitlement.status == "revoked" or entitlement.revoked_at:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail={"status": "error", "reason": f"{normalized} entitlement revoked"},
            )

        if entitlement.status == "active":
            return EntitlementAccess(entitlement=entitlement, grace=False)

        grace_days = get_grace_days()
        if entitlement.within_grace(grace_days):
            return EntitlementAccess(entitlement=entitlement, grace=True)

        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail={"status": "error", "reason": f"{normalized} entitlement expired"},
        )

    return _dependency


def get_service() -> EntitlementService:
    return _service


__all__ = ["EntitlementAccess", "require_entitlement", "get_service"]
