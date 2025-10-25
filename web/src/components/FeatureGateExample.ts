import UpgradeCTA from './UpgradeCTA';
import { BillingStatus, canUse, ENTITLEMENTS } from '../lib/UserAccessEngine';

export type FeatureGateExampleProps = {
  status: BillingStatus;
  feature: keyof typeof ENTITLEMENTS;
};

export function FeatureGateExample({ status, feature }: FeatureGateExampleProps): string {
  const prettyName = feature
    .toLowerCase()
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
  if (canUse(feature, status)) {
    return '<div class="rounded-xl border border-emerald-400 p-3">Feature unlocked!</div>';
  }
  return UpgradeCTA({ feature: prettyName });
}
