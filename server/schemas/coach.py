from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError, constr

__all__ = [
    "CoachChatBody",
    "CoachWeeklySummaryBody",
    "ValidationError",
]


class CoachChatBody(BaseModel):
    userId: constr(strip_whitespace=True, min_length=1)
    message: constr(strip_whitespace=True, min_length=1)
    persona: Optional[constr(strip_whitespace=True, min_length=1)] = None
    history: Optional[List[Dict[str, object]]] = None


class CoachWeeklySummaryBody(BaseModel):
    userId: constr(strip_whitespace=True, min_length=1)
    persona: Optional[constr(strip_whitespace=True, min_length=1)] = None
    lastN: int = Field(5, ge=1, le=50)
