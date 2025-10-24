"""Leaderboard service exposing FastAPI-style endpoints backed by sorted sets."""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

from fastapi import Depends, FastAPI, HTTPException, Query

WINDOWS = {
    "24h": 60 * 60 * 24,
    "7d": 60 * 60 * 24 * 7,
}

METRIC_HARDEST_SHOT = "hardest_shot"
METRIC_MOST_HITS = "most_hits"

SCOPE_GLOBAL = "global"
SCOPE_COUNTRY = "country"
SCOPE_CITY = "city"


class InMemoryRedis:
    """Tiny Redis-like store supporting the sorted-set ops we rely on."""

    def __init__(self) -> None:
        self._sorted_sets: Dict[str, Dict[str, float]] = {}
        self._strings: Dict[str, str] = {}

    def zadd(self, key: str, mapping: Dict[str, float]) -> None:
        store = self._sorted_sets.setdefault(key, {})
        for member, score in mapping.items():
            store[str(member)] = float(score)

    def zrangebyscore(self, key: str, min_score: float, max_score: float) -> List[bytes]:
        store = self._sorted_sets.get(key, {})
        return [member.encode() for member, score in store.items() if min_score <= score <= max_score]

    def zrevrange(self, key: str, start: int, stop: int) -> List[bytes]:
        items = sorted(self._sorted_sets.get(key, {}).items(), key=lambda item: item[1], reverse=True)
        if stop >= 0:
            slice_items = items[start : stop + 1]
        else:
            slice_items = items[start:]
        return [member.encode() for member, _ in slice_items]

    def zrem(self, key: str, member: bytes) -> None:
        member_str = member.decode() if isinstance(member, (bytes, bytearray)) else str(member)
        self._sorted_sets.get(key, {}).pop(member_str, None)

    def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> None:
        store = self._sorted_sets.get(key, {})
        for member, score in list(store.items()):
            if min_score <= score <= max_score:
                del store[member]

    def set(self, key: str, value: str) -> None:
        self._strings[key] = value

    def get(self, key: str) -> Optional[bytes]:
        value = self._strings.get(key)
        return value.encode() if value is not None else None

    def flushall(self) -> None:
        self._sorted_sets.clear()
        self._strings.clear()


@dataclass
class LeaderboardEvent:
    event_id: str
    player_id: str
    score: float
    occurred_at: float
    country: Optional[str]
    city: Optional[str]

    def serialize(self) -> str:
        payload = {
            "event_id": self.event_id,
            "player_id": self.player_id,
            "score": self.score,
            "occurred_at": self.occurred_at,
            "country": self.country,
            "city": self.city,
        }
        return json.dumps(payload)

    @classmethod
    def deserialize(cls, payload: str) -> "LeaderboardEvent":
        data = json.loads(payload)
        return cls(
            event_id=data["event_id"],
            player_id=data["player_id"],
            score=float(data["score"]),
            occurred_at=float(data["occurred_at"]),
            country=data.get("country"),
            city=data.get("city"),
        )


class LeaderboardService:
    def __init__(self, client: InMemoryRedis) -> None:
        self._client = client

    def _score_key(self, metric: str, window: str, scope: str, location: Tuple[Optional[str], Optional[str]]) -> str:
        country, city = location
        suffix = "global"
        if scope == SCOPE_COUNTRY:
            if not country:
                raise ValueError("country scope requires country code")
            suffix = f"country:{country.upper()}"
        elif scope == SCOPE_CITY:
            if not (country and city):
                raise ValueError("city scope requires country and city")
            suffix = f"city:{country.upper()}:{city.lower()}"
        return f"leaderboard:{metric}:{window}:{suffix}"

    def _timestamp_key(self, score_key: str) -> str:
        return f"{score_key}:timestamps"

    def _prune(self, score_key: str, window_seconds: int) -> None:
        now = time.time()
        timestamp_key = self._timestamp_key(score_key)
        cutoff = now - window_seconds
        expired_ids = self._client.zrangebyscore(timestamp_key, 0, cutoff)
        for event_id in expired_ids:
            self._client.zrem(score_key, event_id)
        self._client.zremrangebyscore(timestamp_key, 0, cutoff)

    def _store_event(self, event: LeaderboardEvent) -> None:
        self._client.set(f"leaderboard:event:{event.event_id}", event.serialize())

    def _record(
        self,
        metric: str,
        window: str,
        scope: str,
        location: Tuple[Optional[str], Optional[str]],
        event: LeaderboardEvent,
        window_seconds: int,
    ) -> None:
        score_key = self._score_key(metric, window, scope, location)
        self._prune(score_key, window_seconds)
        self._store_event(event)
        self._client.zadd(score_key, {event.event_id: event.score})
        self._client.zadd(self._timestamp_key(score_key), {event.event_id: event.occurred_at})

    def submit_hardest_shot(
        self,
        *,
        player_id: str,
        ball_speed_kph: float,
        occurred_at: float,
        country: Optional[str],
        city: Optional[str],
    ) -> None:
        event_id = uuid.uuid4().hex
        event = LeaderboardEvent(
            event_id=event_id,
            player_id=player_id,
            score=ball_speed_kph,
            occurred_at=occurred_at,
            country=country,
            city=city,
        )
        for window in ("24h", "7d"):
            self._record(METRIC_HARDEST_SHOT, window, SCOPE_GLOBAL, (country, city), event, WINDOWS[window])
            if country:
                self._record(METRIC_HARDEST_SHOT, window, SCOPE_COUNTRY, (country, city), event, WINDOWS[window])
            if country and city:
                self._record(METRIC_HARDEST_SHOT, window, SCOPE_CITY, (country, city), event, WINDOWS[window])

    def submit_most_hits(
        self,
        *,
        player_id: str,
        hits: int,
        occurred_at: float,
        country: Optional[str],
        city: Optional[str],
    ) -> None:
        event_id = uuid.uuid4().hex
        event = LeaderboardEvent(
            event_id=event_id,
            player_id=player_id,
            score=float(hits),
            occurred_at=occurred_at,
            country=country,
            city=city,
        )
        window = "7d"
        self._record(METRIC_MOST_HITS, window, SCOPE_GLOBAL, (country, city), event, WINDOWS[window])
        if country:
            self._record(METRIC_MOST_HITS, window, SCOPE_COUNTRY, (country, city), event, WINDOWS[window])
        if country and city:
            self._record(METRIC_MOST_HITS, window, SCOPE_CITY, (country, city), event, WINDOWS[window])

    def _collect_events(self, event_ids: Iterable[bytes]) -> List[LeaderboardEvent]:
        events: List[LeaderboardEvent] = []
        for event_id in event_ids:
            payload = self._client.get(f"leaderboard:event:{event_id.decode()}")
            if not payload:
                continue
            events.append(LeaderboardEvent.deserialize(payload.decode()))
        return events

    def read_leaderboard(
        self,
        *,
        metric: str,
        window: str,
        scope: str,
        country: Optional[str],
        city: Optional[str],
        limit: int = 10,
    ) -> List[LeaderboardEvent]:
        window_seconds = WINDOWS.get(window)
        if window_seconds is None:
            raise ValueError(f"Unsupported window {window}")
        score_key = self._score_key(metric, window, scope, (country, city))
        self._prune(score_key, window_seconds)
        event_ids = self._client.zrevrange(score_key, 0, limit - 1)
        return self._collect_events(event_ids)


def _normalize_country(value: Optional[str]) -> Optional[str]:
    return value.upper() if isinstance(value, str) and value else None


def _normalize_city(value: Optional[str]) -> Optional[str]:
    return value.title() if isinstance(value, str) and value else None


def _parse_timestamp(raw: Optional[object]) -> Optional[float]:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw).timestamp()
        except ValueError as exc:  # pragma: no cover - validation guard
            raise HTTPException(status_code=400, detail="invalid timestamp") from exc
    raise HTTPException(status_code=400, detail="invalid timestamp")


def _parse_location(payload: Optional[Dict[str, object]]) -> Tuple[Optional[str], Optional[str]]:
    if not isinstance(payload, dict):
        return None, None
    country = _normalize_country(payload.get("country"))
    city = _normalize_city(payload.get("city"))
    return country, city


def _service_factory() -> LeaderboardService:
    return LeaderboardService(InMemoryRedis())


leaderboard_app = FastAPI(title="SIQ Leaderboards")


def get_service() -> LeaderboardService:
    return _service_factory()


def _format_entries(events: List[LeaderboardEvent]) -> List[Dict[str, object]]:
    formatted: List[Dict[str, object]] = []
    for idx, event in enumerate(events, start=1):
        formatted.append(
            {
                "player_id": event.player_id,
                "score": event.score,
                "occurred_at": datetime.fromtimestamp(event.occurred_at).isoformat(),
                "country": event.country,
                "city": event.city,
                "rank": idx,
            }
        )
    return formatted


@leaderboard_app.post("/leaderboard/hardest-shot")
def post_hardest_shot(
    payload: Dict[str, object],
    service: LeaderboardService = Depends(get_service),
) -> Dict[str, str]:
    player_id = str(payload.get("player_id")) if payload.get("player_id") else None
    ball_speed = payload.get("ball_speed_kph")
    if not player_id or ball_speed is None:
        raise HTTPException(status_code=400, detail="player_id and ball_speed_kph are required")
    occurred_at = _parse_timestamp(payload.get("occurred_at")) or time.time()
    country, city = _parse_location(payload.get("location"))
    service.submit_hardest_shot(
        player_id=player_id,
        ball_speed_kph=float(ball_speed),
        occurred_at=occurred_at,
        country=country,
        city=city,
    )
    return {"status": "accepted"}


@leaderboard_app.post("/leaderboard/most-hits")
def post_most_hits(
    payload: Dict[str, object],
    service: LeaderboardService = Depends(get_service),
) -> Dict[str, str]:
    player_id = str(payload.get("player_id")) if payload.get("player_id") else None
    hits = payload.get("hits")
    if not player_id or hits is None:
        raise HTTPException(status_code=400, detail="player_id and hits are required")
    occurred_at = _parse_timestamp(payload.get("occurred_at")) or time.time()
    country, city = _parse_location(payload.get("location"))
    service.submit_most_hits(
        player_id=player_id,
        hits=int(hits),
        occurred_at=occurred_at,
        country=country,
        city=city,
    )
    return {"status": "accepted"}


def _validate_scope(scope: str, country: Optional[str], city: Optional[str]) -> None:
    if scope == SCOPE_COUNTRY and not country:
        raise HTTPException(status_code=400, detail="country scope requires country code")
    if scope == SCOPE_CITY and not (country and city):
        raise HTTPException(status_code=400, detail="city scope requires country and city")


@leaderboard_app.get("/leaderboard/hardest-shot")
def get_hardest_shot(
    window: str = Query("24h", enum=("24h", "7d")),
    scope: str = Query("global", enum=(SCOPE_GLOBAL, SCOPE_COUNTRY, SCOPE_CITY)),
    country: Optional[str] = None,
    city: Optional[str] = None,
    service: LeaderboardService = Depends(get_service),
) -> Dict[str, object]:
    _validate_scope(scope, country, city)
    events = service.read_leaderboard(
        metric=METRIC_HARDEST_SHOT,
        window=window,
        scope=scope,
        country=_normalize_country(country),
        city=_normalize_city(city),
    )
    return {
        "entries": _format_entries(events),
        "window": window,
        "metric": METRIC_HARDEST_SHOT,
        "scope": scope,
    }


@leaderboard_app.get("/leaderboard/most-hits")
def get_most_hits(
    scope: str = Query("global", enum=(SCOPE_GLOBAL, SCOPE_COUNTRY, SCOPE_CITY)),
    country: Optional[str] = None,
    city: Optional[str] = None,
    service: LeaderboardService = Depends(get_service),
) -> Dict[str, object]:
    _validate_scope(scope, country, city)
    events = service.read_leaderboard(
        metric=METRIC_MOST_HITS,
        window="7d",
        scope=scope,
        country=_normalize_country(country),
        city=_normalize_city(city),
    )
    return {
        "entries": _format_entries(events),
        "window": "7d",
        "metric": METRIC_MOST_HITS,
        "scope": scope,
    }
