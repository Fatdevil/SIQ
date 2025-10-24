import { BillingStatus, canUse, ENTITLEMENTS } from './UserAccessEngine';

describe('UserAccessEngine.canUse', () => {
  const base: BillingStatus = { userId: 'user', tier: 'free' };

  it('locks pro features for free users', () => {
    expect(canUse('AI_PERSONAS', base)).toBe(false);
  });

  it('unlocks pro features when tier is pro', () => {
    const pro: BillingStatus = { ...base, tier: 'pro' };
    expect(canUse('AI_PERSONAS', pro)).toBe(true);
    expect(canUse('ADVANCED_METRICS', pro)).toBe(true);
    expect(canUse('TEAM_DASHBOARD', pro)).toBe(false);
  });

  it('unlocks everything for elite tier', () => {
    const elite: BillingStatus = { ...base, tier: 'elite' };
    (Object.keys(ENTITLEMENTS) as Array<keyof typeof ENTITLEMENTS>).forEach((feature) => {
      expect(canUse(feature, elite)).toBe(true);
    });
  });
});
