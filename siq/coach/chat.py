from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from .guardrails import GuardrailViolation, InMemoryRateLimiter, TokenBudget
from .personas import PersonaPreferenceStore, PersonaProfile, PersonaRegistry


@dataclass
class ConversationTurn:
    role: str
    content: str

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "ConversationTurn":
        role = str(payload.get("role", ""))
        content = str(payload.get("content", ""))
        if not role or not content:
            raise ValueError("conversation turn requires role and content")
        return cls(role=role, content=content)


@dataclass
class CoachChatRequest:
    user_id: str
    message: str
    persona: str | None = None
    history: List[ConversationTurn] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "CoachChatRequest":
        if "userId" not in payload or not str(payload["userId"]).strip():
            raise ValueError("userId is required")
        if "message" not in payload or not str(payload["message"]).strip():
            raise ValueError("message is required")

        history_payload = payload.get("history", [])
        history: List[ConversationTurn] = []
        if history_payload:
            if not isinstance(history_payload, Iterable):
                raise ValueError("history must be iterable")
            for item in history_payload:
                if not isinstance(item, dict):
                    raise ValueError("history entries must be objects")
                history.append(ConversationTurn.from_dict(item))

        persona = payload.get("persona")
        if persona is not None and not str(persona).strip():
            raise ValueError("persona must be non-empty when provided")

        return cls(
            user_id=str(payload["userId"]).strip(),
            message=str(payload["message"]).strip(),
            persona=str(persona).strip() if persona is not None else None,
            history=history,
        )

    def estimated_tokens(self) -> int:
        base = len(self.message.split())
        history_tokens = sum(len(turn.content.split()) for turn in self.history)
        return base + history_tokens + max(len(self.history), 1)


class CoachResponder:
    """Generate persona-aware responses with guardrails."""

    def __init__(
        self,
        preferences: PersonaPreferenceStore | None = None,
        registry: PersonaRegistry | None = None,
        rate_limiter: InMemoryRateLimiter | None = None,
        token_budget: TokenBudget | None = None,
        max_chars: int = 600,
    ) -> None:
        self._registry = registry or PersonaRegistry()
        self._preferences = preferences or PersonaPreferenceStore(self._registry)
        self._rate_limiter = rate_limiter or InMemoryRateLimiter(max_requests=5, window_seconds=60.0)
        self._token_budget = token_budget or TokenBudget(max_tokens=1200, refill_seconds=3600.0)
        self._max_chars = max_chars

    @property
    def preferences(self) -> PersonaPreferenceStore:
        return self._preferences

    def _select_persona(self, request: CoachChatRequest) -> PersonaProfile:
        if request.persona:
            return self._preferences.set_preference(request.user_id, request.persona)
        return self._preferences.get_preference(request.user_id)

    def _apply_guardrails(self, request: CoachChatRequest) -> None:
        self._rate_limiter.hit(request.user_id)
        tokens = request.estimated_tokens()
        self._token_budget.consume(request.user_id, tokens)

    def _render_insight(self, persona: PersonaProfile, request: CoachChatRequest) -> str:
        history_summary = " ".join(turn.content for turn in request.history[-2:])
        insight_parts = [request.message]
        if history_summary:
            insight_parts.append(f"Recent context: {history_summary}")
        insight = " ".join(insight_parts)
        response = persona.format_response(insight)
        if len(response) <= self._max_chars:
            return response
        truncated = response[: self._max_chars - 1].rstrip()
        if len(truncated) < len(response):
            truncated = truncated.rstrip(".,;:!?")
            truncated += "…"
        return truncated

    def reply(self, request: CoachChatRequest) -> Dict[str, object]:
        persona = self._select_persona(request)
        try:
            self._apply_guardrails(request)
        except GuardrailViolation as err:
            return {"status": "error", "reason": err.reason}
        message = self._render_insight(persona, request)
        return {
            "status": "ok",
            "persona": persona.label,
            "reply": message,
            "approxTokens": request.estimated_tokens(),
        }
