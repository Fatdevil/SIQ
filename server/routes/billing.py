from __future__ import annotations

from typing import Any, Dict

from fastapi import HTTPException, status

from server.schemas.billing import (
    EntitlementListResponse,
    EntitlementResponse,
    ReceiptRequest,
    StripeWebhookRequest,
    ValidationError,
)
from server.security.entitlements import get_service
from server.services.telemetry import emit as emit_telemetry

_SERVICE = get_service()


def _resolve_user_id(
    *,
    headers: Dict[str, str] | None = None,
    payload: Dict[str, Any] | None = None,
    query: Dict[str, Any] | None = None,
) -> str:
    candidate = None
    if headers:
        candidate = headers.get("x-user-id") or headers.get("X-User-Id")
    if not candidate and query:
        candidate = query.get("userId")
    if not candidate and payload:
        candidate = payload.get("userId")
    if not candidate:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"status": "error", "reason": "userId required"},
        )
    return str(candidate)


def _to_response(entitlement) -> Dict[str, Any]:
    response = EntitlementResponse.parse_obj(entitlement.to_dict())
    return response.dict()


def register(app) -> None:
    @app.post("/billing/receipt")
    def post_receipt(payload, headers):
        try:
            request = ReceiptRequest.parse_obj(payload)
        except ValidationError:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"status": "error", "reason": "invalid payload"},
            )
        user_id = _resolve_user_id(headers=headers, payload=payload)
        emit_telemetry("start_checkout", {"userId": user_id, "provider": request.provider})
        entitlement = _SERVICE.verify_and_grant(request.provider, request.payload, user_id)
        emit_telemetry(
            "receipt_verified",
            {"userId": user_id, "productId": entitlement.product_id, "source": entitlement.source},
        )
        emit_telemetry(
            "entitlement_granted",
            {
                "userId": user_id,
                "productId": entitlement.product_id,
                "status": entitlement.status,
                "source": entitlement.source,
            },
        )
        return _to_response(entitlement)

    @app.get("/me/entitlements")
    def list_entitlements(query, headers):
        user_id = _resolve_user_id(headers=headers, query=query)
        emit_telemetry("view_upgrade", {"userId": user_id})
        entitlements = [_to_response(ent) for ent in _SERVICE.store.list_for_user(user_id)]
        response = EntitlementListResponse(entitlements=entitlements)
        return response.dict()

    @app.post("/stripe/webhook")
    def stripe_webhook(payload, headers):
        try:
            event = StripeWebhookRequest.parse_obj(payload)
        except ValidationError:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"status": "error", "reason": "invalid payload"},
            )
        entitlement = _SERVICE.process_stripe_checkout(event.dict())
        if entitlement is None:
            return {"status": "ignored"}
        emit_telemetry(
            "entitlement_granted",
            {
                "userId": entitlement.user_id,
                "productId": entitlement.product_id,
                "status": entitlement.status,
                "source": entitlement.source,
                "origin": "stripe_webhook",
            },
        )
        return {"status": "ok", "entitlement": _to_response(entitlement)}
