const ENTITLEMENTS = {
  AI_PERSONAS: 'pro',
  ADVANCED_METRICS: 'pro',
  TEAM_DASHBOARD: 'elite',
};

const PRODUCTS = {
  PRO: 'pro',
  ELITE: 'elite',
};

function resolveFetch(options) {
  if (options.fetch) {
    return options.fetch;
  }
  const globalFetch = globalThis.fetch;
  if (!globalFetch) {
    throw new Error('fetch implementation required');
  }
  return globalFetch.bind(globalThis);
}

function normalizeBase(base) {
  if (!base) {
    return '';
  }
  return base.endsWith('/') ? base.slice(0, -1) : base;
}

function toMap(records) {
  return records.reduce((acc, record) => {
    if (record && record.productId) {
      acc[record.productId] = record;
    }
    return acc;
  }, {});
}

class UserAccessEngine {
  constructor(options) {
    this.apiBase = normalizeBase(options.apiBase);
    this.userId = options.userId;
    this.fetcher = resolveFetch(options);
    this.focusTarget = options.focusTarget ?? (typeof window !== 'undefined' ? window : null);
    this.state = {
      status: 'idle',
      entitlements: {},
      error: null,
      lastFetchedAt: null,
    };
    this.listeners = new Set();
    this.inFlight = null;
    this.focusHandler = null;
  }

  getState() {
    return this.state;
  }

  subscribe(listener) {
    this.listeners.add(listener);
    listener(this.state);
    return () => {
      this.listeners.delete(listener);
    };
  }

  start() {
    if (this.focusTarget && !this.focusHandler) {
      this.focusHandler = () => {
        void this.refresh();
      };
      try {
        this.focusTarget.addEventListener('focus', this.focusHandler);
      } catch {
        // ignore
      }
    }
    return this.refresh();
  }

  stop() {
    if (this.focusTarget && this.focusHandler) {
      try {
        this.focusTarget.removeEventListener('focus', this.focusHandler);
      } catch {
        // ignore
      }
    }
    this.focusHandler = null;
  }

  refresh() {
    if (this.inFlight) {
      return this.inFlight;
    }
    const nextStatus = this.state.status === 'ready' ? 'refreshing' : 'loading';
    this.setState({ status: nextStatus, error: null });
    const url = `${this.apiBase}/me/entitlements`;
    const request = {
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'X-User-Id': this.userId,
      },
    };

    this.inFlight = this.fetcher(url, request)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`status ${response.status}`);
        }
        const body = await response.json();
        const records = Array.isArray(body?.entitlements) ? body.entitlements : [];
        this.setState({
          status: 'ready',
          entitlements: toMap(records),
          error: null,
          lastFetchedAt: Date.now(),
        });
      })
      .catch((error) => {
        const message = error instanceof Error ? error.message : String(error);
        this.setState({
          status: 'error',
          error: message,
        });
      })
      .finally(() => {
        this.inFlight = null;
      });

    return this.inFlight;
  }

  entitlement(productId) {
    return this.state.entitlements[productId];
  }

  hasEntitlement(productId) {
    const ent = this.entitlement(productId);
    return ent ? ent.status === 'active' : false;
  }

  hasPro() {
    return this.hasEntitlement(PRODUCTS.PRO) || this.hasEntitlement(PRODUCTS.ELITE);
  }

  hasElite() {
    return this.hasEntitlement(PRODUCTS.ELITE);
  }

  setState(patch) {
    this.state = { ...this.state, ...patch };
    for (const listener of this.listeners) {
      listener(this.state);
    }
  }
}

function canUse(feature, stateOrEngine) {
  const required = ENTITLEMENTS[feature];
  const state = stateOrEngine instanceof UserAccessEngine ? stateOrEngine.getState() : stateOrEngine;
  if (required === PRODUCTS.ELITE) {
    return Boolean(state.entitlements[PRODUCTS.ELITE]?.status === 'active');
  }
  if (required === PRODUCTS.PRO) {
    const proActive = state.entitlements[PRODUCTS.PRO]?.status === 'active';
    const eliteActive = state.entitlements[PRODUCTS.ELITE]?.status === 'active';
    return Boolean(proActive || eliteActive);
  }
  return true;
}

function tierFromState(state) {
  if (state.entitlements[PRODUCTS.ELITE]?.status === 'active') {
    return 'elite';
  }
  if (state.entitlements[PRODUCTS.PRO]?.status === 'active') {
    return 'pro';
  }
  return 'free';
}

export { UserAccessEngine, canUse, ENTITLEMENTS, PRODUCTS, tierFromState };
