from __future__ import annotations

import os
from typing import Mapping

DEFAULT_GRACE_DAYS = 7
DEFAULT_SWEEP_CRON = "0 3 * * *"


def _resolve_env(environ: Mapping[str, str] | None = None) -> Mapping[str, str]:
    if environ is not None:
        return environ
    return os.environ


def get_grace_days(environ: Mapping[str, str] | None = None) -> int:
    env = _resolve_env(environ)
    value = env.get("GRACE_DAYS") if hasattr(env, "get") else None
    if value is None:
        return DEFAULT_GRACE_DAYS
    try:
        days = int(str(value).strip())
    except (TypeError, ValueError):
        return DEFAULT_GRACE_DAYS
    return max(days, 0)


def get_sweep_cron(environ: Mapping[str, str] | None = None) -> str:
    env = _resolve_env(environ)
    value = env.get("SWEEP_CRON") if hasattr(env, "get") else None
    if value is None:
        return DEFAULT_SWEEP_CRON
    text = str(value).strip()
    return text or DEFAULT_SWEEP_CRON


__all__ = ["DEFAULT_GRACE_DAYS", "DEFAULT_SWEEP_CRON", "get_grace_days", "get_sweep_cron"]
