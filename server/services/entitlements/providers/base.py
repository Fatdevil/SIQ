from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


class VerificationError(RuntimeError):
    """Raised when a provider verification step fails."""


@dataclass(slots=True)
class VerificationResult:
    product_id: str
    user_id: str
    status: str
    expires_at: str | None
    source_status: str | None = None
    meta: Mapping[str, Any] | None = None
    revoked_at: str | None = None


class VerificationAdapter(Protocol):
    provider: str

    def verify(
        self,
        payload: Mapping[str, Any],
        *,
        headers: Mapping[str, str] | None = None,
        raw_body: bytes | None = None,
        user_id: str | None = None,
    ) -> VerificationResult:
        ...
