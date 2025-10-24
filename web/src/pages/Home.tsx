import CoachPersonas from '@/components/CoachPersonas';
import ARTargetPrecision from '@/components/ARTargetPrecision';
import { useBilling } from '@/hooks/useBilling';
import { useMemo } from 'react';

function formatTierLabel(tier: string | undefined) {
  switch (tier) {
    case 'elite':
      return 'Elite';
    case 'pro':
      return 'Pro';
    default:
      return 'Free';
  }
}

export default function Home() {
  const { status, loading, refresh, isElite, isPro } = useBilling();

  const pillClass = useMemo(() => {
    if (isElite) return 'status-pill elite';
    if (isPro) return 'status-pill pro';
    return 'status-pill';
  }, [isElite, isPro]);

  return (
    <div className="container">
      <header style={{ marginBottom: 32 }}>
        <h1 className="page-title">SoccerIQ Studio</h1>
        <p className="text-muted" style={{ maxWidth: 560 }}>
          Manage your training intelligence suite. Upgrade instantly with mock receipts while we integrate the final payment flow.
        </p>
      </header>

      <section className="card" style={{ marginBottom: 32 }}>
        <div className="flex-row" style={{ alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div className={pillClass}>
            Current tier: {formatTierLabel(status?.tier)}
          </div>
          <button className="button-primary" type="button" onClick={() => refresh()} disabled={loading}>
            {loading ? 'Refreshing…' : 'Refresh status'}
          </button>
        </div>
        <p className="text-muted" style={{ margin: 0 }}>
          Use receipts like <code>PRO-DEV</code> or <code>ELITE-TEST</code> in the upgrade flow to try higher tiers.
        </p>
      </section>

      <div className="grid" style={{ gap: 32 }}>
        <CoachPersonas />
        <ARTargetPrecision />
      </div>
    </div>
  );
}
