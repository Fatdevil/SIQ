export type BillingTier = 'free' | 'pro' | 'elite';

export const ENTITLEMENTS = {
  AI_PERSONAS: 'pro',
  ADVANCED_METRICS: 'pro',
  TEAM_DASHBOARD: 'elite',
} as const;

export type EntitlementKey = keyof typeof ENTITLEMENTS;
export type TierEntitlementKey = 'free' | 'pro' | 'elite';

export type EntitlementSnapshot = {
  userId: string;
  tier: BillingTier;
  provider: string | null;
  expiresAt: string | null;
  entitlements: Record<TierEntitlementKey, boolean>;
  features: Record<EntitlementKey, boolean>;
};

export type UserAccessState = {
  status: 'idle' | 'loading' | 'ready' | 'error';
  snapshot: EntitlementSnapshot;
  error: string | null;
  updatedAt: number | null;
};

export type UserAccessStore = {
  getState(): UserAccessState;
  subscribe(listener: (state: UserAccessState) => void): () => void;
  entitlement(key: TierEntitlementKey): boolean;
  canUse(feature: EntitlementKey): boolean;
  refresh(): Promise<void>;
};

const ORDER: Record<BillingTier, number> = { free: 0, pro: 1, elite: 2 };

function computeTierEntitlements(tier: BillingTier, existing?: Partial<Record<TierEntitlementKey, boolean>>): Record<TierEntitlementKey, boolean> {
  const resolved: Record<TierEntitlementKey, boolean> = {
    free: true,
    pro: false,
    elite: false,
  };

  if (existing?.pro !== undefined) {
    resolved.pro = existing.pro;
  } else {
    resolved.pro = ORDER[tier] >= ORDER['pro'];
  }

  if (existing?.elite !== undefined) {
    resolved.elite = existing.elite;
  } else {
    resolved.elite = ORDER[tier] >= ORDER['elite'];
  }

  return resolved;
}

function computeFeatureAccess(
  tiers: Record<TierEntitlementKey, boolean>,
  overrides?: Partial<Record<EntitlementKey, boolean>>,
): Record<EntitlementKey, boolean> {
  const result: Record<EntitlementKey, boolean> = {} as Record<EntitlementKey, boolean>;
  (Object.keys(ENTITLEMENTS) as EntitlementKey[]).forEach((feature) => {
    const required = ENTITLEMENTS[feature];
    let allowed: boolean;
    if (required === 'elite') {
      allowed = tiers.elite;
    } else if (required === 'pro') {
      allowed = tiers.pro;
    } else {
      allowed = true;
    }
    result[feature] = overrides?.[feature] ?? allowed;
  });
  return result;
}

function normaliseSnapshot(userId: string, payload: Partial<EntitlementSnapshot>): EntitlementSnapshot {
  const tier = (payload.tier ?? 'free') as BillingTier;
  const entitlements = computeTierEntitlements(tier, payload.entitlements);
  const features = computeFeatureAccess(entitlements, payload.features);
  return {
    userId: payload.userId ?? userId,
    tier,
    provider: payload.provider ?? null,
    expiresAt: payload.expiresAt ?? null,
    entitlements,
    features,
  };
}

export function createUserAccessStore(apiBase: string, userId: string, fetchImpl: typeof fetch = fetch): UserAccessStore {
  const listeners = new Set<(state: UserAccessState) => void>();
  let state: UserAccessState = {
    status: 'idle',
    snapshot: normaliseSnapshot(userId, {}),
    error: null,
    updatedAt: null,
  };

  function setState(partial: Partial<UserAccessState>): void {
    state = { ...state, ...partial };
    listeners.forEach((listener) => listener(state));
  }

  async function refresh(): Promise<void> {
    setState({ status: 'loading', error: null });
    try {
      const response = await fetchImpl(`${apiBase}/me/entitlements?userId=${encodeURIComponent(userId)}`);
      if (!response.ok) {
        throw new Error(`status ${response.status}`);
      }
      const payload = (await response.json()) as Partial<EntitlementSnapshot>;
      const snapshot = normaliseSnapshot(userId, payload);
      setState({
        status: 'ready',
        snapshot,
        error: null,
        updatedAt: Date.now(),
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'unknown error';
      setState({ status: 'error', error: message });
      throw error;
    }
  }

  return {
    getState() {
      return state;
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    entitlement(key) {
      return state.snapshot.entitlements[key];
    },
    canUse(feature) {
      return state.snapshot.features[feature];
    },
    refresh,
  };
}

export function entitlementAllows(tier: TierEntitlementKey, status: EntitlementSnapshot): boolean {
  return status.entitlements[tier];
}

export function canUseFeature(feature: EntitlementKey, status: EntitlementSnapshot): boolean {
  return status.features[feature];
}
