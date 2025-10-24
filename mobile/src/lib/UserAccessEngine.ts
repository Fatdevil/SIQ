export type BillingStatus = {
  userId: string;
  tier: 'free' | 'pro' | 'elite';
  expiresAt?: string | null;
};

export const ENTITLEMENTS = {
  AI_PERSONAS: 'pro',
  ADVANCED_METRICS: 'pro',
  TEAM_DASHBOARD: 'elite'
} as const;

export async function fetchStatus(apiBase: string, userId: string): Promise<BillingStatus> {
  const response = await fetch(`${apiBase}/billing/status?userId=${encodeURIComponent(userId)}`);
  if (!response.ok) {
    throw new Error(`status ${response.status}`);
  }
  return response.json();
}

export function isFree(status: BillingStatus): boolean {
  return status.tier === 'free';
}

export function isPro(status: BillingStatus): boolean {
  return status.tier === 'pro' || status.tier === 'elite';
}

export function isElite(status: BillingStatus): boolean {
  return status.tier === 'elite';
}

export function canUse(feature: keyof typeof ENTITLEMENTS, status: BillingStatus): boolean {
  const requiredTier = ENTITLEMENTS[feature];
  if (requiredTier === 'elite') {
    return isElite(status);
  }
  if (requiredTier === 'pro') {
    return isPro(status);
  }
  return true;
}
