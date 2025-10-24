# SoccerIQ Billing Tiers

| Tier | Unlocks |
| ---- | ------- |
| Free | Core experience |
| Pro  | AI personas, advanced metrics |
| Elite | AI personas, advanced metrics, team dashboard |

## Mock verification in development

Use the mock billing endpoint to simulate upgrades when running the backend locally.

```bash
curl -X POST http://localhost:8000/billing/verify \
  -H "Content-Type: application/json" \
  -d '{"userId":"dev-user","platform":"ios","receipt":"PRO-XYZ"}'
```

Use a receipt beginning with `PRO-` to upgrade to Pro or `ELITE-` for Elite. Any other receipt leaves the user on Free.

The server persists billing state in the JSON file configured by the `BILLING_STORE_PATH` environment variable (defaults to `data/users.json`).

## How to use the Upgrade screen (dev/mock)

Both the web dashboard and Expo prototype ship with an **Upgrade** screen that hits the mock `/billing/verify` endpoint.

1. Launch the FastAPI server locally so `/billing/status` and `/billing/verify` are reachable (default: `http://localhost:8000`).
2. Open the web client (`npm install && npm run dev` in `web/`) or the Expo app.
3. Navigate to **Upgrade** using any Upgrade CTA in the UI, enter a mock receipt (e.g. `PRO-DEV` or `ELITE-QA`), pick the platform, and submit.
4. The client automatically refreshes billing status and unlocks gated features like Coach Personas and AR Target precision scoring.

Mock receipts beginning with `PRO-` unlock the Pro tier, and receipts starting with `ELITE-` unlock the Elite tier.
