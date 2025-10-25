from __future__ import annotations

from fastapi import HTTPException, status
from pydantic import ValidationError

from server.schemas.billing import (
    EntitlementsResponse,
    ReceiptRequest,
    StatusResponse,
    VerifyRequest,
    VerifyResponse,
)
from server.services.billing import mock_verifier, store

_ORDER = {"free": 0, "pro": 1, "elite": 2}
_FEATURE_REQUIREMENTS = {
    "AI_PERSONAS": "pro",
    "ADVANCED_METRICS": "pro",
    "TEAM_DASHBOARD": "elite",
}


def _resolve_record(user_id: str) -> dict:
    record = store.get_user(user_id)
    if record is None:
        record = {
            "userId": user_id,
            "tier": "free",
            "provider": "mock",
            "expiresAt": None,
        }
    return record


def _entitlements_payload(record: dict) -> dict:
    tier = record.get("tier", "free")
    entitlements = {
        "free": True,
        "pro": _ORDER.get(tier, 0) >= _ORDER["pro"],
        "elite": _ORDER.get(tier, 0) >= _ORDER["elite"],
    }
    features = {
        feature: entitlements[_FEATURE_REQUIREMENTS[feature]]
        for feature in _FEATURE_REQUIREMENTS
    }
    response = EntitlementsResponse(
        userId=record.get("userId", ""),
        tier=tier,
        provider=record.get("provider"),
        expiresAt=record.get("expiresAt"),
        entitlements=entitlements,
        features=features,
    )
    return response.dict()

try:  # pragma: no cover - optional telemetry integration
    from server.routes.ws_telemetry import publish_telemetry  # type: ignore
except Exception:  # pragma: no cover - telemetry optional in tests
    publish_telemetry = None


def _emit_telemetry(event: dict[str, object]) -> None:
    if publish_telemetry is None:
        return
    try:
        publish_telemetry(event)
    except Exception:
        # Telemetry is best effort only.
        pass


def register(app) -> None:
    def _handle_purchase(request: VerifyRequest) -> dict:
        tier, expires_at, provider = mock_verifier.verify(request.receipt)
        record = store.set_tier(request.userId, tier, expires_at, provider)
        _emit_telemetry(
            {
                "timestampMs": 0,
                "event": "receipt_verified",
                "userId": request.userId,
                "platform": request.platform,
                "tier": tier,
                "mode": "purchase",
            }
        )
        return record

    @app.post("/billing/verify")
    def verify(payload, headers):
        try:
            request = VerifyRequest.parse_obj(payload)
        except ValidationError:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"status": "error", "reason": "invalid payload"},
            )

        record = _handle_purchase(request)
        response = VerifyResponse(**record)
        return response.dict()

    @app.post("/billing/receipt")
    def receipt(payload, headers):
        try:
            request = ReceiptRequest.parse_obj(payload)
        except ValidationError:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"status": "error", "reason": "invalid payload"},
            )

        if request.mode == "purchase" and not request.receipt:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"status": "error", "reason": "receipt required"},
            )

        if request.mode == "restore":
            _emit_telemetry(
                {
                    "timestampMs": 0,
                    "event": "restore_clicked",
                    "userId": request.userId,
                    "platform": request.platform,
                }
            )
            record = _resolve_record(request.userId)
            return _entitlements_payload(record)

        verify_request = VerifyRequest(
            userId=request.userId,
            platform=request.platform,
            receipt=request.receipt or "",
        )
        record = _handle_purchase(verify_request)
        return _entitlements_payload(record)

    @app.get("/billing/status")
    def status_route(query, headers):
        user_id = (query or {}).get("userId")
        if not user_id:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"status": "error", "reason": "userId required"},
            )

        record = _resolve_record(user_id)
        response = StatusResponse(**record)
        return response.dict()

    @app.get("/me/entitlements")
    def entitlements(query, headers):
        query = query or {}
        user_id = query.get("userId") or headers.get("x-user-id")
        if not user_id:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"status": "error", "reason": "userId required"},
            )
        record = _resolve_record(user_id)
        return _entitlements_payload(record)
