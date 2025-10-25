export type UpgradeScreenState = {
  tier: 'free' | 'pro' | 'elite';
  submitting?: boolean;
  message?: string;
  error?: string;
};

export function renderUpgradeScreen(state: UpgradeScreenState): string {
  const submitting = Boolean(state.submitting);
  const status = state.tier.toUpperCase();
  const buttonLabel = submitting ? 'Redirecting…' : 'Upgrade with Stripe Checkout';
  const restore = '<button class="restore-button">Restore purchases</button>';
  const error = state.error ? `  <p class="upgrade-error">${state.error}</p>` : '';
  const message = state.message ? `  <p class="upgrade-success">${state.message}</p>` : '';
  return [
    '<section class="upgrade-section">',
    '  <h2>Activate SoccerIQ Pro</h2>',
    '  <p class="upgrade-copy">Checkout is powered by Stripe for the web and the App/Play Store on mobile. Complete payment to unlock Pro instantly.</p>',
    `  <p class="upgrade-status">Current tier: <strong>${status}</strong></p>`,
    '  <ul class="upgrade-benefits">',
    '    <li>Unlimited coach personas</li>',
    '    <li>AR target precision scoring</li>',
    '    <li>Priority match insights</li>',
    '  </ul>',
    `  <button class="upgrade-primary"${submitting ? ' disabled' : ''}>${buttonLabel}</button>`,
    `  ${restore}`,
    error,
    message,
    '</section>',
  ]
    .filter((line) => line !== '')
    .join('\n');
}
