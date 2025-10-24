import { useBilling } from '@/hooks/useBilling';
import UpgradeCTA from '@/components/UpgradeCTA';

const PERSONAS = [
  { id: 'striker', name: 'Striker Savant', focus: 'Finishing + volley drills' },
  { id: 'maestro', name: 'Midfield Maestro', focus: 'First touch + tempo control' },
  { id: 'wall', name: 'Backline Wall', focus: 'Defensive shape + clearances' }
];

export default function CoachPersonas() {
  const { canUse } = useBilling();
  const unlocked = canUse('AI_PERSONAS');

  return (
    <section className="card" aria-labelledby="coach-personas-title">
      <div className="flex-row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 className="section-title" id="coach-personas-title">
          Coach personas
        </h2>
        <span className="badge">AI powered sessions</span>
      </div>
      <p className="text-muted" style={{ marginBottom: 20 }}>
        Tailor sessions to specialist coaches. Free tier includes one persona to get you started.
      </p>
      <div className="flex-row">
        {PERSONAS.map((persona, index) => {
          const locked = !unlocked && index > 0;
          return (
            <article key={persona.id} className={`persona-card${locked ? ' locked' : ''}`}>
              <h4>{persona.name}</h4>
              <p className="text-muted">{persona.focus}</p>
            </article>
          );
        })}
      </div>
      {!unlocked ? <UpgradeCTA feature="Coach personas" /> : null}
    </section>
  );
}
