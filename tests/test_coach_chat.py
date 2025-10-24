from __future__ import annotations

import pytest

from siq.coach import CoachChatRequest, CoachResponder, PersonaPreferenceStore, PersonaRegistry


def test_persona_preference_store_tracks_last_choice() -> None:
    registry = PersonaRegistry()
    store = PersonaPreferenceStore(registry)
    responder = CoachResponder(preferences=store, registry=registry)

    # Initial default should be Pro
    default_profile = store.get_preference("user-1")
    assert default_profile.label == "Pro"

    request = CoachChatRequest.from_dict({"userId": "user-1", "message": "Need tempo help", "persona": "Street"})
    responder.reply(request)

    assert store.get_preference("user-1").label == "Street"


@pytest.mark.parametrize(
    "payload",
    [
        {"message": "hi"},
        {"userId": "", "message": "hi"},
        {"userId": "test"},
        {"userId": "test", "message": "", "history": ["not-a-dict"]},
    ],
)
def test_coach_chat_request_validation(payload) -> None:
    with pytest.raises(ValueError):
        CoachChatRequest.from_dict(payload)


def test_coach_chat_request_parses_history() -> None:
    payload = {
        "userId": "abc",
        "message": "Focus on rotation",
        "history": [
            {"role": "user", "content": "What should I fix?"},
            {"role": "assistant", "content": "Work on shoulder turn."},
        ],
    }
    request = CoachChatRequest.from_dict(payload)
    assert request.history[0].role == "user"
    assert request.history[1].content == "Work on shoulder turn."
