const app = document.getElementById("app");

const state = {
  loading: false,
  result: null,
  tab: "metrics",
  highlights: [],
  leaderboards: {
    hardestShot: [],
    mostHits: [],
  },
};

const tabs = [
  { id: "metrics", label: "Metrics" },
  { id: "highlights", label: "Highlights" },
  { id: "leaderboards", label: "Leaderboards" },
];

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

function render() {
  app.innerHTML = "";
  app.appendChild(createTabs());

  if (state.loading && state.tab === "metrics") {
    const loading = document.createElement("p");
    loading.textContent = "Analyzing back-view...";
    app.appendChild(loading);
    return;
  }
  if (state.tab === "metrics") {
    if (state.result) {
      app.appendChild(createCard(state.result));
    } else {
      const empty = document.createElement("p");
      empty.textContent = "Upload a clip to see metrics.";
      app.appendChild(empty);
    }
  } else if (state.tab === "highlights") {
    app.appendChild(renderHighlights());
  } else if (state.tab === "leaderboards") {
    app.appendChild(renderLeaderboards());
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

render();
