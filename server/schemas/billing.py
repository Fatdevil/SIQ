from __future__ import annotations

from pydantic import BaseModel, constr
from typing import Optional, Literal

Platform = Literal["ios", "android"]


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
