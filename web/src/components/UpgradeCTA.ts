export type UpgradeCTAProps = {
  feature: string;
};

export default function UpgradeCTA({ feature }: UpgradeCTAProps): string {
  return [
    '<div class="upgrade-cta" data-track="upgrade_cta">',
    `  <p class="upgrade-cta__copy">🔒 ${feature} is a Pro feature.</p>`,
    '  <a href="/upgrade" class="upgrade-cta__link">Unlock with SoccerIQ Pro</a>',
    '</div>',
  ].join('\n');
}
