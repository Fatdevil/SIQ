import UpgradeCTA from '@/components/UpgradeCTA';
import { useBilling } from '@/hooks/useBilling';

export default function ARTargetPrecision() {
  const { canUse } = useBilling();
  const unlocked = canUse('ADVANCED_METRICS');

  return (
    <section className="card" aria-labelledby="ar-target-title">
      <div className="flex-row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 className="section-title" id="ar-target-title">
          AR Target precision scoring
        </h2>
        <span className="badge">AR + computer vision</span>
      </div>
      <p className="text-muted" style={{ marginBottom: 20 }}>
        Score every shot against a smart AR overlay that adapts drills to your pace.
      </p>
      {unlocked ? (
        <div>
          <p style={{ fontWeight: 600, marginBottom: 12 }}>Session insights</p>
          <ul style={{ paddingLeft: 20, margin: 0, color: '#0f172a' }}>
            <li>Precision: 87% of shots inside target zones</li>
            <li>Adaptive difficulty suggests 3 new drills for tomorrow</li>
            <li>Elite bonus: compare against academy leaderboard</li>
          </ul>
        </div>
      ) : (
        <UpgradeCTA feature="AR Target precision scoring" />
      )}
    </section>
  );
}
