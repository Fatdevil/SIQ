from __future__ import annotations

from fastapi import HTTPException, status
from pydantic import ValidationError

from server.schemas.billing import StatusResponse, VerifyRequest, VerifyResponse
from server.services.billing import mock_verifier, store

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
    @app.post("/billing/verify")
    def verify(payload, headers):
        try:
            request = VerifyRequest.parse_obj(payload)
        except ValidationError:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"status": "error", "reason": "invalid payload"},
            )

        tier, expires_at, provider = mock_verifier.verify(request.receipt)
        record = store.set_tier(request.userId, tier, expires_at, provider)
        _emit_telemetry(
            {
                "timestampMs": 0,
                "event": "billing_verify",
                "userId": request.userId,
                "platform": request.platform,
                "tier": tier,
                "ok": True,
            }
        )
        response = VerifyResponse(**record)
        return response.dict()

    @app.get("/billing/status")
    def status_route(query, headers):
        user_id = (query or {}).get("userId")
        if not user_id:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"status": "error", "reason": "userId required"},
            )

        record = store.get_user(user_id)
        if record is None:
            record = {
                "userId": user_id,
                "tier": "free",
                "provider": "mock",
                "expiresAt": None,
            }
        response = StatusResponse(**record)
        return response.dict()
