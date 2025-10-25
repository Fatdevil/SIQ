from __future__ import annotations

import logging
from collections import Counter, defaultdict
from typing import Dict

_logger = logging.getLogger("billing.providers")
_counters: Dict[str, Counter[str]] = defaultdict(Counter)


def increment(provider: str, metric: str) -> None:
    counter = _counters[provider]
    counter[metric] += 1
    _logger.debug("provider_metrics", extra={"provider": provider, "metric": metric, "value": counter[metric]})


def snapshot() -> Dict[str, Dict[str, int]]:
    return {provider: dict(counter) for provider, counter in _counters.items()}
