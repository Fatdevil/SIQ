export type UpgradeCTAProps = {
  feature: string;
};

export default function UpgradeCTA({ feature }: UpgradeCTAProps): string {
  return [
    '<div class="rounded-xl bg-amber-100 p-3 text-sm">',
    `  🔒 ${feature} is a Pro feature. `,
    '  <a href="/upgrade" class="underline">',
    '    Unlock with SoccerIQ Pro',
    '  </a>',
    '</div>',
  ].join('\n');
}
