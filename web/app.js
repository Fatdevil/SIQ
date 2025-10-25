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

const state = {
  loading: false,
  result: null,
  tab: "metrics",
  highlights: [],
  leaderboards: {
    hardestShot: [],
    mostHits: [],
  },
  access: {
    snapshot: normaliseSnapshot(),
    loading: true,
    error: null,
  },
  upgrade: {
    receipt: "",
    submitting: false,
    message: "",
    error: "",
  },
};

let lastUpgradeViewAt = 0;

const tabs = [
  { id: "metrics", label: "Metrics" },
  { id: "highlights", label: "Highlights" },
  { id: "leaderboards", label: "Leaderboards" },
  { id: "upgrade", label: "Upgrade" },
];

async function emitTelemetry(event, props = {}) {
  try {
    await fetch(`${API_BASE}/ws/telemetry`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event,
        userId: USER_ID,
        platform: "web",
        timestampMs: Date.now(),
        ...props,
      }),
    });
  } catch (error) {
    console.warn("telemetry failed", error);
  }
}

function normaliseSnapshot(payload = {}) {
  const tier = payload.tier ?? "free";
  const entitlements = payload.entitlements ?? {};
  const features = payload.features ?? {};
  const pro = entitlements.pro ?? tier === "pro" || tier === "elite";
  const elite = entitlements.elite ?? tier === "elite";
  return {
    userId: payload.userId ?? USER_ID,
    tier,
    provider: payload.provider ?? null,
    expiresAt: payload.expiresAt ?? null,
    entitlements: {
      free: true,
      pro,
      elite,
    },
    features: {
      AI_PERSONAS: Boolean(features.AI_PERSONAS ?? pro),
      ADVANCED_METRICS: Boolean(features.ADVANCED_METRICS ?? pro),
      TEAM_DASHBOARD: Boolean(features.TEAM_DASHBOARD ?? elite),
    },
  };
}

function tier() {
  return state.access.snapshot.tier;
}

function isPro() {
  return Boolean(state.access.snapshot.entitlements?.pro);
}

function canUseArPrecision() {
  return Boolean(state.access.snapshot.features.ADVANCED_METRICS);
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

function createBillingBanner() {
  const banner = document.createElement("div");
  banner.className = "billing-banner";
  if (state.access.loading) {
    banner.textContent = "Checking subscription…";
    banner.classList.add("pending");
    return banner;
  }
  if (state.access.error) {
    banner.textContent = state.access.error;
    banner.classList.add("error");
    return banner;
  }
  const snapshot = state.access.snapshot;
  banner.innerHTML = `Current tier: <strong>${snapshot.tier?.toUpperCase() ?? "FREE"}</strong>`;
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
    emitTelemetry("feature_blocked", { feature, source: "web" });
    state.tab = "upgrade";
    render();
  });
  cta.appendChild(message);
  cta.appendChild(button);
  return cta;
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
  const section = document.createElement("section");
  section.className = "feature-section";
  const heading = document.createElement("h3");
  heading.textContent = "Coach Personas";
  section.appendChild(heading);
  const description = document.createElement("p");
  description.textContent = "Hand-picked coaching voices that personalize drills and match prep.";
  section.appendChild(description);

  if (state.access.loading) {
    const loading = document.createElement("p");
    loading.className = "feature-loading";
    loading.textContent = "Loading personas…";
    section.appendChild(loading);
    return section;
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
    section.appendChild(createUpgradeCTA("Unlock all coach personas"));
  }
  return section;
}

function renderArPrecision() {
  const section = document.createElement("section");
  section.className = "feature-section";
  const heading = document.createElement("h3");
  heading.textContent = "AR Target Precision";
  section.appendChild(heading);
  const description = document.createElement("p");
  description.textContent = "Track finishing accuracy with augmented targets on your net.";
  section.appendChild(description);

  if (state.access.loading) {
    const loading = document.createElement("p");
    loading.className = "feature-loading";
    loading.textContent = "Loading precision tools…";
    section.appendChild(loading);
    return section;
  }

  if (!canUseArPrecision()) {
    section.appendChild(
      createUpgradeCTA("AR Target precision scoring"),
    );
    return section;
  }

  const unlocked = document.createElement("div");
  unlocked.className = "ar-summary";
  unlocked.innerHTML = `
    <p class="success">✅ Precision tracking unlocked. Calibrate the target to start logging accuracy streaks.</p>
  `;
  section.appendChild(unlocked);
  return section;
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
    "Use mock receipts (PRO-* or ELITE-*) to simulate App Store or Play Store upgrades while we finalize in-app purchases.";
  container.appendChild(copy);

  if (state.access.snapshot) {
    const current = document.createElement("p");
    current.className = "upgrade-status";
    current.innerHTML = `Current tier: <strong>${tier().toUpperCase()}</strong>`;
    container.appendChild(current);
  }

  const form = document.createElement("form");
  form.className = "upgrade-form";
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    await submitUpgrade();
  });

  const label = document.createElement("label");
  label.setAttribute("for", "receipt");
  label.textContent = "Receipt code";

  const input = document.createElement("input");
  input.id = "receipt";
  input.name = "receipt";
  input.type = "text";
  input.placeholder = "PRO-123";
  input.autocomplete = "off";
  input.value = state.upgrade.receipt;
  input.addEventListener("input", (event) => {
    state.upgrade.receipt = event.target.value;
  });

  const button = document.createElement("button");
  button.type = "submit";
  button.textContent = state.upgrade.submitting ? "Activating…" : "Activate Pro";
  button.disabled = state.upgrade.submitting;

  form.appendChild(label);
  form.appendChild(input);
  form.appendChild(button);
  container.appendChild(form);

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

  const restore = document.createElement("button");
  restore.type = "button";
  restore.className = "restore-button";
  restore.textContent = "Restore purchases";
  restore.disabled = state.upgrade.submitting;
  restore.addEventListener("click", () => {
    restorePurchases();
  });
  container.appendChild(restore);

  return container;
}

function render() {
  app.innerHTML = "";
  app.appendChild(createTabs());

  if (state.tab === "metrics") {
    app.appendChild(createBillingBanner());
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
    const now = Date.now();
    if (now - lastUpgradeViewAt > 500) {
      lastUpgradeViewAt = now;
      emitTelemetry("view_upgrade", { source: "web" });
    }
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
  state.access.loading = true;
  state.access.error = null;
  render();
  try {
    const response = await fetch(
      `${API_BASE}/me/entitlements?userId=${encodeURIComponent(USER_ID)}`,
    );
    if (!response.ok) {
      throw new Error(`status ${response.status}`);
    }
    const data = await response.json();
    state.access.snapshot = normaliseSnapshot(data);
  } catch (error) {
    console.error("Failed to fetch entitlements", error);
    state.access.error = "Unable to refresh entitlements.";
  } finally {
    state.access.loading = false;
    render();
  }
}

async function submitUpgrade() {
  const receipt = state.upgrade.receipt.trim();
  if (!receipt) {
    state.upgrade.error = "Enter a mock receipt (PRO-* or ELITE-*).";
    state.upgrade.message = "";
    render();
    return;
  }
  state.upgrade.submitting = true;
  state.upgrade.error = "";
  state.upgrade.message = "";
  render();
  try {
    emitTelemetry("start_checkout", { provider: "stripe" });
    const response = await fetch(`${API_BASE}/billing/receipt`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        userId: USER_ID,
        platform: "web",
        receipt,
      }),
    });
    if (!response.ok) {
      throw new Error(`status ${response.status}`);
    }
    const data = await response.json();
    state.upgrade.message = `Activated ${data.tier.toUpperCase()} for ${USER_ID}.`;
    state.upgrade.receipt = "";
    state.access.snapshot = normaliseSnapshot(data);
    state.access.error = null;
    emitTelemetry("receipt_verified", { provider: "stripe", tier: data.tier });
    render();
  } catch (error) {
    console.error("Failed to verify receipt", error);
    state.upgrade.error = "Verification failed. Check the receipt and try again.";
  } finally {
    state.upgrade.submitting = false;
    render();
  }
}

async function restorePurchases() {
  state.upgrade.error = "";
  state.upgrade.message = "";
  render();
  emitTelemetry("restore_clicked", { provider: "stripe" });
  try {
    const response = await fetch(`${API_BASE}/billing/receipt`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        userId: USER_ID,
        platform: "web",
        mode: "restore",
      }),
    });
    if (!response.ok) {
      throw new Error(`status ${response.status}`);
    }
    const data = await response.json();
    state.access.snapshot = normaliseSnapshot(data);
    state.access.error = null;
    state.upgrade.message = "Restored your SoccerIQ subscription.";
  } catch (error) {
    console.error("Failed to restore purchases", error);
    state.upgrade.error = "Unable to restore purchases. Try again shortly.";
  } finally {
    render();
  }
}

render();
refreshEntitlements();
window.addEventListener("focus", () => {
  refreshEntitlements();
});
