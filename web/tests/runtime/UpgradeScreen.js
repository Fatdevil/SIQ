function upgradeCTA(feature) {
  return [
    '<div class="upgrade-cta" data-track="upgrade_cta">',
    `  <p class="upgrade-cta__copy">🔒 ${feature} is a Pro feature.</p>`,
    '  <a href="/upgrade" class="upgrade-cta__link">Unlock with SoccerIQ Pro</a>',
    '</div>',
  ].join('\n');
}

function premiumOverlay({ status, feature, headline, description }) {
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
    `  ${upgradeCTA(prettyName)}`,
    '</aside>',
  ].join('\n');
}

export function renderUpgradeScreen({ status, receiptPlaceholder = 'PRO-123', message, error }) {
  const lines = [
    '<section class="upgrade-screen">',
    '  <header><h2>Activate SoccerIQ Pro</h2></header>',
    `  <p class="upgrade-status">Current tier: ${status.tier.toUpperCase()}</p>`,
  ];
  const overlay = premiumOverlay({ status, feature: 'AI_PERSONAS', headline: 'Unlock Pro access' });
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
