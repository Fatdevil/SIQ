from __future__ import annotations

from fastapi import HTTPException, status

from server.services.entitlements import EntitlementService

_service = EntitlementService()


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
        if entitlement is None or entitlement.status != "active":
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail={"status": "error", "reason": f"requires {normalized}"},
            )
        return entitlement

    return _dependency


def get_service() -> EntitlementService:
    return _service
