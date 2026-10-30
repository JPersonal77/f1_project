"""Simulation services behind the web API. Each function mirrors a CLI mode in main.py."""

import contextlib
import io
import random
import re
import sys
import threading
from argparse import Namespace
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import main as cli
from f1sim import simulation as sim
from f1sim.data import (
    ACTIVE_ACADEMIES,
    F1_PROSPECTS,
    academy_policy_report,
    build_2026_calendar,
    build_2026_grid,
)
from f1sim.models import NATIONALITY_FLAGS
from f1sim.season import Season
from f1sim.transfers import REGULATION_CYCLE_SEASONS, run_offseason

UNTIL_CONDITIONS = ("champion", "constructor", "win", "tiebreak", "winners")
MAX_ROW_HISTORY = 500

# History mode prints its events, so its stdout capture must not overlap another capture.
_CAPTURE_LOCK = threading.Lock()


def _driver_data(driver):
    return {
        "name": driver.name,
        "number": driver.number,
        "nationality": driver.nationality,
        "flag": driver.flag,
        "team": driver.team,
        "age": driver.age,
        "pace": driver.pace,
        "overall": round(driver.overall, 1),
    }


def _standings(teams):
    drivers = sorted(
        (driver for team in teams for driver in team.drivers),
        key=lambda driver: (-driver.season_points, -driver.season_wins, driver.name),
    )
    constructors = sorted(
        teams,
        key=lambda team: (-team.season_points, -team.season_wins, team.name),
    )
    return {
        "drivers": [
            {
                **_driver_data(driver),
                "points": round(driver.season_points, 1),
                "wins": driver.season_wins,
                "podiums": driver.season_podiums,
                "poles": driver.season_poles,
                "dnfs": driver.season_dnfs,
            }
            for driver in drivers
        ],
        "constructors": [
            {
                "name": team.name,
                "full_name": team.full_name,
                "points": round(team.season_points, 1),
                "wins": team.season_wins,
                "car_performance": team.car_performance,
                "drivers": [driver.name for driver in team.drivers],
            }
            for team in constructors
        ],
    }


def _race_result(race, points, driver_teams):
    def entry(name, position, status):
        return {
            "name": name,
            "team": driver_teams[name],
            "position": position,
            "grid": race.grid.index(name) + 1,
            "points": points.get(name, 0),
            "status": status,
            "fastest_lap": position is not None and name == race.fastest_lap,
            "time": round(race.race_times.get(name, 0), 3),
            "best_lap": round(race.fastest_lap_times.get(name, 0), 3),
            "laps": race.laps_completed.get(name, 0),
            "pit_stops": race.pit_stops.get(name, 0),
            "strategy": race.tyre_strategy.get(name, []),
        }

    classified = [entry(name, position, "Finished") for position, name in enumerate(race.classified, start=1)]
    retired = [entry(name, None, "DNF") for name in race.dnfs]
    return {
        "winner": race.classified[0] if race.classified else None,
        "fastest_lap": race.fastest_lap,
        "wet": race.wet,
        "extreme_wet": race.extreme_wet,
        "safety_cars": race.safety_cars,
        "results": classified + retired,
    }


def _run_season(year, teams, calendar, seed):
    season = Season(year, teams, calendar, seed=seed, quiet=True)
    for round_number, track in enumerate(calendar, start=1):
        season.run_weekend(round_number, track)
    return season


def _winners(season):
    winners = set()
    for entry in season.race_log:
        for key in ("race", "sprint_race"):
            result = entry[key]
            if result and result.classified:
                winners.add(result.classified[0])
    return winners


def _champion(driver):
    return {
        "name": driver.name,
        "team": driver.team,
        "points": round(driver.season_points, 1),
        "wins": driver.season_wins,
    }


def _tally(counter):
    return [{"name": name, "count": count} for name, count in counter.most_common()]


def initial_data():
    teams = build_2026_grid()
    return {
        "year": 2026,
        "teams": [
            {
                "name": team.name,
                "full_name": team.full_name,
                "drivers": [_driver_data(driver) for driver in team.drivers],
            }
            for team in teams
        ],
        "calendar": _calendar_data(),
    }


def _calendar_data():
    return [
        {
            "round": round_number,
            "name": track.name,
            "country": track.country,
            "laps": track.laps,
            "is_sprint": track.is_sprint,
        }
        for round_number, track in enumerate(build_2026_calendar(), start=1)
    ]


def meta():
    teams = build_2026_grid()
    return {
        "drivers": [{"name": d.name, "team": t.name} for t in teams for d in t.drivers],
        "prospects": [{"name": name, "series": profile["series"]} for name, profile in F1_PROSPECTS.items()],
        "teams": [team.name for team in teams],
        "calendar": _calendar_data(),
    }


def academies():
    prospects = [
        {
            "name": name,
            "series": profile["series"],
            "team": profile["team"],
            "nationality": profile["nationality"],
            "flag": NATIONALITY_FLAGS.get(profile["nationality"], "🏳️"),
            "age": profile["age"],
            "f1_potential": profile["f1_potential"],
            "pace": profile["pace"],
            "academy": profile.get("academy"),
        }
        for name, profile in F1_PROSPECTS.items()
    ]
    prospects.sort(key=lambda prospect: (-prospect["f1_potential"], prospect["name"]))
    return {
        "policies": academy_policy_report(),
        "active": [{"name": name, "academy": academy} for name, academy in ACTIVE_ACADEMIES.items()],
        "prospects": prospects,
    }


def simulate_season(year=2026, seed=None):
    teams = build_2026_grid()
    calendar = build_2026_calendar()
    season = _run_season(year, teams, calendar, seed)
    driver_teams = {driver.name: team.name for team in teams for driver in team.drivers}

    races = []
    for weekend in season.race_log:
        race = weekend["race"]
        qualifying = weekend["quali"]
        sprint_race = weekend["sprint_race"]
        track = calendar[weekend["round"] - 1]
        races.append({
            "round": weekend["round"],
            "name": track.name,
            "country": track.country,
            "laps": track.laps,
            "is_sprint": track.is_sprint,
            "winner": race.classified[0] if race.classified else None,
            "pole": qualifying.grid[0] if qualifying.grid else None,
            "wet": race.wet,
            "qualifying_wet": qualifying.wet,
            "safety_cars": race.safety_cars,
            "qualifying_grid": qualifying.grid,
            "results": _race_result(race, weekend["points"], driver_teams),
            "sprint": (
                _race_result(sprint_race, weekend["sprint_points"], driver_teams)
                if sprint_race else None
            ),
        })

    return {
        "year": year,
        "seed": seed,
        "rounds": len(calendar),
        "standings": _standings(teams),
        "races": races,
    }


def simulate_multi(seasons, seed, start_year):
    """Back-to-back seasons with off-season transfers in between."""
    rng = random.Random(seed)
    teams = build_2026_grid()
    calendar = build_2026_calendar()
    driver_titles = Counter()
    constructor_titles = Counter()
    entries = []

    for index in range(seasons):
        year = start_year + index
        season = _run_season(year, teams, calendar, rng.randint(0, 10**9))
        standings = season.driver_standings()
        constructors = season.constructor_standings()
        champion, runner_up, constructor_champion = standings[0], standings[1], constructors[0]
        driver_titles[champion.name] += 1
        constructor_titles[constructor_champion.name] += 1
        snapshot = _standings(teams)

        news = []
        if index < seasons - 1:
            regulation_change = (index + 1) % REGULATION_CYCLE_SEASONS == 0
            news = run_offseason(teams, rng, quiet=True, regulation_change=regulation_change)

        entries.append({
            "year": year,
            "champion": _champion(champion),
            "runner_up": _champion(runner_up),
            "constructor_champion": {
                "name": constructor_champion.name,
                "points": round(constructor_champion.season_points, 1),
                "wins": constructor_champion.season_wins,
            },
            "winners": len(_winners(season)),
            "standings": snapshot,
            "news": news,
        })

    return {
        "seed": seed,
        "seasons": entries,
        "driver_titles": _tally(driver_titles),
        "constructor_titles": _tally(constructor_titles),
    }


def _practice_payload(practice, driver_teams):
    return [
        [{**result, "team": driver_teams[result["name"]], "time": round(result["time"], 3)} for result in session]
        for session in practice.sessions
    ]


def _qualifying_payload(quali, driver_teams):
    return {
        "wet": quali.wet,
        "grid": [
            {"position": position, "name": name, "team": driver_teams[name]}
            for position, name in enumerate(quali.grid, start=1)
        ],
        "sessions": {
            key: sorted(
                ({"name": name, "team": driver_teams[name], "time": round(time, 3)} for name, time in times.items()),
                key=lambda row: row["time"],
            )
            for key, times in quali.session_times.items()
        },
        "eliminated_q1": quali.eliminated_in_q1,
        "eliminated_q2": quali.eliminated_in_q2,
    }


def simulate_weekend(round_number, seed):
    """One standalone race weekend: practice, qualifying, optional sprint, race."""
    teams = build_2026_grid()
    calendar = build_2026_calendar()
    if not 1 <= round_number <= len(calendar):
        raise ValueError(f"Round must be between 1 and {len(calendar)}")
    track = calendar[round_number - 1]
    rng = random.Random(seed)
    driver_teams = {driver.name: team.name for team in teams for driver in team.drivers}

    for team in teams:
        team.weekend_form = rng.gauss(0.0, 2.0)
    practice = sim.simulate_practice(teams, track, rng, session_count=1 if track.is_sprint else 3)

    sprint_quali = sprint_race = None
    sprint_points = {}
    if track.is_sprint:
        sprint_quali = sim.simulate_sprint_qualifying(teams, track, rng)
        sprint_race = sim.simulate_race(teams, track, sprint_quali.grid, rng)
        sprint_points = sim.award_sprint_points(sprint_race, teams)

    quali = sim.simulate_qualifying(teams, track, rng)
    race = sim.simulate_race(teams, track, quali.grid, rng)
    race_points = sim.award_points(race, teams)

    totals = Counter()
    for earned in (sprint_points, race_points):
        for name, points in earned.items():
            totals[name] += points
    weekend_points = [
        {"name": name, "team": driver_teams[name], "points": points}
        for name, points in sorted(totals.items(), key=lambda item: (-item[1], item[0]))
        if points
    ]

    return {
        "round": round_number,
        "seed": seed,
        "track": {
            "name": track.name,
            "country": track.country,
            "laps": track.laps,
            "is_sprint": track.is_sprint,
            "circuit_length_km": track.circuit_length_km,
            "turn_count": track.turn_count,
            "track_type": track.track_type,
            "overtaking_difficulty": track.overtaking_difficulty,
            "wet_chance": track.wet_chance,
            "safety_car_chance": track.safety_car_chance,
            "tyre_selection": list(track.tyre_selection),
        },
        "practice": _practice_payload(practice, driver_teams),
        "sprint_qualifying": _qualifying_payload(sprint_quali, driver_teams) if sprint_quali else None,
        "sprint": _race_result(sprint_race, sprint_points, driver_teams) if sprint_race else None,
        "qualifying": _qualifying_payload(quali, driver_teams),
        "race": _race_result(race, race_points, driver_teams),
        "weekend_points": weekend_points,
    }


def predict_round(round_number, trials, seed):
    """Monte Carlo a single round on a fresh grid and report outcome probabilities."""
    teams = build_2026_grid()
    calendar = build_2026_calendar()
    if not 1 <= round_number <= len(calendar):
        raise ValueError(f"Round must be between 1 and {len(calendar)}")
    track = calendar[round_number - 1]
    rng = random.Random(seed)
    drivers = [d for t in teams for d in t.drivers]
    driver_team = {d.name: d.team for d in drivers}
    field_size = len(drivers)

    wins, podiums, points_finishes, poles, dnfs = (Counter() for _ in range(5))
    position_sum = defaultdict(float)

    for _ in range(trials):
        for team in teams:
            team.weekend_form = rng.gauss(0.0, 2.0)
        quali = sim.simulate_qualifying(teams, track, rng)
        race = sim.simulate_race(teams, track, quali.grid, rng)
        poles[quali.grid[0]] += 1
        for position, name in enumerate(race.classified, start=1):
            position_sum[name] += position
            wins[name] += position == 1
            podiums[name] += position <= 3
            points_finishes[name] += position <= 10
        for name in race.dnfs:
            dnfs[name] += 1
            position_sum[name] += field_size

    def pct(count):
        return round(count / trials * 100, 1)

    rows = [
        {
            "name": d.name,
            "team": driver_team[d.name],
            "win_pct": pct(wins[d.name]),
            "podium_pct": pct(podiums[d.name]),
            "points_pct": pct(points_finishes[d.name]),
            "pole_pct": pct(poles[d.name]),
            "dnf_pct": pct(dnfs[d.name]),
            "avg_position": round(position_sum[d.name] / trials, 2),
        }
        for d in drivers
    ]
    rows.sort(key=lambda row: row["avg_position"])

    def top(counter):
        if not counter:
            return None
        name, count = counter.most_common(1)[0]
        return {"name": name, "team": driver_team[name], "pct": pct(count)}

    return {
        "round": round_number,
        "trials": trials,
        "seed": seed,
        "track": {"name": track.name, "country": track.country, "is_sprint": track.is_sprint},
        "likely_pole": top(poles),
        "likely_winner": top(wins),
        "rows": rows,
    }


def run_until(condition, target, threshold, seed, start_year, max_seasons):
    """Keep simulating seasons until a condition is met, the cap is hit, or a watched driver leaves."""
    if condition not in UNTIL_CONDITIONS:
        raise ValueError("Unknown condition")
    teams = build_2026_grid()
    calendar = build_2026_calendar()
    known_drivers = {d.name for t in teams for d in t.drivers} | set(F1_PROSPECTS)

    if condition in ("champion", "win") and target not in known_drivers:
        raise ValueError(f"Unknown driver '{target}'. Pick a name from the suggestions.")
    if condition == "constructor" and target not in {t.name for t in teams}:
        raise ValueError(f"Unknown team '{target}'. Pick a name from the suggestions.")
    if condition == "winners" and threshold is None:
        raise ValueError("Enter how many different race winners the season must exceed")
    if condition in ("tiebreak", "winners"):
        target = None
    if condition != "winners":
        threshold = None

    rng = random.Random(seed)
    watched = {target} if condition in ("champion", "win") else set()
    watched_seen = {d.name for t in teams for d in t.drivers} & watched
    year = start_year
    count = 0
    rows = []

    while True:
        season = _run_season(year, teams, calendar, rng.randint(0, 10**9))
        count += 1
        standings = season.driver_standings()
        champion, runner_up = standings[0], standings[1]
        constructor_champion = season.constructor_standings()[0]
        winners = _winners(season)
        margin = champion.season_points - runner_up.season_points
        tiebreak = margin == 0
        enough_winners = threshold is not None and len(winners) > threshold
        rows.append({
            "year": year,
            "champion": champion.name,
            "champion_team": champion.team,
            "constructor_champion": constructor_champion.name,
            "winners": len(winners),
            "margin": round(margin, 1),
        })

        met = {
            "champion": champion.name == target,
            "constructor": constructor_champion.name == target,
            "win": target in winners,
            "tiebreak": tiebreak,
            "winners": enough_winners,
        }[condition]

        if met or count >= max_seasons:
            if met:
                reason = "met"
                message = f"Condition met after {count} season(s) — {year}."
                if condition == "tiebreak":
                    message += (f" {champion.name} and {runner_up.name} both finish on "
                                f"{champion.season_points:.0f} points, decided on countback.")
                if condition == "winners":
                    message += f" {year} had {len(winners)} different race winners (more than {threshold})."
            else:
                reason = "cap"
                message = f"Stopped after reaching the {max_seasons}-season cap without meeting the condition."
                if watched - watched_seen:
                    message += (f" {target} never appeared on the grid, so check whether the name "
                                f"is a prospect who was never promoted.")
            return _until_result(condition, target, threshold, met, reason, message, count, year, rows, teams)

        run_offseason(teams, rng, quiet=True, regulation_change=count % REGULATION_CYCLE_SEASONS == 0)
        year += 1

        if watched:
            active = {d.name for t in teams for d in t.drivers}
            watched_seen |= watched & active
            if (watched & watched_seen) - active:
                message = (f"Stopped after {count} season(s) — {target} left the grid "
                           f"(retired or released) before the condition was met.")
                return _until_result(condition, target, threshold, False, "left_grid", message, count,
                                     year - 1, rows, teams)


def _until_result(condition, target, threshold, met, reason, message, count, year, rows, teams):
    return {
        "condition": condition,
        "target": target,
        "threshold": threshold,
        "met": met,
        "reason": reason,
        "message": message,
        "seasons_run": count,
        "final_year": year,
        "rows": rows[-MAX_ROW_HISTORY:],
        "truncated": len(rows) > MAX_ROW_HISTORY,
        "final_standings": _until_standings(teams),
    }


def _until_standings(teams):
    # Offseason changes have not yet run for the final season, so points still reflect it.
    return _standings(teams)


def simulate_history(seasons, seed, start_year):
    """Many fast seasons; reports notable events plus all-time leaders and records."""
    rng = random.Random(seed)
    teams = build_2026_grid()
    calendar = build_2026_calendar()
    args = Namespace(seasons=seasons, start_year=start_year)
    buffer = io.StringIO()
    with _CAPTURE_LOCK, contextlib.redirect_stdout(buffer):
        cli.run_history(teams, calendar, rng, args)
    return {"seasons": seasons, "seed": seed, **_parse_history(buffer.getvalue())}


def _parse_history(text):
    notes, driver_titles, constructor_titles, records = [], [], [], []
    section = None
    for line in text.splitlines():
        note = re.match(r"^\s+\[(\d+)\] (.+)$", line)
        if note:
            notes.append({"year": int(note.group(1)), "text": note.group(2)})
        elif line.startswith("Most drivers' titles"):
            section = "drivers"
        elif line.startswith("Most constructors' titles"):
            section = "constructors"
        elif line.startswith("Records"):
            section = "records"
        elif section in ("drivers", "constructors"):
            row = re.match(r"^\s+(.+?)\s+(\d+)$", line)
            if row:
                target = driver_titles if section == "drivers" else constructor_titles
                target.append({"name": row.group(1), "count": int(row.group(2))})
        elif section == "records":
            row = re.match(r"^\s+(\w+)\s+(-?[\d.]+)\s+\((.+), (\d+)\)$", line)
            if row:
                records.append({
                    "label": row.group(1),
                    "value": float(row.group(2)),
                    "extra": row.group(3),
                    "year": int(row.group(4)),
                })
    return {
        "notes": notes,
        "driver_titles": driver_titles,
        "constructor_titles": constructor_titles,
        "records": records,
    }
