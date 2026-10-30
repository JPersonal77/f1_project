import { useCallback, useEffect, useMemo, useState } from "react";
import type { CSSProperties, FormEvent, ReactNode } from "react";
import { colorFor } from "./theme";

export type LabView = "seasons" | "weekend" | "until" | "history" | "predict" | "academies";

interface Meta {
  drivers: Array<{ name: string; team: string }>;
  prospects: Array<{ name: string; series: string }>;
  teams: string[];
  calendar: Array<{ round: number; name: string; country: string; is_sprint: boolean }>;
}

interface Tally { name: string; count: number }
interface Champion { name: string; team: string; points: number; wins: number }
interface StandingDriver { name: string; team: string; points: number; wins: number }

interface MultiResult {
  seed: number | null;
  seasons: Array<{
    year: number;
    champion: Champion;
    runner_up: Champion;
    constructor_champion: { name: string; points: number; wins: number };
    winners: number;
    news: string[];
  }>;
  driver_titles: Tally[];
  constructor_titles: Tally[];
}

interface RaceRow {
  name: string; team: string; position: number | null; grid: number; points: number;
  status: string; fastest_lap: boolean; time: number; best_lap: number; laps: number;
  pit_stops: number; strategy: string[];
}
interface RaceOut { winner: string | null; fastest_lap: string | null; wet: boolean; extreme_wet: boolean; safety_cars: number; results: RaceRow[] }
interface QualiOut {
  wet: boolean;
  grid: Array<{ position: number; name: string; team: string }>;
  sessions: Record<string, Array<{ name: string; team: string; time: number }>>;
  eliminated_q1: string[];
  eliminated_q2: string[];
}
interface WeekendResult {
  round: number;
  track: {
    name: string; country: string; laps: number; is_sprint: boolean; circuit_length_km: number;
    turn_count: number; track_type: string; overtaking_difficulty: number; wet_chance: number;
    safety_car_chance: number; tyre_selection: string[];
  };
  practice: Array<Array<{ name: string; team: string; time: number; laps: number; position: number }>>;
  sprint_qualifying: QualiOut | null;
  sprint: RaceOut | null;
  qualifying: QualiOut;
  race: RaceOut;
  weekend_points: Array<{ name: string; team: string; points: number }>;
}

interface UntilResult {
  condition: string;
  target: string | null;
  met: boolean;
  reason: string;
  message: string;
  seasons_run: number;
  final_year: number;
  truncated: boolean;
  rows: Array<{ year: number; champion: string; champion_team: string; constructor_champion: string; winners: number; margin: number }>;
  final_standings: { drivers: StandingDriver[] };
}

interface HistoryResult {
  seasons: number;
  notes: Array<{ year: number; text: string }>;
  driver_titles: Tally[];
  constructor_titles: Tally[];
  records: Array<{ label: string; value: number; extra: string; year: number }>;
}

interface PredictRow {
  name: string; team: string; win_pct: number; podium_pct: number; points_pct: number;
  pole_pct: number; dnf_pct: number; avg_position: number;
}
interface PredictResult {
  round: number;
  trials: number;
  track: { name: string; country: string; is_sprint: boolean };
  likely_pole: { name: string; team: string; pct: number } | null;
  likely_winner: { name: string; team: string; pct: number } | null;
  rows: PredictRow[];
}

interface AcademyResult {
  policies: Array<{ team: string; preferred_academies: string; junior_appetite: string; junior_probability: number }>;
  active: Array<{ name: string; academy: string }>;
  prospects: Array<{
    name: string; series: string; team: string; nationality: string; flag: string; age: number;
    f1_potential: number; pace: number; academy: string | null;
  }>;
}

async function request<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(path, body === undefined ? undefined : {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const message = typeof payload === "object" && payload !== null && "error" in payload
      ? String(payload.error)
      : "Request failed.";
    throw new Error(message);
  }
  return payload as T;
}

function useRequest<T>(path: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const run = useCallback(async (body: unknown) => {
    setLoading(true);
    setError("");
    try {
      setData(await request<T>(path, body));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not reach the simulator API.");
    } finally {
      setLoading(false);
    }
  }, [path]);
  return { data, error, loading, run };
}

const lapTime = (seconds: number) => {
  const minutes = Math.floor(seconds / 60);
  return `${minutes}:${(seconds - minutes * 60).toFixed(3).padStart(6, "0")}`;
};

const raceTime = (seconds: number) => {
  const hours = Math.floor(seconds / 3600);
  const rest = seconds - hours * 3600;
  const minutes = Math.floor(rest / 60);
  return `${hours}:${String(minutes).padStart(2, "0")}:${(rest - minutes * 60).toFixed(3).padStart(6, "0")}`;
};

const humanize = (value: string) => value.replace(/_/g, " ");

function parseSeed(text: string): { seed: number | null; error: string } {
  if (text.trim() === "") return { seed: null, error: "" };
  const value = Number(text);
  return Number.isSafeInteger(value)
    ? { seed: value, error: "" }
    : { seed: null, error: "Seed must be a whole number, or blank for random." };
}

function TeamDot({ team }: { team: string }) {
  return <span className="team-dot" style={{ "--team-color": colorFor(team) } as CSSProperties} />;
}

function LabHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return (
    <div className="lab-header">
      <div className="eyebrow"><span className="eyebrow-line" /> {eyebrow}</div>
      <h1>{title}</h1>
      <p className="section-description">{description}</p>
    </div>
  );
}

function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {hint && <small>{hint}</small>}
    </label>
  );
}

function NumberField({ label, value, onChange, min, max, hint }: {
  label: string; value: string; onChange: (value: string) => void; min: number; max: number; hint?: string;
}) {
  return (
    <Field label={label} hint={hint}>
      <input type="number" min={min} max={max} value={value} onChange={(event) => onChange(event.target.value)} />
    </Field>
  );
}

function SeedField({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <Field label="SEED" hint="Blank = random. Same seed, same result.">
      <input type="number" placeholder="Random" value={value} onChange={(event) => onChange(event.target.value)} />
    </Field>
  );
}

function RunForm({ onSubmit, loading, label, children }: {
  onSubmit: () => void; loading: boolean; label: string; children: ReactNode;
}) {
  const submit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit();
  };
  return (
    <form className="lab-form panel" onSubmit={submit}>
      <div className="field-grid">{children}</div>
      <button className="button button-primary" type="submit" disabled={loading}>
        <span className="button-icon">{loading ? <span className="loading-ring" /> : "▶"}</span>
        {loading ? "Simulating…" : label}
      </button>
    </form>
  );
}

function ErrorBanner({ message }: { message: string }) {
  return message ? <div className="lab-error" role="alert">{message}</div> : null;
}

function Bar({ value, max, color }: { value: number; max: number; color?: string }) {
  const width = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <span className="bar-track">
      <span className="bar-fill" style={{ width: `${width}%`, background: color ?? "var(--red)" }} />
    </span>
  );
}

function TallyList({ title, rows }: { title: string; rows: Tally[] }) {
  const max = rows[0]?.count ?? 0;
  return (
    <article className="panel">
      <div className="panel-heading"><h3>{title}</h3></div>
      {rows.length === 0 ? <p className="lab-muted">None.</p> : (
        <ul className="tally-list">
          {rows.slice(0, 8).map((row) => (
            <li key={row.name}>
              <span className="tally-name">{row.name}</span>
              <Bar value={row.count} max={max} />
              <strong>{row.count}</strong>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

function Stat({ label, value }: { label: string; value: ReactNode }) {
  return <div className="highlight-card"><span>{label}</span><strong>{value}</strong></div>;
}

function SeasonsPage() {
  const [seasons, setSeasons] = useState("10");
  const [startYear, setStartYear] = useState("2026");
  const [seed, setSeed] = useState("");
  const [localError, setLocalError] = useState("");
  const { data, error, loading, run } = useRequest<MultiResult>("/api/seasons");

  const submit = () => {
    const parsed = parseSeed(seed);
    setLocalError(parsed.error);
    if (!parsed.error) void run({ seasons: Number(seasons), start_year: Number(startYear), seed: parsed.seed });
  };

  return (
    <>
      <LabHeader eyebrow="MULTI-SEASON" title="Run many seasons in a row"
        description="Back-to-back championships with off-season transfers, retirements, academy promotions and regulation resets every four years." />
      <RunForm onSubmit={submit} loading={loading} label="Run seasons">
        <NumberField label="SEASONS" value={seasons} onChange={setSeasons} min={1} max={200} hint="1–200" />
        <NumberField label="START YEAR" value={startYear} onChange={setStartYear} min={2026} max={2100} />
        <SeedField value={seed} onChange={setSeed} />
      </RunForm>
      <ErrorBanner message={localError || error} />
      {data && (
        <>
          <div className="lab-grid two">
            <TallyList title="Drivers' titles" rows={data.driver_titles} />
            <TallyList title="Constructors' titles" rows={data.constructor_titles} />
          </div>
          <article className="panel full-table-panel">
            <div className="panel-heading"><div><h3>Season by season</h3><span className="panel-subtitle">Open a row for that off-season's news</span></div></div>
            <div className="table-wrap"><table>
              <thead><tr><th>YEAR</th><th>CHAMPION</th><th>RUNNER-UP</th><th>CONSTRUCTORS</th><th>WINNERS</th><th className="align-right">PTS</th></tr></thead>
              <tbody>
                {data.seasons.map((entry) => (
                  <tr key={entry.year}>
                    <td className="position-cell">{entry.year}</td>
                    <td className="driver-cell"><TeamDot team={entry.champion.team} />{entry.champion.name}</td>
                    <td>{entry.runner_up.name}</td>
                    <td className="team-cell"><TeamDot team={entry.constructor_champion.name} />{entry.constructor_champion.name}</td>
                    <td>{entry.winners}</td>
                    <td className="points-cell">{entry.champion.points}</td>
                  </tr>
                ))}
              </tbody>
            </table></div>
          </article>
          <article className="panel">
            <div className="panel-heading"><h3>Off-season news</h3></div>
            {data.seasons.filter((entry) => entry.news.length > 0).map((entry) => (
              <details className="news-block" key={entry.year}>
                <summary>After {entry.year} <span>{entry.news.length} stories</span></summary>
                <ul>{entry.news.map((line, index) => <li key={index}>{line}</li>)}</ul>
              </details>
            ))}
          </article>
        </>
      )}
    </>
  );
}

function QualiTable({ quali, title }: { quali: QualiOut; title: string }) {
  const sessions = Object.entries(quali.sessions);
  return (
    <article className="panel">
      <div className="panel-heading"><div><h3>{title}</h3><span className="panel-subtitle">{quali.wet ? "Wet session" : "Dry session"}</span></div></div>
      <div className="lab-grid sessions">
        {sessions.map(([name, rows]) => (
          <div key={name}>
            <div className="mini-title">{name}</div>
            <ol className="mini-list">
              {rows.map((row) => <li key={row.name}><TeamDot team={row.team} /><span>{row.name}</span><em>{lapTime(row.time)}</em></li>)}
            </ol>
          </div>
        ))}
      </div>
      <div className="mini-title grid-title">STARTING GRID</div>
      <ol className="grid-list">
        {quali.grid.map((slot) => <li key={slot.name}><b>{slot.position}</b><TeamDot team={slot.team} />{slot.name}</li>)}
      </ol>
    </article>
  );
}

function RaceTable({ race, title }: { race: RaceOut; title: string }) {
  return (
    <article className="panel full-table-panel">
      <div className="panel-heading"><div><h3>{title}</h3>
        <span className="panel-subtitle">{race.wet ? (race.extreme_wet ? "Heavy rain" : "Wet") : "Dry"} · {race.safety_cars} safety car(s) · Fastest lap {race.fastest_lap ?? "—"}</span></div></div>
      <div className="table-wrap"><table>
        <thead><tr><th>POS</th><th>DRIVER</th><th>TEAM</th><th>GRID</th><th>STRATEGY</th><th>TIME</th><th>STATUS</th><th className="align-right">PTS</th></tr></thead>
        <tbody>
          {race.results.map((row) => (
            <tr key={row.name}>
              <td className="position-cell">{row.position ? `P${String(row.position).padStart(2, "0")}` : "—"}</td>
              <td className="driver-cell">{row.name}{row.fastest_lap && <span title="Fastest lap"> ✦</span>}</td>
              <td className="team-cell"><TeamDot team={row.team} />{row.team}</td>
              <td>{row.grid}</td>
              <td>{row.strategy.join(" › ") || "—"}</td>
              <td>{row.position ? raceTime(row.time) : "—"}</td>
              <td className={row.status === "DNF" ? "status-dnf" : "status-finished"}>{row.status}</td>
              <td className="points-cell">{row.points}</td>
            </tr>
          ))}
        </tbody>
      </table></div>
    </article>
  );
}

function WeekendPage({ meta }: { meta: Meta | null }) {
  const [round, setRound] = useState("1");
  const [seed, setSeed] = useState("");
  const [tab, setTab] = useState<"race" | "sprint" | "qualifying" | "practice" | "points">("race");
  const [localError, setLocalError] = useState("");
  const { data, error, loading, run } = useRequest<WeekendResult>("/api/round");

  const submit = () => {
    const parsed = parseSeed(seed);
    setLocalError(parsed.error);
    if (parsed.error) return;
    setTab("race");
    void run({ round: Number(round), seed: parsed.seed });
  };

  const tabs: Array<[typeof tab, string]> = [["race", "Race"]];
  if (data?.sprint) tabs.push(["sprint", "Sprint"]);
  tabs.push(["qualifying", "Qualifying"], ["practice", "Practice"], ["points", "Weekend points"]);

  return (
    <>
      <LabHeader eyebrow="SINGLE ROUND" title="Run one race weekend"
        description="Practice, qualifying, the sprint (where there is one) and the Grand Prix for any round, on the 2026 grid." />
      <RunForm onSubmit={submit} loading={loading} label="Run weekend">
        <Field label="ROUND">
          <select value={round} onChange={(event) => setRound(event.target.value)}>
            {(meta?.calendar ?? []).map((item) => (
              <option key={item.round} value={item.round}>{item.round}. {item.name}{item.is_sprint ? " (sprint)" : ""}</option>
            ))}
          </select>
        </Field>
        <SeedField value={seed} onChange={setSeed} />
      </RunForm>
      <ErrorBanner message={localError || error} />
      {data && (
        <>
          <div className="race-highlights">
            <Stat label="CIRCUIT" value={data.track.name} />
            <Stat label="LAPS · LENGTH" value={`${data.track.laps} · ${data.track.circuit_length_km} km`} />
            <Stat label="TYPE" value={humanize(data.track.track_type)} />
            <Stat label="TYRES" value={data.track.tyre_selection.join(" / ")} />
            <Stat label="WET CHANCE" value={`${Math.round(data.track.wet_chance * 100)}%`} />
            <Stat label="SAFETY CAR CHANCE" value={`${Math.round(data.track.safety_car_chance * 100)}%`} />
            <Stat label="POLE" value={data.qualifying.grid[0]?.name ?? "—"} />
            <Stat label="WINNER" value={data.race.winner ?? "—"} />
          </div>
          <div className="segmented lab-tabs">
            {tabs.map(([key, label]) => (
              <button key={key} className={tab === key ? "selected" : ""} onClick={() => setTab(key)}>{label}</button>
            ))}
          </div>
          {tab === "race" && <RaceTable race={data.race} title="Grand Prix" />}
          {tab === "sprint" && data.sprint && data.sprint_qualifying && (
            <>
              <QualiTable quali={data.sprint_qualifying} title="Sprint qualifying" />
              <RaceTable race={data.sprint} title="Sprint race" />
            </>
          )}
          {tab === "qualifying" && <QualiTable quali={data.qualifying} title="Qualifying" />}
          {tab === "practice" && (
            <div className="lab-grid sessions">
              {data.practice.map((session, index) => (
                <article className="panel" key={index}>
                  <div className="panel-heading"><h3>Practice {index + 1}</h3></div>
                  <ol className="mini-list">
                    {session.map((row) => <li key={row.name}><TeamDot team={row.team} /><span>{row.name}</span><em>{lapTime(row.time)}</em></li>)}
                  </ol>
                </article>
              ))}
            </div>
          )}
          {tab === "points" && (
            <article className="panel">
              <div className="panel-heading"><h3>Points scored this weekend</h3></div>
              <ol className="mini-list">
                {data.weekend_points.map((row) => <li key={row.name}><TeamDot team={row.team} /><span>{row.name}</span><em>{row.points}</em></li>)}
              </ol>
            </article>
          )}
        </>
      )}
    </>
  );
}

const UNTIL_OPTIONS: Array<[string, string]> = [
  ["champion", "A driver wins the championship"],
  ["constructor", "A team wins the constructors' title"],
  ["win", "A driver wins a race"],
  ["tiebreak", "Title decided on a points tie"],
  ["winners", "A season has more than N different winners"],
];

function UntilPage({ meta }: { meta: Meta | null }) {
  const [condition, setCondition] = useState("champion");
  const [target, setTarget] = useState("");
  const [threshold, setThreshold] = useState("10");
  const [maxSeasons, setMaxSeasons] = useState("1000");
  const [startYear, setStartYear] = useState("2026");
  const [seed, setSeed] = useState("");
  const [localError, setLocalError] = useState("");
  const { data, error, loading, run } = useRequest<UntilResult>("/api/until");

  const submit = () => {
    const parsed = parseSeed(seed);
    setLocalError(parsed.error);
    if (parsed.error) return;
    void run({
      condition,
      target: target.trim() || null,
      threshold: Number(threshold),
      max_seasons: Number(maxSeasons),
      start_year: Number(startYear),
      seed: parsed.seed,
    });
  };

  const needsDriver = condition === "champion" || condition === "win";
  const needsTeam = condition === "constructor";
  const suggestions = useMemo(() => {
    if (needsTeam) return meta?.teams ?? [];
    return [...(meta?.drivers.map((d) => d.name) ?? []), ...(meta?.prospects.map((p) => p.name) ?? [])];
  }, [meta, needsTeam]);

  return (
    <>
      <LabHeader eyebrow="UNTIL IT HAPPENS" title="Simulate until a condition is met"
        description="Keep running seasons until a driver or team achieves a goal. F2/F3 prospects work too — if they are never promoted the search stops at the cap." />
      <RunForm onSubmit={submit} loading={loading} label="Search">
        <Field label="CONDITION">
          <select value={condition} onChange={(event) => setCondition(event.target.value)}>
            {UNTIL_OPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </Field>
        {(needsDriver || needsTeam) && (
          <Field label={needsTeam ? "TEAM" : "DRIVER"} hint={needsTeam ? undefined : "Includes F2/F3 prospects"}>
            <input list="until-suggestions" value={target} onChange={(event) => setTarget(event.target.value)}
              placeholder={needsTeam ? "Mercedes" : "Kimi Antonelli"} maxLength={60} />
            <datalist id="until-suggestions">{suggestions.map((name) => <option key={name} value={name} />)}</datalist>
          </Field>
        )}
        {condition === "winners" && <NumberField label="MORE THAN N WINNERS" value={threshold} onChange={setThreshold} min={1} max={100} />}
        <NumberField label="MAX SEASONS" value={maxSeasons} onChange={setMaxSeasons} min={1} max={5000} hint="1–5000" />
        <NumberField label="START YEAR" value={startYear} onChange={setStartYear} min={2026} max={2100} />
        <SeedField value={seed} onChange={setSeed} />
      </RunForm>
      <ErrorBanner message={localError || error} />
      {data && (
        <>
          <div className={`lab-result ${data.met ? "ok" : "stop"}`}>
            <strong>{data.met ? "Condition met" : "Stopped"}</strong>
            <span>{data.message}</span>
          </div>
          <div className="race-highlights">
            <Stat label="SEASONS RUN" value={data.seasons_run} />
            <Stat label="FINAL YEAR" value={data.final_year} />
            <Stat label="LAST CHAMPION" value={data.rows[data.rows.length - 1]?.champion ?? "—"} />
            <Stat label="LAST SEASON WINNERS" value={data.rows[data.rows.length - 1]?.winners ?? "—"} />
          </div>
          <article className="panel full-table-panel">
            <div className="panel-heading"><div><h3>Champions along the way</h3>
              {data.truncated && <span className="panel-subtitle">Showing the last 500 seasons</span>}</div></div>
            <div className="table-wrap tall"><table>
              <thead><tr><th>YEAR</th><th>DRIVER CHAMPION</th><th>CONSTRUCTORS</th><th>WINNERS</th><th className="align-right">MARGIN</th></tr></thead>
              <tbody>
                {[...data.rows].reverse().map((row) => (
                  <tr key={row.year}>
                    <td className="position-cell">{row.year}</td>
                    <td className="driver-cell"><TeamDot team={row.champion_team} />{row.champion}</td>
                    <td className="team-cell"><TeamDot team={row.constructor_champion} />{row.constructor_champion}</td>
                    <td>{row.winners}</td>
                    <td className="points-cell">{row.margin}</td>
                  </tr>
                ))}
              </tbody>
            </table></div>
          </article>
        </>
      )}
    </>
  );
}

function HistoryPage() {
  const [seasons, setSeasons] = useState("100");
  const [startYear, setStartYear] = useState("2026");
  const [seed, setSeed] = useState("");
  const [localError, setLocalError] = useState("");
  const { data, error, loading, run } = useRequest<HistoryResult>("/api/history");

  const submit = () => {
    const parsed = parseSeed(seed);
    setLocalError(parsed.error);
    if (!parsed.error) void run({ seasons: Number(seasons), start_year: Number(startYear), seed: parsed.seed });
  };

  return (
    <>
      <LabHeader eyebrow="HISTORY" title="Write an era of the sport"
        description="Simulate decades of racing and read the story: maiden titles, dynasties, droughts, lockouts, records and retirements." />
      <RunForm onSubmit={submit} loading={loading} label="Simulate history">
        <NumberField label="SEASONS" value={seasons} onChange={setSeasons} min={1} max={1000} hint="1–1000" />
        <NumberField label="START YEAR" value={startYear} onChange={setStartYear} min={2026} max={2100} />
        <SeedField value={seed} onChange={setSeed} />
      </RunForm>
      <ErrorBanner message={localError || error} />
      {data && (
        <>
          <div className="lab-grid two">
            <TallyList title="Most drivers' titles" rows={data.driver_titles} />
            <TallyList title="Most constructors' titles" rows={data.constructor_titles} />
          </div>
          <article className="panel">
            <div className="panel-heading"><h3>Records</h3></div>
            <div className="record-grid">
              {data.records.map((record) => (
                <div className="record" key={record.label}>
                  <span>{humanize(record.label).toUpperCase()}</span>
                  <strong>{record.value}</strong>
                  <em>{record.extra} · {record.year}</em>
                </div>
              ))}
            </div>
          </article>
          <article className="panel">
            <div className="panel-heading"><div><h3>Timeline</h3><span className="panel-subtitle">{data.notes.length} notable moments</span></div></div>
            <ol className="timeline">
              {data.notes.map((note, index) => <li key={index}><b>{note.year}</b><span>{note.text}</span></li>)}
            </ol>
          </article>
        </>
      )}
    </>
  );
}

function PredictPage({ meta }: { meta: Meta | null }) {
  const [round, setRound] = useState("1");
  const [trials, setTrials] = useState("500");
  const [seed, setSeed] = useState("");
  const [localError, setLocalError] = useState("");
  const { data, error, loading, run } = useRequest<PredictResult>("/api/predict");

  const submit = () => {
    const parsed = parseSeed(seed);
    setLocalError(parsed.error);
    if (!parsed.error) void run({ round: Number(round), trials: Number(trials), seed: parsed.seed });
  };

  const maxWin = Math.max(1, ...(data?.rows.map((row) => row.win_pct) ?? []));

  return (
    <>
      <LabHeader eyebrow="PREDICTOR" title="Predict a Grand Prix"
        description="Run one round hundreds of times and see each driver's chance of pole, a win, a podium and points." />
      <RunForm onSubmit={submit} loading={loading} label="Run predictions">
        <Field label="ROUND">
          <select value={round} onChange={(event) => setRound(event.target.value)}>
            {(meta?.calendar ?? []).map((item) => <option key={item.round} value={item.round}>{item.round}. {item.name}</option>)}
          </select>
        </Field>
        <NumberField label="TRIALS" value={trials} onChange={setTrials} min={1} max={5000} hint="1–5000" />
        <SeedField value={seed} onChange={setSeed} />
      </RunForm>
      <ErrorBanner message={localError || error} />
      {data && (
        <>
          <div className="race-highlights">
            <Stat label="CIRCUIT" value={data.track.name} />
            <Stat label="TRIALS" value={data.trials} />
            <Stat label="LIKELY POLE" value={data.likely_pole ? `${data.likely_pole.name} (${data.likely_pole.pct}%)` : "—"} />
            <Stat label="LIKELY WINNER" value={data.likely_winner ? `${data.likely_winner.name} (${data.likely_winner.pct}%)` : "—"} />
          </div>
          <article className="panel full-table-panel">
            <div className="panel-heading"><div><h3>Probabilities</h3><span className="panel-subtitle">Sorted by average finishing position</span></div></div>
            <div className="table-wrap"><table>
              <thead><tr><th>#</th><th>DRIVER</th><th>TEAM</th><th>WIN</th><th>PODIUM</th><th>POINTS</th><th>POLE</th><th>DNF</th><th className="align-right">AVG POS</th></tr></thead>
              <tbody>
                {data.rows.map((row, index) => (
                  <tr key={row.name}>
                    <td className="position-cell">{index + 1}</td>
                    <td className="driver-cell">{row.name}</td>
                    <td className="team-cell"><TeamDot team={row.team} />{row.team}</td>
                    <td><div className="pct-cell"><Bar value={row.win_pct} max={maxWin} color={colorFor(row.team)} />{row.win_pct}%</div></td>
                    <td>{row.podium_pct}%</td>
                    <td>{row.points_pct}%</td>
                    <td>{row.pole_pct}%</td>
                    <td className={row.dnf_pct >= 10 ? "status-dnf" : undefined}>{row.dnf_pct}%</td>
                    <td className="points-cell">{row.avg_position}</td>
                  </tr>
                ))}
              </tbody>
            </table></div>
          </article>
        </>
      )}
    </>
  );
}

function AcademiesPage() {
  const [data, setData] = useState<AcademyResult | null>(null);
  const [error, setError] = useState("");
  const [series, setSeries] = useState("all");

  useEffect(() => {
    request<AcademyResult>("/api/academies").then(setData).catch((caught: unknown) =>
      setError(caught instanceof Error ? caught.message : "Could not load academies."));
  }, []);

  const prospects = (data?.prospects ?? []).filter((item) => series === "all" || item.series === series);

  return (
    <>
      <LabHeader eyebrow="ACADEMIES" title="Junior programmes and prospects"
        description="Which teams favour their own academies, how likely they are to promote juniors, and the F2/F3 talent waiting in the wings." />
      <ErrorBanner message={error} />
      {data && (
        <>
          <article className="panel full-table-panel">
            <div className="panel-heading"><h3>Team academy policies</h3></div>
            <div className="table-wrap"><table>
              <thead><tr><th>TEAM</th><th>PREFERRED ACADEMY</th><th>JUNIOR APPETITE</th><th className="align-right">PROMOTION CHANCE</th></tr></thead>
              <tbody>
                {data.policies.map((policy) => (
                  <tr key={policy.team}>
                    <td className="team-cell"><TeamDot team={policy.team} />{policy.team}</td>
                    <td>{policy.preferred_academies || "—"}</td>
                    <td>{humanize(policy.junior_appetite)}</td>
                    <td className="points-cell">{(policy.junior_probability * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table></div>
          </article>
          <article className="panel full-table-panel">
            <div className="panel-heading"><div><h3>Prospects</h3><span className="panel-subtitle">{prospects.length} drivers</span></div>
              <div className="segmented">
                {["all", "F2", "F3"].map((value) => (
                  <button key={value} className={series === value ? "selected" : ""} onClick={() => setSeries(value)}>{value === "all" ? "All" : value}</button>
                ))}
              </div>
            </div>
            <div className="table-wrap tall"><table>
              <thead><tr><th>DRIVER</th><th>SERIES</th><th>TEAM</th><th>AGE</th><th>ACADEMY</th><th>PACE</th><th className="align-right">POTENTIAL</th></tr></thead>
              <tbody>
                {prospects.map((item) => (
                  <tr key={item.name}>
                    <td className="driver-cell">{item.flag} {item.name}</td>
                    <td>{item.series}</td>
                    <td>{item.team}</td>
                    <td>{item.age}</td>
                    <td>{item.academy ?? "—"}</td>
                    <td>{item.pace}</td>
                    <td className="points-cell">{item.f1_potential}</td>
                  </tr>
                ))}
              </tbody>
            </table></div>
          </article>
        </>
      )}
    </>
  );
}

export function LabPages({ activeView }: { activeView: string }) {
  const [meta, setMeta] = useState<Meta | null>(null);

  useEffect(() => {
    request<Meta>("/api/meta").then(setMeta).catch(() => setMeta(null));
  }, []);

  const panel = (view: LabView, content: ReactNode) => (
    <section className={`view-panel${activeView === view ? " active" : ""}`}>{content}</section>
  );

  return (
    <>
      {panel("seasons", <SeasonsPage />)}
      {panel("weekend", <WeekendPage meta={meta} />)}
      {panel("until", <UntilPage meta={meta} />)}
      {panel("history", <HistoryPage />)}
      {panel("predict", <PredictPage meta={meta} />)}
      {panel("academies", <AcademiesPage />)}
    </>
  );
}
