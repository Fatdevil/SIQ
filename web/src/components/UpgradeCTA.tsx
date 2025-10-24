type UpgradeCTAProps = {
  feature: string;
};

export default function UpgradeCTA({ feature }: UpgradeCTAProps) {
  return (
    <div className="rounded-xl bg-amber-100 p-3 text-sm">
      🔒 {feature} is a Pro feature.{' '}
      <a href="/upgrade" className="underline">
        Unlock with SoccerIQ Pro
      </a>
    </div>
  );
}
