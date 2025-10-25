#!/usr/bin/env node
import assert from 'node:assert/strict';
import {
  UserAccessEngine,
  canUse,
  ENTITLEMENTS,
  PRODUCTS,
  tierFromState,
} from './runtime/UserAccessEngine.js';

const scenario = process.argv[2] ?? 'success';

const calls = [];
const focusTarget = {
  _listeners: [],
  addEventListener(type, handler) {
    if (type === 'focus') {
      this._listeners.push(handler);
    }
  },
  removeEventListener(type, handler) {
    this._listeners = this._listeners.filter((fn) => fn !== handler);
  },
  fire() {
    for (const handler of [...this._listeners]) {
      handler();
    }
  },
};

if (scenario === 'success') {
  const fetchMock = async (input, init) => {
    calls.push({ input: String(input), headers: init?.headers || {} });
    return {
      ok: true,
      status: 200,
      json: async () => ({
        entitlements: [
          {
            productId: 'pro',
            status: 'active',
            source: 'mock',
            createdAt: '2024-01-01T00:00:00Z',
          },
        ],
      }),
    };
  };
  const engine = new UserAccessEngine({
    apiBase: 'https://api.test',
    userId: 'tester',
    fetch: fetchMock,
    focusTarget,
  });
  const statuses = [];
  engine.subscribe((state) => statuses.push(state.status));
  await engine.start();
  assert.deepEqual(statuses.slice(0, 3), ['idle', 'loading', 'ready']);
  assert.equal(engine.hasPro(), true);
  const headers = calls[0].headers || {};
  const headerKeys = Object.keys(headers).map((key) => key.toLowerCase());
  assert.ok(headerKeys.includes('x-user-id'));
  assert.equal(headers['X-User-Id'] || headers['x-user-id'], 'tester');
  focusTarget.fire();
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(statuses.at(-1), 'ready');
  assert.ok(statuses.includes('refreshing'));
  assert.equal(canUse('AI_PERSONAS', engine.getState()), true);
  assert.equal(tierFromState(engine.getState()), 'pro');
} else {
  let attempts = 0;
  const fetchMock = async () => {
    attempts += 1;
    if (attempts === 1) {
      return { ok: false, status: 503, json: async () => ({}) };
    }
    return {
      ok: true,
      status: 200,
      json: async () => ({ entitlements: [] }),
    };
  };
  const engine = new UserAccessEngine({
    apiBase: 'https://api.test',
    userId: 'tester',
    fetch: fetchMock,
    focusTarget: null,
  });
  const statuses = [];
  engine.subscribe((state) => statuses.push(state.status));
  await engine.refresh();
  assert.equal(statuses.at(-1), 'error');
  await engine.refresh();
  assert.equal(statuses.at(-1), 'ready');
  assert.equal(engine.hasPro(), false);
}
