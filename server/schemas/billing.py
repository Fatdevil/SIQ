from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ValidationError, constr

EntitlementStatus = Literal["active", "expired", "revoked"]
Provider = Literal["apple", "google", "stripe", "mock", "test"]


class ReceiptRequest(BaseModel):
    provider: Provider
    payload: Dict[str, Any]


class EntitlementResponse(BaseModel):
    userId: constr(strip_whitespace=True, min_length=1)
    productId: constr(strip_whitespace=True, min_length=1)
    status: EntitlementStatus
    source: constr(strip_whitespace=True, min_length=1)
    expiresAt: Optional[str] = None
    createdAt: constr(strip_whitespace=True, min_length=1)


class EntitlementListResponse(BaseModel):
    entitlements: List[EntitlementResponse]


class StripeWebhookRequest(BaseModel):
    type: constr(strip_whitespace=True, min_length=1)
    data: Dict[str, Any]


__all__ = [
    "EntitlementListResponse",
    "EntitlementResponse",
    "ReceiptRequest",
    "StripeWebhookRequest",
    "ValidationError",
]
