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

## How to test the Upgrade screen (mock)

1. Start the FastAPI server locally so `/billing/status` and `/billing/verify` are reachable from the web client or Expo app.
2. Open the web client (`web/index.html`) and switch to the **Upgrade** tab, or navigate to the **Upgrade** screen from the mobile app home.
3. Enter a mock receipt:
   - `PRO-*` values unlock the Pro tier.
   - `ELITE-*` values unlock the Elite tier.
4. Submit the form. The client calls `POST /billing/verify` with the active `userId` and then refreshes `GET /billing/status` to update gates immediately.
5. Return to the home view—coach personas unlock and AR Target Precision is no longer gated for upgraded tiers.

Receipts and tiers are cached on the client after a successful verification so gates stay open until the mock store resets.
