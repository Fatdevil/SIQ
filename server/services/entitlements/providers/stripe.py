from __future__ import annotations

import hashlib
import hmac
import json
import os
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any, Iterable, Tuple

from .base import VerificationError, VerificationResult


class StripeVerificationAdapter:
    provider = "stripe"

    def __init__(self, secret: str | None = None) -> None:
        self._secret = secret or os.environ.get("STRIPE_WEBHOOK_SECRET")

    def verify(
        self,
        payload: Mapping[str, Any],
        *,
        headers: Mapping[str, str] | None = None,
        raw_body: bytes | None = None,
        user_id: str | None = None,
    ) -> VerificationResult:
        if not self._secret:
            raise VerificationError("stripe webhook secret not configured")

        signature_header = None
        if headers:
            for key in ("Stripe-Signature", "stripe-signature"):
                signature_header = headers.get(key)
                if signature_header:
                    break
        if not signature_header:
            raise VerificationError("missing stripe signature header")

        timestamp, signatures = self._parse_signature(signature_header)
        body = raw_body
        if body is None:
            body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        signed_payload = f"{timestamp}.{body.decode('utf-8')}"
        expected = hmac.new(
            self._secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not any(hmac.compare_digest(expected, candidate) for candidate in signatures):
            raise VerificationError("invalid stripe signature")

        session = self._extract_session(payload)
        metadata = session.get("metadata") if isinstance(session, Mapping) else {}
        if not isinstance(metadata, Mapping):
            metadata = {}
        product_id = metadata.get("productId") or metadata.get("product_id")
        user_id_metadata = metadata.get("userId") or metadata.get("user_id")
        if not product_id:
            raise VerificationError("stripe metadata missing productId")
        if not user_id_metadata:
            raise VerificationError("stripe metadata missing userId")

        expires_at = None
        subscription = session.get("subscription") if isinstance(session, Mapping) else None
        if isinstance(subscription, Mapping):
            expires = subscription.get("current_period_end")
            if isinstance(expires, (int, float)):
                expires_at = (
                    datetime.fromtimestamp(float(expires), tz=timezone.utc)
                    .replace(microsecond=0)
                    .isoformat()
                    .replace("+00:00", "Z")
                )

        return VerificationResult(
            product_id=str(product_id),
            user_id=str(user_id_metadata),
            status="active",
            expires_at=expires_at,
        )

    @staticmethod
    def _parse_signature(header: str) -> Tuple[str, Iterable[str]]:
        parts = [segment.strip() for segment in header.split(",") if segment.strip()]
        timestamp = None
        signatures: list[str] = []
        for part in parts:
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            if key == "t":
                timestamp = value
            elif key == "v1":
                signatures.append(value)
        if not timestamp or not signatures:
            raise VerificationError("invalid stripe signature header")
        return timestamp, signatures

    @staticmethod
    def _extract_session(payload: Mapping[str, Any]) -> Mapping[str, Any]:
        data = payload.get("data") if isinstance(payload, Mapping) else None
        if not isinstance(data, Mapping):
            return {}
        obj = data.get("object")
        return obj if isinstance(obj, Mapping) else {}


__all__ = ["StripeVerificationAdapter"]
