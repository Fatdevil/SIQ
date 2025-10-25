from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Mapping as TypingMapping

from fastapi import HTTPException, status

from server.models import Entitlement
from .config import get_sweep_cron
from .providers import (
    VerificationAdapter,
    VerificationError,
    VerificationResult,
    create_default_adapters,
)
from .providers.metrics import increment as increment_metric
from .providers.utils import sandbox_result
from .store import EntitlementStore
from .sweeper import EntitlementExpirySweeper
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
        self._sweeper = EntitlementExpirySweeper(self._store)
        self._sweep_cron = get_sweep_cron()

    @property
    def store(self) -> EntitlementStore:
        return self._store

    @property
    def webhook_store(self) -> WebhookEventStore:
        return self._webhook_store

    @property
    def sweep_cron(self) -> str:
        return self._sweep_cron

    def run_expiry_sweep(self, *, now: datetime | None = None) -> list[Entitlement]:
        return self._sweeper.sweep(now=now)

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

        verified_at = Entitlement._now_iso()
        revoked_at = result.revoked_at
        if result.status == "revoked" and not revoked_at:
            revoked_at = verified_at
        if result.status != "revoked":
            revoked_at = None

        entitlement = self._store.grant(
            user_id=user_id,
            product_id=result.product_id,
            status=result.status,
            source=provider_key,
            expires_at=result.expires_at,
            last_verified_at=verified_at,
            revoked_at=revoked_at,
            source_status=result.source_status,
            meta=result.meta,
        )
        return entitlement

    def restore(
        self,
        provider: str,
        payload: TypingMapping[str, Any] | None,
        user_id: str,
    ) -> Entitlement:
        data: Mapping[str, Any]
        if payload is None:
            data = {}
        elif isinstance(payload, Mapping):
            data = payload
        else:
            data = dict(payload)  # type: ignore[arg-type]
        return self.verify_and_grant(provider, data, user_id)

    # -- Stripe webhook -------------------------------------------------------
    def process_stripe_checkout(
        self,
        event: Mapping[str, Any],
        *,
        headers: Mapping[str, str] | None = None,
        raw_body: bytes,
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
