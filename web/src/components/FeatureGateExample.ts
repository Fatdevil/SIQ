import UpgradeCTA from './UpgradeCTA';
import PremiumOverlay from './PremiumOverlay';
import { EntitlementSnapshot, canUseFeature, ENTITLEMENTS } from '../lib/UserAccessEngine';

export type FeatureGateExampleProps = {
  status: EntitlementSnapshot;
  feature: keyof typeof ENTITLEMENTS;
};

export function FeatureGateExample({ status, feature }: FeatureGateExampleProps): string {
  const prettyName = feature
    .toLowerCase()
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
  if (canUseFeature(feature, status)) {
    return '<div class="rounded-xl border border-emerald-400 p-3">Feature unlocked!</div>';
  }
  return [
    '<div class="relative rounded-xl border border-amber-400 p-3">',
    '  <div class="blur-sm">',
    '    Feature locked until you upgrade.',
    '  </div>',
    `  ${PremiumOverlay({ status, feature, headline: `${prettyName} requires Pro` })}`,
    '</div>',
  ].join('\n');
}
