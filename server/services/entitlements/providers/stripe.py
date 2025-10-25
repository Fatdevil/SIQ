from __future__ import annotations

import hashlib
import hmac
import json
import os
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Tuple

from .base import VerificationError, VerificationResult
from .utils import dev_sandbox_enabled


class StripeVerificationAdapter:
    provider = "stripe"

    def __init__(
        self,
        secret: str | None = None,
        *,
        secret_getter: Callable[[], str | None] | None = None,
    ) -> None:
        if secret_getter is not None:
            self._secret_getter = secret_getter
        elif secret is not None:
            self._secret_getter = lambda: secret
        else:
            self._secret_getter = lambda: os.environ.get("STRIPE_WEBHOOK_SECRET")

    def verify(
        self,
        payload: Mapping[str, Any] | None = None,
        *,
        headers: Mapping[str, str] | None = None,
        raw_body: bytes | None = None,
        user_id: str | None = None,
    ) -> VerificationResult:
        body = raw_body
        if body is None:
            if payload is None:
                raise VerificationError("stripe raw payload required")
            body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

        headers = headers or {}
        signature_header = None
        for key in ("Stripe-Signature", "stripe-signature"):
            signature_header = headers.get(key)
            if signature_header:
                break

        secret = (self._secret_getter() or "").strip()
        if not secret:
            if dev_sandbox_enabled():
                event = self._load_event(body)
                return self._build_result(event)
            raise VerificationError("stripe webhook secret not configured")

        if not signature_header:
            raise VerificationError("missing stripe signature header")

        timestamp, signatures = self._parse_signature(signature_header)
        try:
            signed_payload = timestamp.encode("ascii") + b"." + body
        except UnicodeEncodeError as exc:
            raise VerificationError("invalid stripe timestamp") from exc

        digest = hmac.new(secret.encode("ascii"), signed_payload, hashlib.sha256).hexdigest()
        if not any(hmac.compare_digest(digest, candidate) for candidate in signatures):
            raise VerificationError("invalid stripe signature")

        event = self._load_event(body)
        return self._build_result(event)

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
    def _load_event(body: bytes) -> Mapping[str, Any]:
        try:
            decoded = body.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise VerificationError("invalid stripe payload encoding") from exc
        try:
            event = json.loads(decoded)
        except json.JSONDecodeError as exc:
            raise VerificationError("invalid stripe payload json") from exc
        if not isinstance(event, Mapping):
            raise VerificationError("invalid stripe payload type")
        return event

    def _build_result(self, event: Mapping[str, Any]) -> VerificationResult:
        session = self._extract_session(event)
        metadata = session.get("metadata") if isinstance(session, Mapping) else {}
        if not isinstance(metadata, Mapping):
            raise VerificationError("stripe metadata invalid")
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
    def _extract_session(payload: Mapping[str, Any]) -> Mapping[str, Any]:
        data = payload.get("data") if isinstance(payload, Mapping) else None
        if not isinstance(data, Mapping):
            return {}
        obj = data.get("object")
        return obj if isinstance(obj, Mapping) else {}


__all__ = ["StripeVerificationAdapter"]
