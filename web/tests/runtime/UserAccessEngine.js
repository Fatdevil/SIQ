export const ENTITLEMENTS = {
  AI_PERSONAS: 'pro',
  ADVANCED_METRICS: 'pro',
  TEAM_DASHBOARD: 'elite',
};

const ORDER = { free: 0, pro: 1, elite: 2 };

function computeTierEntitlements(tier, existing = {}) {
  return {
    free: true,
    pro: existing.pro ?? ORDER[tier] >= ORDER.pro,
    elite: existing.elite ?? ORDER[tier] >= ORDER.elite,
  };
}

function computeFeatureAccess(tiers, overrides = {}) {
  return Object.fromEntries(
    Object.keys(ENTITLEMENTS).map((feature) => {
      const required = ENTITLEMENTS[feature];
      const allowed =
        required === 'elite'
          ? tiers.elite
          : required === 'pro'
          ? tiers.pro
          : true;
      return [feature, overrides[feature] ?? allowed];
    }),
  );
}

export function normaliseSnapshot(userId, payload = {}) {
  const tier = payload.tier ?? 'free';
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

export function createUserAccessStore(apiBase, userId, fetchImpl = fetch) {
  const listeners = new Set();
  let state = {
    status: 'idle',
    snapshot: normaliseSnapshot(userId),
    error: null,
    updatedAt: null,
  };

  function setState(partial) {
    state = { ...state, ...partial };
    listeners.forEach((listener) => listener(state));
  }

  async function refresh() {
    setState({ status: 'loading', error: null });
    try {
      const response = await fetchImpl(
        `${apiBase}/me/entitlements?userId=${encodeURIComponent(userId)}`,
      );
      if (!response.ok) {
        throw new Error(`status ${response.status}`);
      }
      const payload = await response.json();
      const snapshot = normaliseSnapshot(userId, payload);
      setState({ status: 'ready', snapshot, updatedAt: Date.now(), error: null });
    } catch (error) {
      setState({ status: 'error', error: error.message || String(error) });
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
