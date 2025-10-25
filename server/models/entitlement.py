from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import ClassVar, Dict, Literal

EntitlementStatus = Literal["active", "expired", "revoked"]
EntitlementSource = Literal["apple", "google", "stripe", "mock", "test"]


@dataclass(frozen=True, slots=True)
class Entitlement:
    """Represents a product entitlement for a specific user."""

    user_id: str
    product_id: str
    status: EntitlementStatus
    source: EntitlementSource
    expires_at: str | None
    created_at: str

    _VALID_STATUS: ClassVar[set[str]] = {"active", "expired", "revoked"}

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @classmethod
    def new(
        cls,
        *,
        user_id: str,
        product_id: str,
        status: EntitlementStatus,
        source: EntitlementSource,
        expires_at: str | None,
    ) -> "Entitlement":
        cls._validate_status(status)
        return cls(
            user_id=user_id,
            product_id=product_id,
            status=status,
            source=source,
            expires_at=expires_at,
            created_at=cls._now_iso(),
        )

    @classmethod
    def _validate_status(cls, status: str) -> None:
        if status not in cls._VALID_STATUS:
            raise ValueError(f"invalid entitlement status: {status}")

    def update(
        self,
        *,
        status: EntitlementStatus,
        source: EntitlementSource,
        expires_at: str | None,
    ) -> "Entitlement":
        self._validate_status(status)
        return replace(self, status=status, source=source, expires_at=expires_at)

    def to_dict(self) -> Dict[str, str | None]:
        return {
            "userId": self.user_id,
            "productId": self.product_id,
            "status": self.status,
            "source": self.source,
            "expiresAt": self.expires_at,
            "createdAt": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, str | None]) -> "Entitlement":
        status = str(payload.get("status", "active"))
        cls._validate_status(status)
        created = payload.get("createdAt")
        if not created:
            created = cls._now_iso()
        return cls(
            user_id=str(payload.get("userId", "")),
            product_id=str(payload.get("productId", "")),
            status=status,  # type: ignore[arg-type]
            source=str(payload.get("source", "mock")),  # type: ignore[arg-type]
            expires_at=payload.get("expiresAt"),
            created_at=str(created),
        )
