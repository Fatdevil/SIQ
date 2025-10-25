import test from 'node:test';
import assert from 'node:assert/strict';

import { createUserAccessStore } from './runtime/UserAccessEngine.js';

test('refresh transitions to ready and normalises entitlements', async () => {
  const responses = [
    {
      ok: true,
      json: async () => ({
        userId: 'user-123',
        tier: 'pro',
        entitlements: { pro: true, elite: false },
        features: { AI_PERSONAS: true, ADVANCED_METRICS: true, TEAM_DASHBOARD: false },
      }),
    },
  ];

  const store = createUserAccessStore('https://api.siq.test', 'user-123', async () => {
    const next = responses.shift();
    if (!next) {
      throw new Error('Missing response');
    }
    return next;
  });

  const transitions = [];
  store.subscribe((state) => transitions.push(state.status));

  await store.refresh();
  const state = store.getState();
  assert.equal(state.status, 'ready');
  assert.equal(state.snapshot.tier, 'pro');
  assert.equal(state.snapshot.entitlements.pro, true);
  assert.equal(state.snapshot.features.TEAM_DASHBOARD, false);
  assert.equal(transitions[0], 'loading');
  assert.equal(transitions[1], 'ready');
});

test('refresh surfaces errors and preserves last snapshot', async () => {
  const store = createUserAccessStore('https://api.siq.test', 'user-999', async () => ({
    ok: false,
    status: 500,
    json: async () => ({}),
  }));

  await assert.rejects(store.refresh.bind(store));
  const state = store.getState();
  assert.equal(state.status, 'error');
  assert.equal(state.snapshot.tier, 'free');
});
