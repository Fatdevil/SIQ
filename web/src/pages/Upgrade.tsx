import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBilling } from '@/hooks/useBilling';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const PLATFORMS = [
  { id: 'web-mock', label: 'Web mock' },
  { id: 'ios', label: 'iOS (StoreKit mock)' },
  { id: 'android', label: 'Android (Play Billing mock)' }
];

export default function Upgrade() {
  const navigate = useNavigate();
  const { userId, refresh } = useBilling();
  const [receipt, setReceipt] = useState('');
  const [platform, setPlatform] = useState('web-mock');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!receipt.trim()) {
      setError('Enter a mock receipt (example: PRO-DEV or ELITE-QA).');
      return;
    }
    setSubmitting(true);
    setError(null);
    setSuccess(false);

    try {
      const response = await fetch(`${API_BASE}/billing/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId, platform, receipt: receipt.trim() })
      });

      if (!response.ok) {
        throw new Error(`Verify failed (${response.status})`);
      }

      await refresh();
      setSuccess(true);
      setReceipt('');
      setTimeout(() => navigate('/'), 600);
    } catch (verifyError) {
      console.error(verifyError);
      setError('Could not verify the mock receipt. Double-check the value (PRO-* or ELITE-*).');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="container">
      <header style={{ marginBottom: 24 }}>
        <h1 className="page-title">Activate SoccerIQ Pro</h1>
        <p className="text-muted" style={{ maxWidth: 520 }}>
          Use mock receipts to flip billing tiers instantly while we finish the real checkout flow.
        </p>
      </header>

      <section className="card" style={{ maxWidth: 560 }}>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="receipt">Mock receipt</label>
            <input
              id="receipt"
              name="receipt"
              placeholder="PRO-DEV"
              value={receipt}
              onChange={(event) => setReceipt(event.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Platform</label>
            <div className="flex-row">
              {PLATFORMS.map((item) => (
                <label key={item.id} style={{ display: 'flex', gap: 8, alignItems: 'center', cursor: 'pointer' }}>
                  <input
                    type="radio"
                    name="platform"
                    value={item.id}
                    checked={platform === item.id}
                    onChange={() => setPlatform(item.id)}
                    style={{ width: 'auto' }}
                  />
                  {item.label}
                </label>
              ))}
            </div>
          </div>

          <button className="button-primary" type="submit" disabled={submitting}>
            {submitting ? 'Activating…' : 'Activate Pro'}
          </button>
        </form>

        <div style={{ marginTop: 24 }}>
          <p className="text-muted" style={{ marginBottom: 4 }}>
            Mock rules:
          </p>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            <li>Receipts starting with <code>PRO-</code> unlock the Pro tier.</li>
            <li>Receipts starting with <code>ELITE-</code> unlock the Elite tier.</li>
          </ul>
        </div>

        {error ? (
          <div className="alert error" role="alert" style={{ marginTop: 24 }}>
            {error}
          </div>
        ) : null}

        {success ? (
          <div className="alert" role="status" style={{ marginTop: 24 }}>
            ✅ Tier updated! Redirecting back to the dashboard…
          </div>
        ) : null}
      </section>
    </div>
  );
}
