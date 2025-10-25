from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from .base import VerificationResult

_DEV_FLAG_ENV = "ENTITLEMENTS_DEV_SANDBOX_OK"


def future_iso(days: int) -> str:
    return (
        datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=days)
    ).isoformat().replace("+00:00", "Z")


def dev_sandbox_enabled(environ: Mapping[str, str] | None = None) -> bool:
    env = environ or {}
    value = env.get(_DEV_FLAG_ENV) if hasattr(env, "get") else None
    if value is None:
        import os

        value = os.environ.get(_DEV_FLAG_ENV)
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def sandbox_result(
    payload: Mapping[str, Any],
    *,
    user_id: str,
    provider: str,
) -> VerificationResult:
    token = str(
        payload.get("receipt")
        or payload.get("token")
        or payload.get("id")
        or ""
    ).upper()
    product_id = str(
        payload.get("productId")
        or payload.get("product_id")
        or "pro"
    )
    status = "active"
    expires_at: str | None = None
    if token.startswith("EXPIRED-"):
        status = "expired"
        expires_at = future_iso(-1)
    elif token.startswith("REVOKED-"):
        status = "revoked"
    else:
        normalized = product_id.lower()
        if normalized in {"pro", "elite"}:
            expires_at = future_iso(30)
    return VerificationResult(
        product_id=product_id,
        user_id=user_id,
        status=status,
        expires_at=expires_at,
    )
