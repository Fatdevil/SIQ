import UpgradeCTA from './UpgradeCTA';
import { EntitlementSnapshot, ENTITLEMENTS } from '../lib/UserAccessEngine';

export type PremiumOverlayProps = {
  status: EntitlementSnapshot;
  feature: keyof typeof ENTITLEMENTS;
  headline?: string;
  description?: string;
};

export default function PremiumOverlay({
  status,
  feature,
  headline,
  description,
}: PremiumOverlayProps): string {
  if (status.entitlements.pro) {
    return '';
  }

  const prettyName = feature
    .toLowerCase()
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');

  const heading = headline ?? `${prettyName} is locked`;
  const copy =
    description ??
    'Upgrade to unlock precision analytics, AI coaching personas, and the full SoccerIQ toolkit.';

  return [
    '<aside class="premium-overlay" role="dialog" aria-live="polite">',
    `  <h3 class="premium-overlay__title">${heading}</h3>`,
    `  <p class="premium-overlay__copy">${copy}</p>`,
    `  ${UpgradeCTA({ feature: prettyName })}`,
    '</aside>',
  ].join('\n');
}
