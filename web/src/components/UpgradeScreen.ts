import PremiumOverlay from './PremiumOverlay';
import type { EntitlementSnapshot } from '../lib/UserAccessEngine';

export type UpgradeScreenProps = {
  status: EntitlementSnapshot;
  receiptPlaceholder?: string;
  message?: string;
  error?: string;
};

export default function renderUpgradeScreen({
  status,
  receiptPlaceholder = 'PRO-123',
  message,
  error,
}: UpgradeScreenProps): string {
  const lines: string[] = [
    '<section class="upgrade-screen">',
    '  <header><h2>Activate SoccerIQ Pro</h2></header>',
    `  <p class="upgrade-status">Current tier: ${status.tier.toUpperCase()}</p>`,
  ];

  const overlay = PremiumOverlay({ status, feature: 'AI_PERSONAS', headline: 'Unlock Pro access' });
  if (overlay) {
    overlay.split('\n').forEach((line) => {
      lines.push(`  ${line}`);
    });
  }

  if (error) {
    lines.push(`  <p class="upgrade-error">${error}</p>`);
  }
  if (message) {
    lines.push(`  <p class="upgrade-message">${message}</p>`);
  }

  lines.push(`  <form><input placeholder="${receiptPlaceholder}" /></form>`);
  lines.push('</section>');
  return lines.join('\n');
}
