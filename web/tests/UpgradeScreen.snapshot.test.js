import test from 'node:test';
import assert from 'node:assert/strict';

import { renderUpgradeScreen } from './runtime/UpgradeScreen.js';

test('renders upgrade screen snapshot for free tier', () => {
  const snapshot = {
    userId: 'snapshot-user',
    tier: 'free',
    provider: null,
    expiresAt: null,
    entitlements: { free: true, pro: false, elite: false },
    features: { AI_PERSONAS: false, ADVANCED_METRICS: false, TEAM_DASHBOARD: false },
  };

  const html = renderUpgradeScreen({
    status: snapshot,
    receiptPlaceholder: 'PRO-LOCK',
    message: 'Unlock full match intelligence.',
  });

  const expected = `<section class="upgrade-screen">
  <header><h2>Activate SoccerIQ Pro</h2></header>
  <p class="upgrade-status">Current tier: FREE</p>
  <aside class="premium-overlay" role="dialog" aria-live="polite">
    <h3 class="premium-overlay__title">Unlock Pro access</h3>
    <p class="premium-overlay__copy">Upgrade to unlock precision analytics, AI coaching personas, and the full SoccerIQ toolkit.</p>
    <div class="upgrade-cta" data-track="upgrade_cta">
    <p class="upgrade-cta__copy">🔒 Ai Personas is a Pro feature.</p>
    <a href="/upgrade" class="upgrade-cta__link">Unlock with SoccerIQ Pro</a>
  </div>
  </aside>
  <p class="upgrade-message">Unlock full match intelligence.</p>
  <form><input placeholder="PRO-LOCK" /></form>
</section>`;

  assert.equal(html, expected);
});
