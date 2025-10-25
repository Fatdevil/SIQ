const app = document.getElementById("app");

const API_BASE = window.API_BASE ?? "";
const USER_ID = window.CURRENT_USER_ID ?? "mock-user";

const COACH_PERSONAS = [
  {
    id: "visionary",
    name: "Visionary Playmaker",
    tagline: "Unlock elite build-up patterns tailored to every possession.",
  },
  {
    id: "finisher",
    name: "Clinical Finisher",
    tagline: "Dial in striker drills for every body shape and first touch.",
  },
  {
    id: "guardian",
    name: "Backline Guardian",
    tagline: "Coach defensive units with instant shape and pressure cues.",
  },
];

const blockedFeatures = new Set();

const state = {
  loading: false,
  result: null,
  tab: "metrics",
  highlights: [],
  leaderboards: {
    hardestShot: [],
    mostHits: [],
  },
  entitlements: {
    status: "loading",
    map: {},
    error: null,
  },
  upgrade: {
    submitting: false,
    message: "",
    error: "",
  },
};

const tabs = [
  { id: "metrics", label: "Metrics" },
  { id: "highlights", label: "Highlights" },
  { id: "leaderboards", label: "Leaderboards" },
  { id: "upgrade", label: "Upgrade" },
];

function tier() {
  if (state.entitlements.map.elite?.status === "active") {
    return "elite";
  }
  if (state.entitlements.map.pro?.status === "active") {
    return "pro";
  }
  return "free";
}

function isPro() {
  const current = tier();
  return current === "pro" || current === "elite";
}

function canUseArPrecision() {
  return isPro();
}

function maybeLogFeatureBlocked(feature) {
  if (blockedFeatures.has(feature)) {
    return;
  }
  blockedFeatures.add(feature);
  fetch(`${API_BASE}/billing/events/feature-blocked`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": USER_ID,
    },
    body: JSON.stringify({ feature }),
  }).catch(() => {
    blockedFeatures.delete(feature);
  });
}

function createTabs() {
  const nav = document.createElement("nav");
  nav.className = "tabs";
  tabs.forEach((tab) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = tab.label;
    button.className = tab.id === state.tab ? "active" : "";
    button.addEventListener("click", () => {
      state.tab = tab.id;
      render();
    });
    nav.appendChild(button);
  });
  return nav;
}

function createEntitlementBanner() {
  const banner = document.createElement("div");
  banner.className = "billing-banner";
  if (state.entitlements.status === "loading" || state.entitlements.status === "refreshing") {
    banner.textContent = "Checking subscription…";
    banner.classList.add("pending");
    return banner;
  }
  if (state.entitlements.status === "error") {
    banner.textContent = state.entitlements.error ?? "Unable to refresh entitlements.";
    banner.classList.add("error");
    return banner;
  }
  banner.innerHTML = `Current tier: <strong>${tier().toUpperCase()}</strong>`;
  return banner;
}

function createUpgradeCTA(feature) {
  const cta = document.createElement("div");
  cta.className = "upgrade-cta";
  const message = document.createElement("p");
  message.innerHTML = `🔒 ${feature} is locked for Free accounts.`;
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = "Go to Upgrade";
  button.addEventListener("click", () => {
    state.tab = "upgrade";
    render();
  });
  cta.appendChild(message);
  cta.appendChild(button);
  return cta;
}

function attachPremiumOverlay(section, featureKey) {
  maybeLogFeatureBlocked(featureKey);
  section.classList.add("premium-locked");
  const overlay = document.createElement("div");
  overlay.className = "premium-overlay";
  const text = document.createElement("p");
  text.textContent = "SoccerIQ Pro unlocks this feature.";
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = "Upgrade";
  button.addEventListener("click", () => {
    state.tab = "upgrade";
    render();
  });
  overlay.appendChild(text);
  overlay.appendChild(button);
  section.appendChild(overlay);
}

function createCard(result) {
  const card = document.createElement("section");
  card.className = "result-card";
  card.innerHTML = `
    <h2>Back-view Result</h2>
    <div class="metrics">
      <div><span class="label">Ball Speed</span><span>${result.ballSpeedMps} m/s</span></div>
      <div><span class="label">Club Speed</span><span>${result.clubSpeedMps} m/s</span></div>
      <div><span class="label">Side Angle</span><span>${result.sideAngleDeg}°</span></div>
      <div><span class="label">Carry Estimate</span><span>${result.carryEstM} m</span></div>
    </div>
    <div class="quality">
      <h3>Quality Flags</h3>
      <ul>
        ${Object.entries(result.quality)
          .map(([key, value]) => `<li>${key}: ${value ? "✅" : "⚠️"}</li>`)
          .join("")}
      </ul>
    </div>
    <div class="source-hints">
      <h3>Source Hints</h3>
      <pre>${JSON.stringify(result.sourceHints, null, 2)}</pre>
    </div>
    <div class="overlay" aria-hidden="true">
      <span class="ghost">⚽️</span>
    </div>
  `;
  return card;
}

function renderCoachPersonas() {
  const wrapper = document.createElement("div");
  const section = document.createElement("section");
  section.className = "feature-section";
  const heading = document.createElement("h3");
  heading.textContent = "Coach Personas";
  section.appendChild(heading);
  const description = document.createElement("p");
  description.textContent = "Hand-picked coaching voices that personalize drills and match prep.";
  section.appendChild(description);

  if (state.entitlements.status === "loading" || state.entitlements.status === "refreshing") {
    const loading = document.createElement("p");
    loading.className = "feature-loading";
    loading.textContent = "Loading personas…";
    section.appendChild(loading);
    wrapper.appendChild(section);
    return wrapper;
  }

  const grid = document.createElement("div");
  grid.className = "persona-grid";
  const unlocked = isPro() ? COACH_PERSONAS.length : 1;
  COACH_PERSONAS.forEach((persona, index) => {
    const card = document.createElement("article");
    const locked = index >= unlocked;
    card.className = `persona-card${locked ? " locked" : ""}`;
    card.innerHTML = `
      <h4>${persona.name}</h4>
      <p>${persona.tagline}</p>
      <span class="pill">${locked ? "Locked" : "Included"}</span>
    `;
    grid.appendChild(card);
  });
  section.appendChild(grid);

  if (!isPro()) {
    attachPremiumOverlay(section, "coach_personas");
    wrapper.appendChild(section);
    wrapper.appendChild(createUpgradeCTA("Unlock all coach personas"));
    return wrapper;
  }
  wrapper.appendChild(section);
  return wrapper;
}

function renderArPrecision() {
  const wrapper = document.createElement("div");
  const section = document.createElement("section");
  section.className = "feature-section";
  const heading = document.createElement("h3");
  heading.textContent = "AR Target Precision";
  section.appendChild(heading);
  const description = document.createElement("p");
  description.textContent = "Track finishing accuracy with augmented targets on your net.";
  section.appendChild(description);

  if (state.entitlements.status === "loading" || state.entitlements.status === "refreshing") {
    const loading = document.createElement("p");
    loading.className = "feature-loading";
    loading.textContent = "Loading precision tools…";
    section.appendChild(loading);
    wrapper.appendChild(section);
    return wrapper;
  }

  if (!canUseArPrecision()) {
    attachPremiumOverlay(section, "ar_precision");
    wrapper.appendChild(section);
    wrapper.appendChild(createUpgradeCTA("AR Target precision scoring"));
    return wrapper;
  }

  const unlocked = document.createElement("div");
  unlocked.className = "ar-summary";
  unlocked.innerHTML = `
    <p class="success">✅ Precision tracking unlocked. Calibrate the target to start logging accuracy streaks.</p>
  `;
  section.appendChild(unlocked);
  wrapper.appendChild(section);
  return wrapper;
}

function renderUpgrade() {
  const container = document.createElement("section");
  container.className = "upgrade-section";
  const title = document.createElement("h2");
  title.textContent = "Activate SoccerIQ Pro";
  container.appendChild(title);

  const copy = document.createElement("p");
  copy.className = "upgrade-copy";
  copy.innerHTML =
    "Checkout is powered by Stripe for the web and the App/Play Store on mobile. Complete payment to unlock Pro instantly.";
  container.appendChild(copy);

  const status = document.createElement("p");
  status.className = "upgrade-status";
  status.innerHTML = `Current tier: <strong>${tier().toUpperCase()}</strong>`;
  container.appendChild(status);

  const benefits = document.createElement("ul");
  benefits.className = "upgrade-benefits";
  [
    "Unlimited coach personas",
    "AR target precision scoring",
    "Priority match insights",
  ].forEach((benefit) => {
    const item = document.createElement("li");
    item.textContent = benefit;
    benefits.appendChild(item);
  });
  container.appendChild(benefits);

  const button = document.createElement("button");
  button.type = "button";
  button.className = "upgrade-primary";
  button.textContent = state.upgrade.submitting ? "Redirecting…" : "Upgrade with Stripe Checkout";
  button.disabled = state.upgrade.submitting;
  button.addEventListener("click", async () => {
    await startWebCheckout();
  });
  container.appendChild(button);

  const restore = document.createElement("button");
  restore.type = "button";
  restore.className = "restore-button";
  restore.textContent = "Restore purchases";
  restore.addEventListener("click", () => {
    handleRestore();
  });
  container.appendChild(restore);

  if (state.upgrade.error) {
    const error = document.createElement("p");
    error.className = "upgrade-error";
    error.textContent = state.upgrade.error;
    container.appendChild(error);
  }

  if (state.upgrade.message) {
    const message = document.createElement("p");
    message.className = "upgrade-success";
    message.textContent = state.upgrade.message;
    container.appendChild(message);
  }

  return container;
}

function render() {
  app.innerHTML = "";
  app.appendChild(createTabs());

  if (state.tab === "metrics") {
    app.appendChild(createEntitlementBanner());
    if (state.loading) {
      const loading = document.createElement("p");
      loading.textContent = "Analyzing back-view…";
      app.appendChild(loading);
    } else if (state.result) {
      app.appendChild(createCard(state.result));
    } else {
      const empty = document.createElement("p");
      empty.textContent = "Upload a clip to see metrics.";
      app.appendChild(empty);
    }
    app.appendChild(renderCoachPersonas());
    app.appendChild(renderArPrecision());
  } else if (state.tab === "highlights") {
    app.appendChild(renderHighlights());
  } else if (state.tab === "leaderboards") {
    app.appendChild(renderLeaderboards());
  } else if (state.tab === "upgrade") {
    app.appendChild(renderUpgrade());
  }
}

export function setBackViewResult(result) {
  state.result = result;
  state.loading = false;
  render();
}

export function setLoading() {
  state.loading = true;
  render();
}

export function setHighlights(highlights) {
  state.highlights = highlights;
  render();
}

export function setLeaderboards(leaderboards) {
  state.leaderboards = leaderboards;
  render();
}

function renderHighlights() {
  const container = document.createElement("div");
  container.className = "highlight-grid";
  if (!state.highlights.length) {
    const empty = document.createElement("p");
    empty.textContent = "No highlights yet. Capture a hit to create one.";
    container.appendChild(empty);
    return container;
  }
  state.highlights.forEach((highlight) => {
    const tile = document.createElement("article");
    tile.className = "highlight-card";
    tile.innerHTML = `
      <div class="preview" role="img" aria-label="${highlight.title}">
        <span>${highlight.badge}</span>
      </div>
      <div class="details">
        <h3>${highlight.title}</h3>
        <p>${highlight.subtitle}</p>
        <button type="button" data-id="${highlight.id}">Share</button>
      </div>
    `;
    const button = tile.querySelector("button");
    button.addEventListener("click", () => highlight.onShare?.(highlight));
    container.appendChild(tile);
  });
  return container;
}

function leaderboardSection(title, entries) {
  const section = document.createElement("section");
  section.className = "leaderboard";
  section.innerHTML = `<h3>${title}</h3>`;
  const list = document.createElement("ol");
  entries.forEach((entry) => {
    const item = document.createElement("li");
    item.innerHTML = `
      <span class="rank">${entry.rank}</span>
      <span class="player">${entry.player}</span>
      <span class="score">${entry.score}</span>
      <span class="region">${entry.region}</span>
    `;
    list.appendChild(item);
  });
  section.appendChild(list);
  return section;
}

function renderLeaderboards() {
  const container = document.createElement("div");
  container.className = "leaderboard-grid";
  const hardest = leaderboardSection("Hardest Shot", state.leaderboards.hardestShot);
  const hits = leaderboardSection("Most Hits", state.leaderboards.mostHits);
  container.appendChild(hardest);
  container.appendChild(hits);
  return container;
}

async function refreshEntitlements() {
  state.entitlements.status = state.entitlements.status === "ready" ? "refreshing" : "loading";
  state.entitlements.error = null;
  render();
  try {
    const response = await fetch(`${API_BASE}/me/entitlements`, {
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-User-Id": USER_ID,
      },
    });
    if (!response.ok) {
      throw new Error(`status ${response.status}`);
    }
    const data = await response.json();
    const entries = Array.isArray(data.entitlements) ? data.entitlements : [];
    const map = {};
    entries.forEach((entry) => {
      if (entry && entry.productId) {
        map[entry.productId] = entry;
      }
    });
    state.entitlements.map = map;
    state.entitlements.status = "ready";
    state.entitlements.error = null;
  } catch (error) {
    console.error("Failed to fetch entitlements", error);
    state.entitlements.status = "error";
    state.entitlements.error = "Unable to refresh entitlements.";
  } finally {
    render();
  }
}

async function startWebCheckout() {
  if (state.upgrade.submitting) {
    return;
  }
  state.upgrade.submitting = true;
  state.upgrade.error = "";
  state.upgrade.message = "";
  render();
  try {
    const response = await fetch(`${API_BASE}/billing/receipt`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-User-Id": USER_ID,
      },
      body: JSON.stringify({
        provider: "stripe",
        payload: {
          receipt: `STRIPE-${Date.now()}`,
          productId: "pro",
        },
      }),
    });
    if (!response.ok) {
      throw new Error(`status ${response.status}`);
    }
    const data = await response.json();
    state.upgrade.message = `You're now on ${data.productId.toUpperCase()} via Stripe Checkout.`;
    await refreshEntitlements();
  } catch (error) {
    console.error("Failed to start checkout", error);
    state.upgrade.error = "Checkout failed. Try again in a moment.";
  } finally {
    state.upgrade.submitting = false;
    render();
  }
}

function handleRestore() {
  fetch(`${API_BASE}/billing/events/restore`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": USER_ID,
    },
    body: JSON.stringify({ provider: "stripe" }),
  }).catch(() => undefined);
  window.open("https://billing.stripe.com/p/session/test", "_blank", "noopener");
}

render();
refreshEntitlements();

if (typeof window !== "undefined") {
  window.addEventListener("focus", () => {
    void refreshEntitlements();
  });
}
