from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class PersonaProfile:
    """Description for a coach persona."""

    key: str
    label: str
    intro: str
    closing: str

    def format_response(self, insight: str) -> str:
        """Wrap generated insight with persona tone."""

        body = f"{self.intro} {insight.strip()} {self.closing}".strip()
        # Ensure spacing without doubling spaces.
        return " ".join(body.split())


class PersonaRegistry:
    """Register available personas and resolve aliases."""

    def __init__(self) -> None:
        self._profiles: Dict[str, PersonaProfile] = {
            "pro": PersonaProfile(
                key="pro",
                label="Pro",
                intro="Tour-pro precision coming your way:",
                closing="Stay smooth and trust your numbers.",
            ),
            "street": PersonaProfile(
                key="street",
                label="Street",
                intro="Street-smart breakdown:",
                closing="Keep the grind tight and the tempo tighter.",
            ),
            "worldcup": PersonaProfile(
                key="worldcup",
                label="WorldCup",
                intro="World Cup energy check:",
                closing="Play it with global flair and fearless rhythm.",
            ),
        }

    @property
    def profiles(self) -> Dict[str, PersonaProfile]:
        return dict(self._profiles)

    def resolve(self, name: str | None) -> PersonaProfile:
        if not name:
            return self._profiles["pro"]
        key = name.lower()
        if key not in self._profiles:
            raise ValueError(f"Unknown persona: {name}")
        return self._profiles[key]


class PersonaPreferenceStore:
    """Remember a user's preferred persona."""

    def __init__(self, registry: PersonaRegistry | None = None) -> None:
        self._registry = registry or PersonaRegistry()
        self._preferences: Dict[str, str] = {}

    def set_preference(self, user_id: str, persona_name: str) -> PersonaProfile:
        profile = self._registry.resolve(persona_name)
        self._preferences[user_id] = profile.key
        return profile

    def get_preference(self, user_id: str) -> PersonaProfile:
        key = self._preferences.get(user_id, "pro")
        return self._registry.resolve(key)

    def clear(self) -> None:
        self._preferences.clear()
