import { useEffect, useState } from "react";
import type { CSSProperties, ReactNode } from "react";
import { LabPages } from "./labs";
import type { LabView } from "./labs";
import { colorFor } from "./theme";

type View = "overview" | "calendar" | "drivers" | "teams" | "race" | LabView;
type RaceType = "race" | "sprint";

interface DriverProfile {
  name: string;
  number: number;
  nationality: string;
  flag: string;
  team: string;
  pace: number;
  overall: number;
}

interface Driver extends DriverProfile {
  points: number;
  wins: number;
  podiums: number;
  poles: number;
  dnfs: number;
}

interface Constructor {
  name: string;
  full_name: string;
  points: number;
  wins: number;
  car_performance: number;
  drivers: string[];
}

interface CalendarRound {
  round: number;
  name: string;
  country: string;
  laps: number;
  is_sprint: boolean;
}

interface RaceEntry {
  name: string;
  team: string;
  position: number | null;
  grid: number;
  points: number;
  status: "Finished" | "DNF";
  fastest_lap: boolean;
  time: number;
  laps: number;
  pit_stops: number;
  strategy: string[];
}

interface RaceResult {
  winner: string | null;
  fastest_lap: string;
  wet: boolean;
  extreme_wet: boolean;
  safety_cars: number;
  results: RaceEntry[];
}

interface SimulatedRace extends CalendarRound {
  winner: string | null;
  pole: string | null;
  wet: boolean;
  qualifying_wet: boolean;
  safety_cars: number;
  qualifying_grid: string[];
  results: RaceResult;
  sprint: RaceResult | null;
}

interface InitialData {
  year: number;
  teams: Array<{
    name: string;
    full_name: string;
    drivers: DriverProfile[];
  }>;
  calendar: CalendarRound[];
}

interface SeasonData {
  year: number;
  seed: number | null;
  rounds: number;
  standings: {
    drivers: Driver[];
    constructors: Constructor[];
  };
  races: SimulatedRace[];
}

type NavView = Exclude<View, "race">;

const NAV_ITEMS: Array<{ view: NavView; icon: string; label: string }> = [
  { view: "overview", icon: "◫", label: "Overview" },
  { view: "calendar", icon: "◷", label: "Race calendar" },
  { view: "drivers", icon: "♙", label: "Drivers" },
  { view: "teams", icon: "▤", label: "Constructors" },
];

const LAB_NAV_ITEMS: Array<{ view: NavView; icon: string; label: string }> = [
  { view: "weekend", icon: "⚑", label: "Single round" },
  { view: "predict", icon: "◎", label: "Predictor" },
  { view: "seasons", icon: "↻", label: "Multi-season" },
  { view: "until", icon: "⌖", label: "Until it happens" },
  { view: "history", icon: "❖", label: "History" },
  { view: "academies", icon: "✎", label: "Academies" },
];

const SEASON_VIEWS: View[] = ["overview", "calendar", "drivers", "teams", "race"];

function Eyebrow({ children }: { children: ReactNode }) {
  return <div className="eyebrow">{children}</div>;
}

function TeamDot({ team }: { team: string }) {
  return <span className="team-dot" style={{ "--team-color": colorFor(team) } as CSSProperties} />;
}

function SectionHeading({
  eyebrow,
  title,
  action,
  onAction,
}: {
  eyebrow: string;
  title: string;
  action?: string;
  onAction?: () => void;
}) {
  return (
    <div className="section-heading">
      <div>
        <Eyebrow>{eyebrow}</Eyebrow>
        <h2>{title}</h2>
      </div>
      {action && onAction && (
        <button className="text-button" onClick={onAction}>
          {action} <span>↗</span>
        </button>
      )}
    </div>
  );
}

function EmptyState({
  title,
  description,
  flag,
  compact = false,
}: {
  title: string;
  description: string;
  flag?: string;
  compact?: boolean;
}) {
  return (
    <div className={`empty-state${compact ? " compact-empty" : ""}`}>
      {flag && <span className="empty-flag">{flag}</span>}
      <strong>{title}</strong>
      <span>{description}</span>
    </div>
  );
}

function CalendarCard({
  round,
  race,
  detailed = false,
  onOpen,
}: {
  round: CalendarRound;
  race?: SimulatedRace;
  detailed?: boolean;
  onOpen: (round: number) => void;
}) {
  const winnerTeam = race?.winner
    ? race.results.results.find((entry) => entry.name === race.winner)?.team ?? ""
    : "";
  return (
    <button
      className={`calendar-card${race?.winner ? " race-won" : ""}`}
      data-round={round.round}
      style={{ "--team-color": colorFor(winnerTeam) } as CSSProperties}
      onClick={() => onOpen(round.round)}
    >
      <span className="calendar-round">
        ROUND {String(round.round).padStart(2, "0")}
        {round.is_sprint && <span className="sprint-badge">SPRINT</span>}
      </span>
      <span className="calendar-name">{round.name}</span>
      <span className="calendar-country">
        {round.country}
        {detailed && ` · ${round.laps} LAPS`}
      </span>
      {race && (
        <span className="calendar-winner">
          {race.pole && `P ${race.pole}`}
          {race.pole && race.winner && " · "}
          {race.winner && `W ${race.winner}`}
        </span>
      )}
    </button>
  );
}

function StandingsTable({ drivers }: { drivers: Driver[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>POS</th><th>DRIVER</th><th>TEAM</th><th>W</th><th>POD</th><th>POLE</th><th>DNF</th>
            <th className="align-right">PTS</th>
          </tr>
        </thead>
        <tbody>
          {drivers.map((driver, index) => (
            <tr className={index < 3 ? `podium-${index + 1}` : ""} key={driver.name}>
              <td className="position-cell">{String(index + 1).padStart(2, "0")}</td>
              <td className="driver-cell">{driver.flag} &nbsp;{driver.name}</td>
              <td className="team-cell"><TeamDot team={driver.team} />{driver.team}</td>
              <td>{driver.wins}</td><td>{driver.podiums}</td><td>{driver.poles}</td><td>{driver.dnfs}</td>
              <td className="points-cell">{driver.points}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ConstructorRows({ teams }: { teams: Constructor[] }) {
  const maxPoints = Math.max(1, teams[0]?.points ?? 0);
  return (
    <div className="constructor-list">
      {teams.slice(0, 7).map((team, index) => (
        <div className="constructor-row" key={team.name}>
          <span className="constructor-rank">{String(index + 1).padStart(2, "0")}</span>
          <div className="constructor-meta">
            <div className="constructor-name"><TeamDot team={team.name} />{team.name}</div>
            <div className="constructor-bar-track">
              <div
                className="constructor-bar"
                style={{
                  "--bar-width": `${Math.max(3, (team.points / maxPoints) * 100)}%`,
                  "--team-color": colorFor(team.name),
                } as CSSProperties}
              />
            </div>
          </div>
          <span className="constructor-points">{team.points}</span>
        </div>
      ))}
    </div>
  );
}

function App() {
  const [initial, setInitial] = useState<InitialData | null>(null);
  const [season, setSeason] = useState<SeasonData | null>(null);
  const [activeView, setActiveView] = useState<View>("overview");
  const [currentRace, setCurrentRace] = useState<SimulatedRace | null>(null);
  const [raceType, setRaceType] = useState<RaceType>("race");
  const [seed, setSeed] = useState("");
  const [isSimulating, setIsSimulating] = useState(false);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/initial", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error("Could not load the season grid.");
        return response.json() as Promise<InitialData>;
      })
      .then(setInitial)
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        const message = error instanceof Error ? error.message : "Could not load the season grid.";
        setNotice(`${message} Start the API with: python3 backend/server.py`);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!notice) return;
    const timeout = window.setTimeout(() => setNotice(""), 4500);
    return () => window.clearTimeout(timeout);
  }, [notice]);

  const navigate = (view: View) => {
    setActiveView(view);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const openRace = (round: number) => {
    const race = season?.races.find((item) => item.round === round);
    if (!race) {
      setNotice("Simulate the season to reveal this race result.");
      return;
    }
    setCurrentRace(race);
    setRaceType("race");
    navigate("race");
  };

  const simulateSeason = async () => {
    if (!initial) return;
    const parsedSeed = seed.trim() === "" ? null : Number(seed);
    if (parsedSeed !== null && !Number.isSafeInteger(parsedSeed)) {
      setNotice("Enter a whole-number seed, or leave it blank for a random season.");
      return;
    }
    setIsSimulating(true);
    try {
      const response = await fetch("/api/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ year: initial.year, seed: parsedSeed }),
      });
      const payload: unknown = await response.json();
      if (!response.ok) {
        const message =
          typeof payload === "object" && payload !== null && "error" in payload
            ? String(payload.error)
            : "Simulation failed.";
        throw new Error(message);
      }
      setSeason(payload as SeasonData);
      setCurrentRace(null);
      navigate("overview");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Could not reach the simulator API.");
    } finally {
      setIsSimulating(false);
    }
  };

  const openView = (view: NavView) => navigate(view);
  const isSeasonView = SEASON_VIEWS.includes(activeView);
  const drivers = season?.standings.drivers ?? [];
  const constructors = season?.standings.constructors ?? [];
  const selectedResult = currentRace
    ? raceType === "sprint" && currentRace.sprint
      ? currentRace.sprint
      : currentRace.results
    : null;
  const uniqueWinners = new Set(season?.races.map((race) => race.winner).filter(Boolean)).size;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="Apex home">
          <span className="brand-mark">A</span>
          <span className="brand-name">APEX<span className="brand-period">.</span></span>
        </a>
        <div className="side-label">RACE CONTROL</div>
        <nav className="side-nav" aria-label="Main navigation">
          {NAV_ITEMS.map((item) => (
            <button
              className={`nav-link${activeView === item.view ? " active" : ""}`}
              key={item.view}
              onClick={() => openView(item.view)}
            >
              <span className="nav-icon">{item.icon}</span>{item.label}
            </button>
          ))}
        </nav>
        <div className="side-label side-label-gap">SIMULATION LAB</div>
        <nav className="side-nav" aria-label="Simulation lab">
          {LAB_NAV_ITEMS.map((item) => (
            <button
              className={`nav-link${activeView === item.view ? " active" : ""}`}
              key={item.view}
              onClick={() => openView(item.view)}
            >
              <span className="nav-icon">{item.icon}</span>{item.label}
            </button>
          ))}
        </nav>
        <div className="side-season">
          <div className="side-label">SEASON</div>
          <div className="season-year">{season?.year ?? initial?.year ?? 2026}</div>
          <div className="season-sub">
            <span className={`live-dot${season ? " is-live" : ""}`} />
            <span>{isSimulating ? "Season in progress" : season ? "Season complete" : initial ? "Ready to race" : "Loading grid"}</span>
          </div>
        </div>
        <div className="sidebar-bottom">
          <span className="footer-stripe" />
          <p>Every race tells a story.</p>
          <span className="version-label">F1 SEASON SIMULATOR <span>·</span> 01</span>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumbs">
            {isSeasonView ? "SEASON" : "SIMULATION LAB"} <span>/</span>{" "}
            <strong>{isSeasonView ? season?.year ?? initial?.year ?? 2026 : LAB_NAV_ITEMS.find((item) => item.view === activeView)?.label}</strong>
          </div>
          <div className="topbar-actions" hidden={!isSeasonView}>
            <label className="seed-control" htmlFor="seed-input">
              <span>SEED</span>
              <input
                id="seed-input"
                type="number"
                placeholder="Random"
                aria-label="Simulation seed"
                value={seed}
                onChange={(event) => setSeed(event.target.value)}
              />
            </label>
            <button className="button button-primary" disabled={isSimulating || !initial} onClick={simulateSeason}>
              <span className="button-icon">{isSimulating ? <span className="loading-ring" /> : "▶"}</span>
              {isSimulating ? "Running 24 rounds…" : season ? "Run it again" : "Simulate season"}
            </button>
          </div>
        </header>

        <div className="page-wrap">
          <section className={`view-panel${activeView === "overview" ? " active" : ""}`}>
            <div className="hero">
              <div className="hero-copy">
                <Eyebrow><span className="eyebrow-line" /> THE GRID IS SET <span className="eyebrow-year">{season?.year ?? initial?.year ?? 2026}</span></Eyebrow>
                <h1>One season.<br /><span>Twenty-four chances.</span></h1>
                <p className="hero-description">A full championship, simulated from lights out to the final flag. Strategy, weather, reliability and a little chaos decide who takes the crown.</p>
                <div className="hero-actions">
                  <button className="button button-primary button-large" disabled={isSimulating || !initial} onClick={simulateSeason}>
                    <span className="button-icon">{isSimulating ? <span className="loading-ring" /> : "▶"}</span>
                    {isSimulating ? "Simulating the season…" : "Simulate the season"}
                  </button>
                  <span className="hero-note">11 TEAMS <i>·</i> 22 DRIVERS <i>·</i> {initial?.calendar.length ?? 24} ROUNDS</span>
                </div>
              </div>
              <div className="hero-art" aria-hidden="true">
                <div className="hero-orbit orbit-one" /><div className="hero-orbit orbit-two" />
                <div className="hero-orbit orbit-three" />
                <div className="hero-car"><span className="car-wing" /><span className="car-body" /><span className="car-cockpit" /><span className="car-wheel wheel-a" /><span className="car-wheel wheel-b" /><span className="car-wheel wheel-c" /><span className="car-wheel wheel-d" /></div>
                <div className="hero-art-label">{season?.year ?? initial?.year ?? 2026} <span>WORLD CHAMPIONSHIP</span></div>
                <span className="hero-art-number">01</span>
              </div>
            </div>

            <div className="stat-grid">
              <article className="stat-card"><div className="stat-title">SEASON PROGRESS <span className="stat-symbol">◷</span></div><div className="stat-value">{season ? <>{season.rounds}<small> / {season.rounds}</small></> : <>—<small> / {initial?.calendar.length ?? 24}</small></>}</div><div className="stat-foot">{season ? "The chequered flag has fallen" : "Awaiting lights out"}</div></article>
              <article className="stat-card"><div className="stat-title">RACE WINNER <span className="stat-symbol">♛</span></div><div className="stat-value stat-name">{drivers[0]?.name ?? "—"}</div><div className="stat-foot">{drivers[0] ? `${drivers[0].team} · ${drivers[0].points} pts` : "The first flag is yours to wave"}</div></article>
              <article className="stat-card"><div className="stat-title">CONSTRUCTOR LEADER <span className="stat-symbol">▤</span></div><div className="stat-value stat-name">{constructors[0]?.name ?? "—"}</div><div className="stat-foot">{constructors[0] ? `${constructors[0].points} points · ${constructors[0].wins} wins` : "Every point counts"}</div></article>
              <article className="stat-card"><div className="stat-title">RACE WINNERS <span className="stat-symbol">✦</span></div><div className="stat-value">{season ? uniqueWinners : "—"}</div><div className="stat-foot">{season ? "Different race winners this season" : "How wide will the fight be?"}</div></article>
            </div>

            <SectionHeading eyebrow="THE CHAMPIONSHIP" title="Season at a glance" action="Full calendar" onAction={() => navigate("calendar")} />
            <div className="content-grid">
              <article className="panel standings-panel">
                <div className="panel-heading"><div><h3>Drivers' standings</h3><span className="panel-subtitle">A battle measured in points</span></div><button className="round-link" onClick={() => navigate("drivers")}>ALL DRIVERS ↗</button></div>
                {season ? (
                  <div className="table-wrap"><table><thead><tr><th>POS</th><th>DRIVER</th><th>TEAM</th><th>W</th><th className="align-right">PTS</th></tr></thead><tbody>
                    {drivers.slice(0, 8).map((driver, index) => <tr className={index < 3 ? `podium-${index + 1}` : ""} key={driver.name}><td className="position-cell">{String(index + 1).padStart(2, "0")}</td><td className="driver-cell">{driver.flag} &nbsp;{driver.name}</td><td className="team-cell"><TeamDot team={driver.team} />{driver.team}</td><td>{driver.wins}</td><td className="points-cell">{driver.points}</td></tr>)}
                  </tbody></table></div>
                ) : <EmptyState flag="🏁" title="Waiting for the first lap" description="Run a season to see the championship take shape." />}
              </article>
              <article className="panel constructor-panel">
                <div className="panel-heading"><div><h3>Constructors</h3><span className="panel-subtitle">The fight behind the drivers</span></div><button className="round-link" onClick={() => navigate("teams")}>FULL TABLE ↗</button></div>
                {season ? <ConstructorRows teams={constructors} /> : <EmptyState compact title="The team battle starts here" description={`${initial?.teams.length ?? 11} constructors on the grid`} />}
              </article>
            </div>

            <SectionHeading eyebrow="THE ROAD AHEAD" title="Race calendar" action="Explore all rounds" onAction={() => navigate("calendar")} />
            <div className="calendar-strip">
              {(initial?.calendar ?? []).slice(0, 12).map((round) => (
                <CalendarCard key={round.round} round={round} race={season?.races[round.round - 1]} onOpen={openRace} />
              ))}
            </div>
          </section>

          <section className={`view-panel${activeView === "calendar" ? " active" : ""}`}>
            <div className="section-heading page-heading"><div><Eyebrow>ROUND BY ROUND</Eyebrow><h1>Race calendar</h1><p className="section-description">Twenty-four circuits. One world championship.</p></div></div>
            <div className="calendar-grid">
              {(initial?.calendar ?? []).map((round) => (
                <CalendarCard key={round.round} round={round} race={season?.races[round.round - 1]} detailed onOpen={openRace} />
              ))}
            </div>
          </section>

          <section className={`view-panel${activeView === "drivers" ? " active" : ""}`}>
            <div className="section-heading page-heading"><div><Eyebrow>THE GRID</Eyebrow><h1>Drivers' championship</h1><p className="section-description">Every driver, every point, every position gained.</p></div></div>
            <article className="panel full-table-panel">
              <div className="panel-heading"><div><h3>Driver standings</h3><span className="panel-subtitle">{season ? `${drivers.length} drivers · ${season.rounds} rounds completed` : `${initial?.teams.reduce((total, team) => total + team.drivers.length, 0) ?? 22} drivers competing`}</span></div></div>
              {season ? <StandingsTable drivers={drivers} /> : <EmptyState flag="🏎" title="Championship standings will appear here" description="Simulate the season to see how the grid stacks up." />}
            </article>
          </section>

          <section className={`view-panel${activeView === "teams" ? " active" : ""}`}>
            <div className="section-heading page-heading"><div><Eyebrow>TEAM PERFORMANCE</Eyebrow><h1>Constructors</h1><p className="section-description">The points that bring a team to the top.</p></div></div>
            <article className="panel full-table-panel">
              <div className="panel-heading"><div><h3>Constructors' standings</h3><span className="panel-subtitle">{initial?.teams.length ?? 11} teams on the grid</span></div></div>
              {season ? (
                <div className="table-wrap"><table><thead><tr><th>POS</th><th>TEAM</th><th>DRIVERS</th><th>W</th><th className="align-right">PTS</th></tr></thead><tbody>
                  {constructors.map((team, index) => <tr className={index < 3 ? `podium-${index + 1}` : ""} key={team.name}><td className="position-cell">{String(index + 1).padStart(2, "0")}</td><td className="driver-cell"><TeamDot team={team.name} />{team.name}</td><td className="team-cell">{team.drivers.join(" / ")}</td><td>{team.wins}</td><td className="points-cell">{team.points}</td></tr>)}
                </tbody></table></div>
              ) : <EmptyState title="Every team starts on zero" description="Simulate a season to see who builds the best campaign." />}
            </article>
          </section>

          <section className={`view-panel${activeView === "race" ? " active" : ""}`}>
            {currentRace && selectedResult && (
              <>
                <div className="race-detail-top"><button className="back-button" onClick={() => navigate("calendar")}>← Back to calendar</button><span className="round-chip">ROUND {String(currentRace.round).padStart(2, "0")}</span></div>
                <div className="race-hero"><div><Eyebrow>RACE REPORT</Eyebrow><h1>{currentRace.name}</h1><p className="section-description">{currentRace.country} · {currentRace.laps} laps{currentRace.is_sprint ? " · Sprint weekend" : ""}</p></div><div className="race-winner-block"><span>{raceType === "sprint" ? "SPRINT WINNER" : "RACE WINNER"}</span><strong>{selectedResult.winner ?? "No classified finishers"}</strong></div></div>
                <div className="race-highlights">
                  <div className="highlight-card"><span>POLE POSITION</span><strong>{currentRace.pole ?? "—"}</strong></div>
                  <div className="highlight-card"><span>FASTEST LAP</span><strong>{selectedResult.fastest_lap || "—"}</strong></div>
                  <div className="highlight-card"><span>RACE CONDITIONS</span><strong>{selectedResult.wet ? selectedResult.extreme_wet ? "Heavy rain" : "Wet" : "Dry"}</strong></div>
                  <div className="highlight-card"><span>SAFETY CARS</span><strong>{selectedResult.safety_cars}</strong></div>
                </div>
                <article className="panel full-table-panel">
                  <div className="panel-heading"><div><h3>Grand Prix classification</h3><span className="panel-subtitle">Starting grid, race result and points</span></div>
                    {currentRace.sprint && <div className="segmented"><button className={raceType === "race" ? "selected" : ""} onClick={() => setRaceType("race")}>Grand Prix</button><button className={raceType === "sprint" ? "selected" : ""} onClick={() => setRaceType("sprint")}>Sprint</button></div>}
                  </div>
                  <div className="table-wrap"><table><thead><tr><th>POS</th><th>DRIVER</th><th>TEAM</th><th>GRID</th><th>STOPS</th><th>STATUS</th><th className="align-right">PTS</th></tr></thead><tbody>
                    {selectedResult.results.map((entry) => <tr key={entry.name}><td className="position-cell">{entry.position ? `P${String(entry.position).padStart(2, "0")}` : "—"}</td><td className="driver-cell">{entry.name}{entry.fastest_lap && <span title="Fastest lap"> ✦</span>}</td><td className="team-cell"><TeamDot team={entry.team} />{entry.team}</td><td>{entry.grid}</td><td>{entry.pit_stops}</td><td className={entry.status === "DNF" ? "status-dnf" : "status-finished"}>{entry.status}{entry.laps < currentRace.laps && entry.status !== "DNF" && ` · ${currentRace.laps - entry.laps}L`}</td><td className="points-cell">{entry.points}</td></tr>)}
                  </tbody></table></div>
                </article>
              </>
            )}
          </section>
          <LabPages activeView={activeView} />
          {notice && <div className="notice visible" role="status" aria-live="polite">{notice}</div>}
        </div>
      </main>
    </div>
  );
}

export default App;
