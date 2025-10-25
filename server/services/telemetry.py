from __future__ import annotations

from typing import Any, Dict

try:  # pragma: no cover - optional telemetry integration
    from server.routes.ws_telemetry import publish_telemetry  # type: ignore
except Exception:  # pragma: no cover - telemetry optional in tests
    publish_telemetry = None


def emit(event: str, data: Dict[str, Any] | None = None) -> None:
    if publish_telemetry is None:
        return
    payload = {"timestampMs": 0, "event": event}
    if data:
        payload.update(data)
    try:
        publish_telemetry(payload)
    except Exception:
        pass
