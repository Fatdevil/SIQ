from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Dict

from fastapi import HTTPException, status

from server.models import Entitlement
from .providers import (
    VerificationAdapter,
    VerificationError,
    VerificationResult,
    create_default_adapters,
)
from .providers.metrics import increment as increment_metric
from .providers.utils import sandbox_result
from .store import EntitlementStore
from .webhooks import WebhookEventStore


@dataclass(slots=True)
class WebhookOutcome:
    status: str
    entitlement: Entitlement | None = None


class EntitlementService:
    """Coordinates receipt verification and entitlement persistence."""

    def __init__(
        self,
        store: EntitlementStore | None = None,
        *,
        adapters: Dict[str, VerificationAdapter] | None = None,
        webhook_store: WebhookEventStore | None = None,
    ) -> None:
        self._store = store or EntitlementStore()
        self._adapters = adapters or create_default_adapters()
        self._webhook_store = webhook_store or WebhookEventStore()

    @property
    def store(self) -> EntitlementStore:
        return self._store

    @property
    def webhook_store(self) -> WebhookEventStore:
        return self._webhook_store

    # -- Receipt verification -------------------------------------------------
    def verify_and_grant(
        self,
        provider: str,
        payload: Mapping[str, Any],
        user_id: str,
    ) -> Entitlement:
        provider_key = provider.lower()
        adapter = self._adapters.get(provider_key)
        if adapter is not None:
            try:
                result = adapter.verify(payload, user_id=user_id)
            except VerificationError as exc:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail={"status": "error", "reason": str(exc)},
                ) from exc
        elif provider_key in {"mock", "test"}:
            result = sandbox_result(payload, user_id=user_id, provider=provider_key)
        else:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "reason": f"unknown provider: {provider}"},
            )

        if result.user_id != user_id:
            result = VerificationResult(
                product_id=result.product_id,
                user_id=user_id,
                status=result.status,
                expires_at=result.expires_at,
            )

        entitlement = self._store.grant(
            user_id=user_id,
            product_id=result.product_id,
            status=result.status,
            source=provider_key,
            expires_at=result.expires_at,
        )
        return entitlement

    # -- Stripe webhook -------------------------------------------------------
    def process_stripe_checkout(
        self,
        event: Mapping[str, Any],
        *,
        headers: Mapping[str, str] | None = None,
        raw_body: bytes | None = None,
    ) -> WebhookOutcome:
        provider = "stripe"
        increment_metric(provider, "received")

        event_id = str(event.get("id") or "").strip()
        if not event_id:
            increment_metric(provider, "failed")
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "reason": "missing event id"},
            )

        if self._webhook_store.is_duplicate(provider, event_id):
            increment_metric(provider, "duplicate")
            return WebhookOutcome(status="duplicate")

        event_type = event.get("type")
        if event_type != "checkout.session.completed":
            increment_metric(provider, "ignored")
            self._webhook_store.record(provider, event_id, "ignored")
            return WebhookOutcome(status="ignored")

        adapter = self._adapters.get(provider)
        if adapter is None:
            increment_metric(provider, "failed")
            self._webhook_store.record(provider, event_id, "failed")
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "reason": "stripe adapter unavailable"},
            )

        try:
            result = adapter.verify(event, headers=headers, raw_body=raw_body)
        except VerificationError as exc:
            increment_metric(provider, "failed")
            self._webhook_store.record(provider, event_id, "failed")
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "reason": str(exc)},
            ) from exc

        entitlement = self._store.grant(
            user_id=result.user_id,
            product_id=result.product_id,
            status=result.status,
            source=provider,
            expires_at=result.expires_at,
        )
        increment_metric(provider, "verified")
        self._webhook_store.record(provider, event_id, "processed")
        return WebhookOutcome(status="granted", entitlement=entitlement)


__all__ = ["EntitlementService", "WebhookOutcome"]
