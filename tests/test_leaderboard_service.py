from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from server import leaderboard


@pytest.fixture
def service() -> leaderboard.LeaderboardService:
    client = leaderboard.InMemoryRedis()
    client.flushall()
    return leaderboard.LeaderboardService(client)


@pytest.fixture
def client(service: leaderboard.LeaderboardService) -> TestClient:
    leaderboard.leaderboard_app.dependency_overrides[leaderboard.get_service] = lambda: service
    with TestClient(leaderboard.leaderboard_app) as test_client:
        yield test_client
    leaderboard.leaderboard_app.dependency_overrides.pop(leaderboard.get_service, None)


def test_hardest_shot_windows_sorted(service: leaderboard.LeaderboardService, client: TestClient) -> None:
    now = datetime.now(tz=timezone.utc)
    service.submit_hardest_shot(
        player_id="p1",
        ball_speed_kph=102.0,
        occurred_at=now.timestamp(),
        country="US",
        city="Austin",
    )
    service.submit_hardest_shot(
        player_id="p2",
        ball_speed_kph=111.0,
        occurred_at=(now - timedelta(hours=6)).timestamp(),
        country="US",
        city="Austin",
    )
    service.submit_hardest_shot(
        player_id="p3",
        ball_speed_kph=98.0,
        occurred_at=(now - timedelta(days=3)).timestamp(),
        country="US",
        city="Austin",
    )

    daily = client.get("/leaderboard/hardest-shot", params={"window": "24h", "scope": "global"})
    weekly = client.get("/leaderboard/hardest-shot", params={"window": "7d", "scope": "global"})

    assert daily.status_code == 200
    daily_scores = [entry["score"] for entry in daily.json()["entries"]]
    assert daily_scores == sorted(daily_scores, reverse=True)
    assert len(daily_scores) == 2

    assert weekly.status_code == 200
    weekly_scores = [entry["score"] for entry in weekly.json()["entries"]]
    assert weekly_scores[0] == pytest.approx(111.0)
    assert len(weekly_scores) == 3


def test_most_hits_scope_filters(service: leaderboard.LeaderboardService, client: TestClient) -> None:
    now = datetime.now(tz=timezone.utc)
    service.submit_most_hits(
        player_id="us1",
        hits=12,
        occurred_at=now.timestamp(),
        country="US",
        city="Austin",
    )
    service.submit_most_hits(
        player_id="us2",
        hits=9,
        occurred_at=now.timestamp(),
        country="US",
        city="Dallas",
    )
    service.submit_most_hits(
        player_id="ca1",
        hits=14,
        occurred_at=now.timestamp(),
        country="CA",
        city="Toronto",
    )

    response = client.get("/leaderboard/most-hits", params={"scope": "country", "country": "US"})
    assert response.status_code == 200
    players = [entry["player_id"] for entry in response.json()["entries"]]
    assert players == ["us1", "us2"]

    response_city = client.get(
        "/leaderboard/most-hits",
        params={"scope": "city", "country": "US", "city": "Austin"},
    )
    assert response_city.status_code == 200
    city_entries = response_city.json()["entries"]
    assert len(city_entries) == 1 and city_entries[0]["player_id"] == "us1"

    missing_country = client.get("/leaderboard/most-hits", params={"scope": "country"})
    assert missing_country.status_code == 400


def test_post_submission_endpoints(service: leaderboard.LeaderboardService, client: TestClient) -> None:
    payload = {
        "player_id": "abc",
        "ball_speed_kph": 120.5,
        "location": {"country": "es", "city": "madrid"},
    }
    resp = client.post("/leaderboard/hardest-shot", json=payload)
    assert resp.status_code == 200

    resp_hits = client.post(
        "/leaderboard/most-hits",
        json={"player_id": "abc", "hits": 4, "location": {"country": "es", "city": "madrid"}},
    )
    assert resp_hits.status_code == 200
