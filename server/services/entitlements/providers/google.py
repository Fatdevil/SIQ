from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any, Callable

from .base import VerificationAdapter, VerificationError, VerificationResult
from .utils import dev_sandbox_enabled, sandbox_result


class GoogleVerificationAdapter:
    provider = "google"

    def __init__(self, *, http_post: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None) -> None:
        self._credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
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
            raise VerificationError("user_id required for google verification")

        if not self._credentials_path:
            if not dev_sandbox_enabled():
                raise VerificationError("google verification unavailable")
            return sandbox_result(payload, user_id=user_id, provider=self.provider)

        try:
            response = self._http_post(payload)
        except Exception as exc:
            raise VerificationError("google verification failed") from exc

        try:
            return self._parse_response(response, user_id)
        except Exception as exc:
            raise VerificationError("invalid google response") from exc

    def _parse_response(self, response: Mapping[str, Any], user_id: str) -> VerificationResult:
        product_id = response.get("productId") or response.get("product_id")
        status = response.get("status", "active")
        expires_at = response.get("expiresAt") or response.get("expiryTime")
        if product_id is None:
            raise VerificationError("google response missing productId")
        return VerificationResult(
            product_id=str(product_id),
            user_id=user_id,
            status=str(status),
            expires_at=str(expires_at) if expires_at is not None else None,
        )

    @staticmethod
    def _default_http_post(payload: Mapping[str, Any]) -> Mapping[str, Any]:  # pragma: no cover - network placeholder
        raise RuntimeError("google verification transport not configured")


__all__ = ["GoogleVerificationAdapter"]
