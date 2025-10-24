const app = document.getElementById("app");

const state = {
  loading: false,
  result: null,
};

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
  if (state.loading) {
    const loading = document.createElement("p");
    loading.textContent = "Analyzing back-view...";
    app.appendChild(loading);
    return;
  }
  if (state.result) {
    app.appendChild(createCard(state.result));
  } else {
    const empty = document.createElement("p");
    empty.textContent = "Upload a clip to see metrics.";
    app.appendChild(empty);
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

render();
