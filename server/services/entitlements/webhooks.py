from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Mapping

_DEFAULT_PATH = Path(os.environ.get("WEBHOOK_EVENTS_STORE_PATH", "data/webhook_events.json"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _load_raw(path: Path) -> Dict[str, Dict[str, Dict[str, str]]]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            if isinstance(data, dict):
                normalized: Dict[str, Dict[str, Dict[str, str]]] = {}
                for provider, entries in data.items():
                    if not isinstance(entries, dict):
                        continue
                    normalized[str(provider)] = {
                        str(event_id): item
                        for event_id, item in entries.items()
                        if isinstance(item, dict)
                    }
                return normalized
    except json.JSONDecodeError:
        return {}
    return {}


def _save_raw(payload: Mapping[str, Dict[str, Dict[str, str]]], path: Path) -> None:
    _ensure_parent(path)
    fd, tmp_name = tempfile.mkstemp(prefix="webhook_events_", suffix=".json", dir=str(path.parent))
    os.close(fd)
    tmp_path = Path(tmp_name)
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


@dataclass(frozen=True, slots=True)
class WebhookEventRecord:
    provider: str
    event_id: str
    status: str
    processed_at: str


class WebhookEventStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _DEFAULT_PATH

    @property
    def path(self) -> Path:
        return self._path

    def is_duplicate(self, provider: str, event_id: str) -> bool:
        raw = _load_raw(self._path)
        provider_events = raw.get(provider, {})
        return event_id in provider_events

    def record(self, provider: str, event_id: str, status: str) -> WebhookEventRecord:
        raw = _load_raw(self._path)
        provider_events = raw.setdefault(provider, {})
        record = {
            "status": status,
            "processedAt": _now_iso(),
        }
        provider_events[event_id] = record
        _save_raw(raw, self._path)
        return WebhookEventRecord(
            provider=provider,
            event_id=event_id,
            status=status,
            processed_at=record["processedAt"],
        )


__all__ = ["WebhookEventRecord", "WebhookEventStore"]
