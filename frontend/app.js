const state = {
  initial: null,
  season: null,
  currentRace: null,
  raceType: "race",
};

const teamColors = {
  McLaren: "#ff8700",
  Ferrari: "#e8002d",
  "Red Bull Racing": "#3671c6",
  Mercedes: "#27f4d2",
  "Aston Martin": "#229971",
  Williams: "#64c4ff",
  Audi: "#bb1424",
  Alpine: "#ff87bc",
  Haas: "#b6babd",
  "Racing Bulls": "#6692ff",
  Cadillac: "#d8d8dc",
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

function colorFor(team) {
  return teamColors[team] || "#e1222e";
}

function notify(message) {
  const notice = $("#notice");
  notice.textContent = message;
  notice.classList.add("visible");
  window.clearTimeout(notify.timeout);
  notify.timeout = window.setTimeout(() => notice.classList.remove("visible"), 4500);
}

function navigate(view) {
  $$(".view-panel").forEach((panel) => panel.classList.toggle("active", panel.id === `view-${view}`));
  $$(".nav-link").forEach((button) => button.classList.toggle("active", button.dataset.view === view));
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function makeCalendarCard(round, detailed = false) {
  const race = state.season?.races[round.round - 1];
  const team = race?.winner
    ? state.season.standings.drivers.find((driver) => driver.name === race.winner)?.team
    : "";
  const winnerLine = race
    ? `<span class="calendar-winner">${race.pole ? `P ${escapeHtml(race.pole)}` : ""}${race.winner ? ` · W ${escapeHtml(race.winner)}` : ""}</span>`
    : "";
  return `<button class="calendar-card${race?.winner ? " race-won" : ""}" data-round="${round.round}" style="--team-color:${colorFor(team)}">
    <span class="calendar-round">ROUND ${String(round.round).padStart(2, "0")}${round.is_sprint ? '<span class="sprint-badge">SPRINT</span>' : ""}</span>
    <span class="calendar-name">${escapeHtml(round.name)}</span>
    <span class="calendar-country">${escapeHtml(round.country)}${detailed ? ` · ${round.laps} LAPS` : ""}</span>${winnerLine}
  </button>`;
}

function renderCalendar() {
  const rounds = state.initial?.calendar || [];
  $("#calendar-strip").innerHTML = rounds.slice(0, 12).map((round) => makeCalendarCard(round)).join("");
  $("#calendar-grid").innerHTML = rounds.map((round) => makeCalendarCard(round, true)).join("");
  $("#round-count").textContent = rounds.length || 24;
}

function renderStandings() {
  const standings = state.season?.standings;
  if (!standings) return;

  const driverRows = standings.drivers;
  $("#driver-standings").innerHTML = driverRows.slice(0, 8).map((driver, index) => `
    <tr class="${index < 3 ? `podium-${index + 1}` : ""}">
      <td class="position-cell">${String(index + 1).padStart(2, "0")}</td>
      <td class="driver-cell">${escapeHtml(driver.flag)} &nbsp;${escapeHtml(driver.name)}</td>
      <td class="team-cell"><span class="team-dot" style="--team-color:${colorFor(driver.team)}"></span>${escapeHtml(driver.team)}</td>
      <td>${driver.wins}</td><td class="points-cell">${driver.points}</td>
    </tr>`).join("");
  $("#drivers-empty").hidden = true;

  $("#driver-table").innerHTML = driverRows.map((driver, index) => `
    <tr class="${index < 3 ? `podium-${index + 1}` : ""}">
      <td class="position-cell">${String(index + 1).padStart(2, "0")}</td>
      <td class="driver-cell">${escapeHtml(driver.flag)} &nbsp;${escapeHtml(driver.name)}</td>
      <td class="team-cell"><span class="team-dot" style="--team-color:${colorFor(driver.team)}"></span>${escapeHtml(driver.team)}</td>
      <td>${driver.wins}</td><td>${driver.podiums}</td><td>${driver.poles}</td><td>${driver.dnfs}</td>
      <td class="points-cell">${driver.points}</td>
    </tr>`).join("");
  $("#driver-table-empty").hidden = true;
  $("#driver-table-subtitle").textContent = `${driverRows.length} drivers · ${state.season.rounds} rounds completed`;

  const constructors = standings.constructors;
  const maxPoints = Math.max(1, constructors[0]?.points || 0);
  $("#constructor-list").innerHTML = constructors.slice(0, 7).map((team, index) => `
    <div class="constructor-row">
      <span class="constructor-rank">${String(index + 1).padStart(2, "0")}</span>
      <div class="constructor-meta"><div class="constructor-name"><span class="team-dot" style="--team-color:${colorFor(team.name)}"></span>${escapeHtml(team.name)}</div>
      <div class="constructor-bar-track"><div class="constructor-bar" style="--bar-width:${Math.max(3, team.points / maxPoints * 100)}%;--team-color:${colorFor(team.name)}"></div></div></div>
      <span class="constructor-points">${team.points}</span>
    </div>`).join("");
  $("#constructors-empty").hidden = true;

  $("#team-table").innerHTML = constructors.map((team, index) => `
    <tr class="${index < 3 ? `podium-${index + 1}` : ""}">
      <td class="position-cell">${String(index + 1).padStart(2, "0")}</td>
      <td class="driver-cell"><span class="team-dot" style="--team-color:${colorFor(team.name)}"></span>${escapeHtml(team.name)}</td>
      <td class="team-cell">${team.drivers.map(escapeHtml).join(" / ")}</td>
      <td>${team.wins}</td><td class="points-cell">${team.points}</td>
    </tr>`).join("");
  $("#team-table-empty").hidden = true;
}

function renderSeason() {
  const season = state.season;
  if (!season) return;
  const drivers = season.standings.drivers;
  const teams = season.standings.constructors;
  const uniqueWinners = new Set(season.races.map((race) => race.winner).filter(Boolean)).size;
  $("#stat-progress").innerHTML = `${season.rounds}<small> / ${season.rounds}</small>`;
  $("#stat-progress-foot").textContent = "The chequered flag has fallen";
  $("#stat-winner").textContent = drivers[0]?.name || "—";
  $("#stat-winner-foot").textContent = drivers[0] ? `${drivers[0].team} · ${drivers[0].points} pts` : "No classified drivers";
  $("#stat-team").textContent = teams[0]?.name || "—";
  $("#stat-team-foot").textContent = teams[0] ? `${teams[0].points} points · ${teams[0].wins} wins` : "Every point counts";
  $("#stat-wins").textContent = String(uniqueWinners);
  $("#stat-wins-foot").textContent = `Different race winners this season`;
  $("#sidebar-year").textContent = season.year;
  $("#topbar-year").textContent = season.year;
  $("#hero-year").textContent = season.year;
  $("#season-status").textContent = "Season complete";
  $(".live-dot").classList.add("is-live");
  $("#simulate-label").textContent = "Run it again";
  renderStandings();
  renderCalendar();
}

async function simulateSeason() {
  const button = $("#simulate-button");
  const heroButton = $("#hero-simulate");
  const seedValue = $("#seed-input").value.trim();
  const seed = seedValue === "" ? null : Number(seedValue);
  if (seed !== null && !Number.isSafeInteger(seed)) {
    notify("Enter a whole-number seed, or leave it blank for a random season.");
    $("#seed-input").focus();
    return;
  }
  button.disabled = true;
  heroButton.disabled = true;
  $("#simulate-label").innerHTML = '<span class="loading-ring"></span> Running 24 rounds…';
  $("#season-status").textContent = "Season in progress";
  try {
    const response = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ year: state.initial.year, seed }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Simulation failed.");
    state.season = payload;
    state.currentRace = null;
    renderSeason();
    navigate("overview");
  } catch (error) {
    $("#season-status").textContent = state.season ? "Season complete" : "Ready to race";
    notify(error.message || "Could not reach the simulator. Check that the local server is running.");
  } finally {
    button.disabled = false;
    heroButton.disabled = false;
    $("#simulate-label").textContent = state.season ? "Run it again" : "Simulate season";
  }
}

function renderRaceType() {
  const race = state.currentRace;
  if (!race) return;
  const isSprint = state.raceType === "sprint" && race.sprint;
  const result = isSprint ? race.sprint : race.results;
  $("#race-tabs").hidden = !race.sprint;
  $$("#race-tabs button").forEach((button) => button.classList.toggle("selected", button.dataset.raceType === state.raceType));
  $("#race-results-table").innerHTML = result.results.map((entry) => `
    <tr>
      <td class="position-cell">${entry.position ? `P${String(entry.position).padStart(2, "0")}` : "—"}</td>
      <td class="driver-cell">${escapeHtml(entry.name)}${entry.fastest_lap ? ' <span title="Fastest lap">✦</span>' : ""}</td>
      <td class="team-cell"><span class="team-dot" style="--team-color:${colorFor(entry.team)}"></span>${escapeHtml(entry.team)}</td>
      <td>${entry.grid}</td><td>${entry.pit_stops}</td>
      <td class="${entry.status === "DNF" ? "status-dnf" : "status-finished"}">${entry.status}${entry.laps < race.laps && entry.status !== "DNF" ? ` · ${race.laps - entry.laps}L` : ""}</td>
      <td class="points-cell">${entry.points}</td>
    </tr>`).join("");
  $("#race-winner").textContent = result.winner || "No classified finishers";
}

function openRace(round) {
  const race = state.season?.races.find((item) => item.round === round);
  if (!race) {
    notify("Simulate the season to reveal this race result.");
    return;
  }
  state.currentRace = race;
  state.raceType = "race";
  $("#race-round").textContent = `ROUND ${String(race.round).padStart(2, "0")}`;
  $("#race-title").textContent = race.name;
  $("#race-subtitle").textContent = `${race.country} · ${race.laps} laps${race.is_sprint ? " · Sprint weekend" : ""}`;
  $("#race-highlights").innerHTML = `
    <div class="highlight-card"><span>POLE POSITION</span><strong>${escapeHtml(race.pole || "—")}</strong></div>
    <div class="highlight-card"><span>FASTEST LAP</span><strong>${escapeHtml(race.results.fastest_lap || "—")}</strong></div>
    <div class="highlight-card"><span>RACE CONDITIONS</span><strong>${race.wet ? (race.results.extreme_wet ? "Heavy rain" : "Wet") : "Dry"}</strong></div>
    <div class="highlight-card"><span>SAFETY CARS</span><strong>${race.safety_cars}</strong></div>`;
  $("#sprint-tab").hidden = !race.sprint;
  renderRaceType();
  navigate("race");
}

async function start() {
  try {
    const response = await fetch("/api/initial");
    if (!response.ok) throw new Error("Could not load the season grid.");
    state.initial = await response.json();
    $("#sidebar-year").textContent = state.initial.year;
    $("#topbar-year").textContent = state.initial.year;
    $("#hero-year").textContent = state.initial.year;
    $("#round-count").textContent = state.initial.calendar.length;
    $("#hero-simulate").addEventListener("click", simulateSeason);
    $("#simulate-button").addEventListener("click", simulateSeason);
    $$(".nav-link").forEach((button) => button.addEventListener("click", () => navigate(button.dataset.view)));
    $$("[data-go]").forEach((button) => button.addEventListener("click", () => navigate(button.dataset.go)));
    document.addEventListener("click", (event) => {
      const card = event.target.closest("[data-round]");
      if (card) openRace(Number(card.dataset.round));
    });
    $("#race-tabs").addEventListener("click", (event) => {
      const button = event.target.closest("[data-race-type]");
      if (!button || button.hidden) return;
      state.raceType = button.dataset.raceType;
      renderRaceType();
    });
    renderCalendar();
  } catch (error) {
    notify(`${error.message} Start the app with: python3 backend/server.py`);
    $("#season-status").textContent = "Server unavailable";
  }
}

start();
