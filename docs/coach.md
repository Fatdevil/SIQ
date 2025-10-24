# Coach Personas & Chat

Coach v1.2 introduces persona-aware chat guidance plus a weekly performance summary job.

## Personas

Available personas are:

- **Pro** – Tour-caliber, data-forward breakdowns.
- **Street** – Conversational, motivational tone.
- **WorldCup** – High-energy, global hype.

A user's last selected persona is remembered automatically.

## Chat Endpoint

```
POST /coach/chat
Content-Type: application/json
```

Example request:

```json
{
  "userId": "player-7",
  "persona": "WorldCup",
  "message": "Dial in my wedge distance control",
  "history": [
    {"role": "user", "content": "Missed greens right all week"},
    {"role": "assistant", "content": "Work on club path"}
  ]
}
```

Sample response:

```json
{
  "status": "ok",
  "persona": "WorldCup",
  "reply": "World Cup energy check: Dial in my wedge distance control Recent context: Missed greens right all week Work on club path. Play it with global flair and fearless rhythm.",
  "approxTokens": 19
}
```

Responses are capped at 600 characters. Requests are guarded by a sliding window rate limit and an hourly token budget.

## Weekly Summary Job

Use the job to roll up the last *N* recorded runs into a concise summary:

```python
from datetime import datetime

from siq.coach import RunHistory, RunRecord, WeeklySummaryJob

history = RunHistory(max_runs=20)
job = WeeklySummaryJob(history)

history.add_run(
    "player-7",
    RunRecord(ball_speed_mps=62.4, club_speed_mps=43.1, carry_m=145.0, captured_at=datetime.utcnow()),
)
summary = job.summarize("player-7", persona_name="street", last_n=5)
```

The returned paragraph mirrors the selected persona tone and remains under 600 characters, making it safe to surface in UI widgets or outbound emails.
