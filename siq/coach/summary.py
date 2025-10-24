from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Deque, Dict, List

from .personas import PersonaProfile, PersonaRegistry


@dataclass
class RunRecord:
    ball_speed_mps: float
    club_speed_mps: float
    carry_m: float
    captured_at: datetime


class RunHistory:
    """Maintain a bounded history of runs per user."""

    def __init__(self, max_runs: int = 20) -> None:
        self._max_runs = max_runs
        self._runs: Dict[str, Deque[RunRecord]] = {}

    def add_run(self, user_id: str, record: RunRecord) -> None:
        bucket = self._runs.setdefault(user_id, deque(maxlen=self._max_runs))
        bucket.append(record)

    def last_runs(self, user_id: str, limit: int) -> List[RunRecord]:
        bucket = self._runs.get(user_id)
        if not bucket:
            return []
        if limit <= 0:
            return []
        return list(list(bucket)[-limit:])


class WeeklySummaryJob:
    """Aggregate run history into short persona-aware summaries."""

    def __init__(
        self,
        history: RunHistory,
        registry: PersonaRegistry | None = None,
        max_chars: int = 600,
    ) -> None:
        self._history = history
        self._registry = registry or PersonaRegistry()
        self._max_chars = max_chars

    def summarize(self, user_id: str, persona_name: str | None = None, last_n: int = 5) -> str:
        runs = self._history.last_runs(user_id, last_n)
        persona: PersonaProfile = self._registry.resolve(persona_name)
        if not runs:
            return persona.format_response("No recent swings logged. Capture a new session to unlock insights.")
        avg_ball = sum(run.ball_speed_mps for run in runs) / len(runs)
        avg_club = sum(run.club_speed_mps for run in runs) / len(runs)
        avg_carry = sum(run.carry_m for run in runs) / len(runs)

        trend = "stable"
        if len(runs) >= 2:
            delta = runs[-1].carry_m - runs[0].carry_m
            if delta > 1.0:
                trend = "up"
            elif delta < -1.0:
                trend = "down"

        insight = (
            f"Averaging {avg_ball:.1f} m/s ball and {avg_club:.1f} m/s club speed with {avg_carry:.1f} m carry. "
            f"Carry trend looks {trend}. Lock tempo and keep sequencing smooth."
        )
        summary = persona.format_response(insight)
        if len(summary) <= self._max_chars:
            return summary
        return summary[: self._max_chars - 1].rstrip() + "…"
