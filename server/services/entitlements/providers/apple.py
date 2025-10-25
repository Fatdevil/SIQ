from __future__ import annotations

import base64
import json
import os
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any, Callable

from .base import VerificationError, VerificationResult
from .utils import dev_sandbox_enabled, future_iso, sandbox_result

_SANDBOX_SUBSCRIPTIONS_URL = "https://api.storekit-sandbox.itunes.apple.com/inApps/v1/subscriptions/lookup"


def _encode_segment(segment: Mapping[str, Any]) -> str:
    raw = json.dumps(segment, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _encode_jwt(header: Mapping[str, Any], claims: Mapping[str, Any], private_key: str) -> str:
    header_segment = _encode_segment(header)
    payload_segment = _encode_segment(claims)
    signature = base64.urlsafe_b64encode(private_key.encode("utf-8")[:16]).rstrip(b"=").decode("ascii")
    return f"{header_segment}.{payload_segment}.{signature}"


class AppleVerificationAdapter:
    provider = "apple"

    def __init__(self, *, http_post: Callable[[str, bytes, Mapping[str, str]], bytes] | None = None) -> None:
        self._issuer_id = os.environ.get("APPLE_ISSUER_ID")
        self._key_id = os.environ.get("APPLE_KEY_ID")
        self._private_key = os.environ.get("APPLE_PRIVATE_KEY")
        self._http_post = http_post or self._default_http_post

    def verify(
        self,
        payload: Mapping[str, Any],
        *,
        headers: Mapping[str, str] | None = None,
        raw_body: bytes | None = None,
        user_id: str | None = None,
    ) -> VerificationResult:
        if not user_id:
            raise VerificationError("user_id required for apple verification")

        if not self._issuer_id or not self._key_id or not self._private_key:
            if not dev_sandbox_enabled():
                raise VerificationError("apple verification unavailable")
            return sandbox_result(payload, user_id=user_id, provider=self.provider)

        try:
            response = self._call_sandbox(payload)
        except Exception as exc:
            raise VerificationError("apple sandbox verification failed") from exc

        try:
            return self._parse_response(response, user_id)
        except Exception as exc:
            raise VerificationError("invalid apple sandbox response") from exc

    def _call_sandbox(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        header = {"alg": "ES256", "kid": self._key_id, "typ": "JWT"}
        now = int(datetime.now(timezone.utc).timestamp())
        claims = {"iss": self._issuer_id, "iat": now, "exp": now + 1800, "aud": "appstoreconnect-v1"}
        token = _encode_jwt(header, claims, self._private_key)

        body = json.dumps(payload).encode("utf-8")
        response_bytes = self._http_post(
            _SANDBOX_SUBSCRIPTIONS_URL,
            body,
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )
        return json.loads(response_bytes.decode("utf-8"))

    def _parse_response(self, response: Mapping[str, Any], user_id: str) -> VerificationResult:
        latest = response.get("data") or {}
        attributes = latest.get("attributes") if isinstance(latest, Mapping) else {}
        product_id = attributes.get("productId")
        expires = attributes.get("expiresDate") or attributes.get("expiresDateMs")
        if product_id is None:
            raise VerificationError("apple sandbox missing productId")
        expires_at = None
        if isinstance(expires, str):
            expires_at = str(expires)
        elif isinstance(expires, (int, float)):
            expires_at = (
                datetime.fromtimestamp(float(expires) / 1000, tz=timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
            )
        elif expires:
            raise VerificationError("apple sandbox invalid expires")
        return VerificationResult(
            product_id=str(product_id),
            user_id=user_id,
            status="active",
            expires_at=expires_at or future_iso(30),
        )

    @staticmethod
    def _default_http_post(url: str, body: bytes, headers: Mapping[str, str]) -> bytes:  # pragma: no cover - network
        import urllib.request

        request = urllib.request.Request(url, data=body, headers=dict(headers), method="POST")
        with urllib.request.urlopen(request, timeout=5) as handle:  # type: ignore[call-arg]
            return handle.read()


__all__ = ["AppleVerificationAdapter"]
