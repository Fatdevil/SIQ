from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Deque, Dict
from collections import deque


class GuardrailViolation(Exception):
    """Raised when a guardrail prevents an action."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass
class _RequestRecord:
    timestamp: float


class InMemoryRateLimiter:
    """Simple sliding-window rate limiter."""

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._events: Dict[str, Deque[_RequestRecord]] = {}

    def hit(self, key: str) -> None:
        now = time.monotonic()
        events = self._events.setdefault(key, deque())
        while events and now - events[0].timestamp > self._window_seconds:
            events.popleft()
        if len(events) >= self._max_requests:
            raise GuardrailViolation("rate_limited")
        events.append(_RequestRecord(timestamp=now))


@dataclass
class _BudgetState:
    available: int
    refreshed_at: float


class TokenBudget:
    """Guardrails for approximate token consumption."""

    def __init__(self, max_tokens: int, refill_seconds: float) -> None:
        self._max_tokens = max_tokens
        self._refill_seconds = refill_seconds
        self._state: Dict[str, _BudgetState] = {}

    def _current_state(self, key: str, now: float) -> _BudgetState:
        state = self._state.get(key)
        if state is None or now - state.refreshed_at >= self._refill_seconds:
            state = _BudgetState(available=self._max_tokens, refreshed_at=now)
            self._state[key] = state
        return state

    def consume(self, key: str, amount: int) -> None:
        if amount > self._max_tokens:
            raise GuardrailViolation("token_budget_exceeded")
        now = time.monotonic()
        state = self._current_state(key, now)
        if state.available < amount:
            raise GuardrailViolation("token_budget_exhausted")
        state.available -= amount
        state.refreshed_at = now
