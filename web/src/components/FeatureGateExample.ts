import UpgradeCTA from './UpgradeCTA';
import { canUse, ENTITLEMENTS, EntitlementState } from '../lib/UserAccessEngine';

export type FeatureGateExampleProps = {
  entitlements: EntitlementState;
  feature: keyof typeof ENTITLEMENTS;
};

export function FeatureGateExample({ entitlements, feature }: FeatureGateExampleProps): string {
  const prettyName = feature
    .toLowerCase()
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
  if (canUse(feature, entitlements)) {
    return '<div class="rounded-xl border border-emerald-400 p-3">Feature unlocked!</div>';
  }
  return UpgradeCTA({ feature: prettyName });
}
