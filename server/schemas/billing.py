from __future__ import annotations

from pydantic import BaseModel, constr
from typing import Dict, Optional, Literal

Platform = Literal["ios", "android", "web"]
ReceiptMode = Literal["purchase", "restore"]


class VerifyRequest(BaseModel):
    userId: constr(strip_whitespace=True, min_length=1)
    platform: Platform
    receipt: constr(strip_whitespace=True, min_length=1)


class VerifyResponse(BaseModel):
    userId: str
    tier: Literal["free", "pro", "elite"]
    provider: str = "mock"
    expiresAt: Optional[str] = None


class StatusResponse(BaseModel):
    userId: str
    tier: Literal["free", "pro", "elite"]
    provider: Optional[str] = "mock"
    expiresAt: Optional[str] = None


class ReceiptRequest(BaseModel):
    userId: constr(strip_whitespace=True, min_length=1)
    platform: Platform
    mode: ReceiptMode = "purchase"
    receipt: Optional[constr(strip_whitespace=True, min_length=1)] = None


class EntitlementsResponse(BaseModel):
    userId: str
    tier: Literal["free", "pro", "elite"]
    provider: Optional[str] = "mock"
    expiresAt: Optional[str] = None
    entitlements: Dict[str, bool]
    features: Dict[str, bool]
