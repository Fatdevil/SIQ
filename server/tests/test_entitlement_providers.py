import hashlib
import hmac
import json
from typing import Mapping

import pytest

from server.services.entitlements.providers.apple import AppleVerificationAdapter
from server.services.entitlements.providers.base import VerificationError
from server.services.entitlements.providers.google import GoogleVerificationAdapter
from server.services.entitlements.providers.stripe import StripeVerificationAdapter


def _stripe_signature(secret: str, timestamp: str, body: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), f"{timestamp}.{body}".encode("utf-8"), hashlib.sha256)
    return digest.hexdigest()


def test_stripe_adapter_verifies_signature() -> None:
    adapter = StripeVerificationAdapter(secret="whsec_test")
    payload = {
        "id": "evt_test_adapter",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_adapter",
                "metadata": {"userId": "user-1", "productId": "pro"},
            }
        },
    }
    body = json.dumps(payload)
    timestamp = "1234567890"
    signature = _stripe_signature("whsec_test", timestamp, body)
    result = adapter.verify(
        payload,
        headers={"Stripe-Signature": f"t={timestamp},v1={signature}"},
        raw_body=body.encode("utf-8"),
    )
    assert result.product_id == "pro"
    assert result.user_id == "user-1"
    assert result.status == "active"


def test_stripe_adapter_missing_signature() -> None:
    adapter = StripeVerificationAdapter(secret="whsec_test")
    payload = {"data": {"object": {"metadata": {"userId": "user-1", "productId": "pro"}}}}
    with pytest.raises(VerificationError):
        adapter.verify(payload, headers={}, raw_body=b"{}")


def test_apple_adapter_returns_sandbox_when_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APPLE_ISSUER_ID", raising=False)
    monkeypatch.delenv("APPLE_KEY_ID", raising=False)
    monkeypatch.delenv("APPLE_PRIVATE_KEY", raising=False)
    monkeypatch.setenv("ENTITLEMENTS_DEV_SANDBOX_OK", "1")
    adapter = AppleVerificationAdapter()
    result = adapter.verify({"productId": "elite"}, user_id="apple-user")
    assert result.product_id == "elite"
    assert result.user_id == "apple-user"
    assert result.status == "active"


def test_apple_adapter_requires_flag_when_no_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APPLE_ISSUER_ID", raising=False)
    monkeypatch.delenv("APPLE_KEY_ID", raising=False)
    monkeypatch.delenv("APPLE_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("ENTITLEMENTS_DEV_SANDBOX_OK", raising=False)
    adapter = AppleVerificationAdapter()
    with pytest.raises(VerificationError):
        adapter.verify({"productId": "pro"}, user_id="apple-user")


def test_apple_adapter_parses_response(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_post(url: str, body: bytes, headers: Mapping[str, str]) -> bytes:
        response = {
            "data": {
                "attributes": {
                    "productId": "pro",
                    "expiresDateMs": 0,
                }
            }
        }
        return json.dumps(response).encode("utf-8")

    monkeypatch.setenv("APPLE_ISSUER_ID", "issuer")
    monkeypatch.setenv("APPLE_KEY_ID", "key")
    monkeypatch.setenv("APPLE_PRIVATE_KEY", "private")
    monkeypatch.delenv("ENTITLEMENTS_DEV_SANDBOX_OK", raising=False)
    adapter = AppleVerificationAdapter(http_post=_fake_post)
    result = adapter.verify({"receipt": "token"}, user_id="apple-user")
    assert result.product_id == "pro"
    assert result.expires_at is not None


def test_google_adapter_returns_sandbox(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.setenv("ENTITLEMENTS_DEV_SANDBOX_OK", "1")
    adapter = GoogleVerificationAdapter()
    result = adapter.verify({"productId": "pro"}, user_id="google-user")
    assert result.product_id == "pro"
    assert result.user_id == "google-user"


def test_google_adapter_requires_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("ENTITLEMENTS_DEV_SANDBOX_OK", raising=False)
    adapter = GoogleVerificationAdapter()
    with pytest.raises(VerificationError):
        adapter.verify({"productId": "pro"}, user_id="google-user")


def test_google_adapter_uses_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "creds.json")
    monkeypatch.delenv("ENTITLEMENTS_DEV_SANDBOX_OK", raising=False)

    def _fake_http(payload: Mapping[str, object]) -> Mapping[str, object]:
        return {"productId": payload.get("productId"), "status": "active", "expiresAt": "2025-01-01T00:00:00Z"}

    adapter = GoogleVerificationAdapter(http_post=_fake_http)
    result = adapter.verify({"productId": "elite"}, user_id="google-user")
    assert result.product_id == "elite"
    assert result.expires_at == "2025-01-01T00:00:00Z"
