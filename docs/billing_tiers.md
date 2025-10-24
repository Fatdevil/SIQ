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
