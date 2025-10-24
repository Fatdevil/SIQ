from __future__ import annotations

from fastapi import HTTPException

from server.services.billing.store import get_user

ORDER = {"free": 0, "pro": 1, "elite": 2}


def require_tier(required: str):
    required_lower = required.lower()
    if required_lower not in ORDER:
        raise ValueError(f"unknown tier: {required}")

    def _dependency(userId: str | None = None):
        user = get_user(userId or "") or {"tier": "free"}
        current_tier = user.get("tier", "free")
        if ORDER.get(current_tier, 0) < ORDER[required_lower]:
            raise HTTPException(
                status_code=403,
                detail={"status": "error", "reason": f"requires {required_lower.upper()}"},
            )
        return user

    return _dependency
