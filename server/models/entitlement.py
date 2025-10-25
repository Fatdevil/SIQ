from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar, Dict, Literal, Mapping

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
    last_verified_at: str
    revoked_at: str | None = None
    source_status: str | None = None
    meta: Mapping[str, Any] = field(default_factory=dict)

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
        last_verified_at: str | None = None,
        revoked_at: str | None = None,
        source_status: str | None = None,
        meta: Mapping[str, Any] | None = None,
    ) -> "Entitlement":
        cls._validate_status(status)
        now = cls._now_iso()
        return cls(
            user_id=user_id,
            product_id=product_id,
            status=status,
            source=source,
            expires_at=expires_at,
            created_at=now,
            last_verified_at=last_verified_at or now,
            revoked_at=revoked_at,
            source_status=source_status,
            meta=dict(meta) if meta is not None else {},
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
        last_verified_at: str | None = None,
        revoked_at: str | None = None,
        source_status: str | None = None,
        meta: Mapping[str, Any] | None = None,
    ) -> "Entitlement":
        self._validate_status(status)
        next_meta = dict(meta) if meta is not None else dict(self.meta)
        next_last_verified = last_verified_at or self.last_verified_at
        return replace(
            self,
            status=status,
            source=source,
            expires_at=expires_at,
            last_verified_at=next_last_verified,
            revoked_at=revoked_at,
            source_status=source_status,
            meta=next_meta,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "userId": self.user_id,
            "productId": self.product_id,
            "status": self.status,
            "source": self.source,
            "expiresAt": self.expires_at,
            "createdAt": self.created_at,
            "lastVerifiedAt": self.last_verified_at,
            "revokedAt": self.revoked_at,
            "sourceStatus": self.source_status,
            "meta": dict(self.meta),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "Entitlement":
        status = str(payload.get("status", "active"))
        cls._validate_status(status)
        created = payload.get("createdAt")
        if not created:
            created = cls._now_iso()
        last_verified = payload.get("lastVerifiedAt")
        if not last_verified:
            last_verified = created
        raw_meta = payload.get("meta")
        meta: Mapping[str, Any]
        if isinstance(raw_meta, Mapping):
            meta = dict(raw_meta)
        elif isinstance(raw_meta, dict):  # pragma: no cover - defensive
            meta = dict(raw_meta)
        else:
            meta = {}
        return cls(
            user_id=str(payload.get("userId", "")),
            product_id=str(payload.get("productId", "")),
            status=status,  # type: ignore[arg-type]
            source=str(payload.get("source", "mock")),  # type: ignore[arg-type]
            expires_at=payload.get("expiresAt"),
            created_at=str(created),
            last_verified_at=str(last_verified),
            revoked_at=payload.get("revokedAt"),
            source_status=payload.get("sourceStatus"),
            meta=meta,
        )

    @staticmethod
    def _parse_iso(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            normalized = value.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized).astimezone(timezone.utc)
        except ValueError:  # pragma: no cover - defensive
            return None

    def expires_datetime(self) -> datetime | None:
        return self._parse_iso(self.expires_at)

    def last_verified_datetime(self) -> datetime | None:
        return self._parse_iso(self.last_verified_at)

    def within_grace(self, grace_days: int, *, now: datetime | None = None) -> bool:
        if grace_days <= 0:
            return False
        if self.status == "revoked" or self.revoked_at:
            return False
        verified_at = self.last_verified_datetime()
        if verified_at is None:
            return False
        current = now or datetime.now(timezone.utc)
        window = verified_at + timedelta(days=grace_days)
        return window >= current
