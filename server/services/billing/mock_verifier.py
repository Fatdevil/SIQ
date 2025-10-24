from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple


def _expiry_date(days: int) -> str:
    return (
        datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=days)
    ).isoformat().replace("+00:00", "Z")


def verify(receipt: str) -> Tuple[str, Optional[str], str]:
    normalized = receipt.upper()
    if normalized.startswith("ELITE-"):
        return "elite", _expiry_date(30), "mock"
    if normalized.startswith("PRO-"):
        return "pro", _expiry_date(30), "mock"
    return "free", None, "mock"
