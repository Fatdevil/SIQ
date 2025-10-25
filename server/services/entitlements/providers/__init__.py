from __future__ import annotations

from typing import Dict

from .apple import AppleVerificationAdapter
from .base import VerificationAdapter, VerificationError, VerificationResult
from .google import GoogleVerificationAdapter
from .stripe import StripeVerificationAdapter


def create_default_adapters() -> Dict[str, VerificationAdapter]:
    return {
        "apple": AppleVerificationAdapter(),
        "google": GoogleVerificationAdapter(),
        "stripe": StripeVerificationAdapter(),
    }


__all__ = [
    "AppleVerificationAdapter",
    "GoogleVerificationAdapter",
    "StripeVerificationAdapter",
    "VerificationAdapter",
    "VerificationError",
    "VerificationResult",
    "create_default_adapters",
]
