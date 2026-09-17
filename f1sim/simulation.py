"""
Simulates a race weekend: Practice -> Qualifying (Q1/Q2/Q3) -> Race.

The model is deliberately simple and tweakable:
- A driver's session "score" is a weighted blend of car performance and
  driver skill, plus Gaussian noise for variance.
- Wet weekends re-weight the blend toward wet_skill.
- Race position changes are driven by a performance score with a grid
  position advantage baked in (harder to overtake => grid matters more),
  plus a DNF roll per driver based on team reliability / driver mistakes.
"""
import random
from dataclasses import dataclass
from typing import List, Dict

POINTS = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
SPRINT_POINTS = {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}


def _team_of(driver, teams):
    for t in teams:
        if t.name == driver.team:
            return t
    return None


def _track_adjustment(team, track) -> float:
    """Return a small track-specific package adjustment around zero."""
    turn_total = max(track.turn_count, 1)
    slow_share = track.slow_corners / turn_total
    high_share = track.high_speed_corners / turn_total
    engine_straight_speed = (team.straight_line_speed * 0.55
                             + team.engine_performance * 0.45)
    suitability = (
        team.aero_efficiency * track.downforce_demand * 0.28
        + team.low_speed_performance * slow_share * 0.16
        + team.high_speed_performance * high_share * 0.16
        + team.traction * track.traction_demand * 0.16
        + team.braking * track.braking_demand * 0.12
        + engine_straight_speed * track.straight_line_demand * 0.12
    )
    demand_total = (
        track.downforce_demand * 0.28
        + slow_share * 0.16
        + high_share * 0.16
        + track.traction_demand * 0.16
        + track.braking_demand * 0.12
        + track.straight_line_demand * 0.12
    )
    adjustment = suitability / demand_total - 80
    return max(-4.0, min(4.0, adjustment * 0.12))


def _session_score(driver, team, wet: bool, rng: random.Random, track) -> float:
    base = (team.car_performance + _track_adjustment(team, track)
            + team.weekend_form) * 0.55
    # External driver scores provide a restrained current-form adjustment.
    driver_form = ((driver.reference_tms - 50.0) * 0.025
                   + (driver.reference_sps - 50.0) * 0.012)
    base += max(-2.0, min(2.0, driver_form))
    if wet:
        base += driver.wet_skill * 0.30 + driver.pace * 0.10 + driver.consistency * 0.05
    else:
        base += driver.pace * 0.30 + driver.consistency * 0.10 + driver.experience * 0.05
    noise = rng.gauss(0, 3.2)
    return base + noise


def _lap_time(score: float, track, rng: random.Random) -> float:
    base = 65.0 + track.circuit_length_km * 7.0
    return max(55.0, base - score * 0.12 + rng.gauss(0, 0.08))


def _choose_dry_strategy(track, team, driver, rng: random.Random):
    """Choose a varied but plausible dry-race strategy from recent patterns."""
    soft, medium, hard = track.tyre_selection
    pit_cost = track.pit_lane_time_seconds + team.pit_stop_average_seconds
    two_stop_bias = (track.tyre_wear_rate - 0.55) * 1.8
    two_stop_bias += max(0.0, 4.5 - pit_cost) * 0.04
    two_stop_bias += max(0, driver.aggression - driver.consistency) * 0.003
    two_stop_bias = max(0.05, min(0.65, two_stop_bias))

    if rng.random() < two_stop_bias:
        strategies = [(soft, medium, soft), (medium, hard, medium), (soft, hard, soft)]
        return list(rng.choice(strategies))

    strategies = [(medium, hard), (hard, medium), (soft, hard), (soft, medium)]
    return list(rng.choice(strategies))


@dataclass
class PracticeResult:
    sessions: List[List[dict]]


def simulate_practice(teams, track, rng: random.Random, session_count=3) -> PracticeResult:
    sessions = []
    for _ in range(session_count):
        wet = rng.random() < track.wet_chance * 0.5
        session = []
        for team in teams:
            for driver in team.drivers:
                score = max(_session_score(driver, team, wet, rng, track) for _ in range(3))
                session.append({
                    "name": driver.name,
                    "time": _lap_time(score, track, rng),
                    "laps": rng.randint(14, 28),
                    "wet": wet,
                })
        max_laps = max(result["laps"] for result in session)
        new_max_laps = max(1, int(max_laps * 0.80))
        for result in session:
            result["laps"] = min(result["laps"], new_max_laps)
        session.sort(key=lambda result: result["time"])
        for position, result in enumerate(session, start=1):
            result["position"] = position
        sessions.append(session)
    return PracticeResult(sessions=sessions)


@dataclass
class QualifyingResult:
    grid: List[str]                 # driver names, pole first
    q3_order: List[str]
    eliminated_in_q1: List[str]
    eliminated_in_q2: List[str]
    wet: bool
    session_times: Dict[str, Dict[str, float]]


def simulate_qualifying(teams, track, rng: random.Random) -> QualifyingResult:
    wet = rng.random() < track.wet_chance
    all_drivers = [(d, _team_of(d, teams)) for t in teams for d in t.drivers]

    session_times = {"Q1": {}, "Q2": {}, "Q3": {}}

    def timed(pool, session_name):
        scored = [(d, _session_score(d, t, wet, rng, track)) for d, t in pool]
        for driver, score in scored:
            session_times[session_name][driver.name] = _lap_time(score, track, rng)
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    # Q1: everyone runs, bottom six are eliminated (22 -> 16)
    q1 = timed(all_drivers, "Q1")
    n_drop_q1 = max(len(q1) - 16, 0)
    q1_out = q1[-n_drop_q1:] if n_drop_q1 else []
    q1_through = q1[: len(q1) - n_drop_q1]

    # Q2: bottom six are eliminated (16 -> 10)
    q2_pool = [(d, _team_of(d, teams)) for d, _ in q1_through]
    q2 = timed(q2_pool, "Q2")
    n_drop_q2 = max(len(q2) - 10, 0)
    q2_out = q2[-n_drop_q2:] if n_drop_q2 else []
    q2_through = q2[: len(q2) - n_drop_q2]

    # Q3: top 10 fight for pole
    q3_pool = [(d, _team_of(d, teams)) for d, _ in q2_through]
    q3 = timed(q3_pool, "Q3")

    grid = [d.name for d, _ in q3] + [d.name for d, _ in reversed(q2_out)] + [d.name for d, _ in reversed(q1_out)]
    return QualifyingResult(
        grid=grid,
        q3_order=[d.name for d, _ in q3],
        eliminated_in_q1=[d.name for d, _ in q1_out],
        eliminated_in_q2=[d.name for d, _ in q2_out],
        wet=wet,
        session_times=session_times,
    )


def simulate_sprint_qualifying(teams, track, rng: random.Random) -> QualifyingResult:
    """Runs one timed session for the sprint grid instead of Q1/Q2/Q3."""
    wet = rng.random() < track.wet_chance
    scored = []
    session_times = {"SQ": {}}
    for team in teams:
        for driver in team.drivers:
            score = _session_score(driver, team, wet, rng, track)
            scored.append((driver, score))
            session_times["SQ"][driver.name] = _lap_time(score, track, rng)
    scored.sort(key=lambda item: item[1], reverse=True)
    grid = [driver.name for driver, _ in scored]
    return QualifyingResult(
        grid=grid,
        q3_order=grid,
        eliminated_in_q1=[],
        eliminated_in_q2=[],
        wet=wet,
        session_times=session_times,
    )


@dataclass
class RaceResult:
    classified: List[str]           # finishing order, names, classified finishers only
    dnfs: List[str]
    fastest_lap: str
    wet: bool
    grid: List[str]
    pit_stops: Dict[str, int]
    tyre_strategy: Dict[str, List[str]]
    pit_lane_time: Dict[str, float]
    race_times: Dict[str, float]
    laps_completed: Dict[str, int]
    fastest_lap_times: Dict[str, float]


def simulate_race(teams, track, grid: List[str], rng: random.Random) -> RaceResult:
    wet = rng.random() < track.wet_chance
    driver_lookup = {d.name: (d, t) for t in teams for d in t.drivers}

    dnfs = []
    scores = {}
    pit_stops = {}
    tyre_strategy = {}
    pit_lane_time = {}
    race_times = {}
    laps_completed = {}
    fastest_lap_times = {}
    base_race_time = track.laps * (65.0 + track.circuit_length_km * 7.0)
    for pos, name in enumerate(grid, start=1):
        d, t = driver_lookup[name]

        if wet:
            strategy = ["INTERMEDIATE"]
            stops = 1
        else:
            strategy = _choose_dry_strategy(track, t, d, rng)
            stops = len(strategy) - 1
        pit_stops[name] = stops
        tyre_strategy[name] = strategy
        pit_lane_time[name] = stops * (track.pit_lane_time_seconds + t.pit_stop_average_seconds)
        laps_completed[name] = track.laps
        fastest_lap_times[name] = _lap_time(
            _session_score(d, t, wet, rng, track), track, rng
        )

        # Mechanical DNF chance
        dnf_chance = (100 - t.reliability) * 0.0028
        # Driver-error DNF chance: aggression up, consistency down = more crashes
        dnf_chance += max(0, (d.aggression - d.consistency)) * 0.0009
        if wet:
            dnf_chance += (100 - d.wet_skill) * 0.0007

        if rng.random() < dnf_chance:
            dnfs.append(name)
            laps_completed[name] = rng.randint(max(1, track.laps // 4), max(1, track.laps - 1))
            race_times[name] = laps_completed[name] * (65.0 + track.circuit_length_km * 7.0)
            continue

        perf = (_session_score(d, t, wet, rng, track) + d.racecraft * 0.20
            - pit_lane_time[name] * 0.12)
        # Grid position advantage: harder to overtake tracks reward qualifying more
        grid_bonus = (len(grid) - pos) * (1.4 + track.overtaking_difficulty * 2.2)
        # A touch of race-day chaos (strategy, safety cars, etc.)
        chaos = rng.gauss(0, 4.0)
        scores[name] = perf + grid_bonus + chaos

    classified = sorted(scores.keys(), key=lambda n: scores[n], reverse=True)
    for position, name in enumerate(classified):
        if position >= 15 and rng.random() < 0.12:
            laps_completed[name] = max(1, track.laps - 1)

    # A car that is lapped cannot finish fewer laps down than a car ahead.
    leader_laps = track.laps
    lowest_laps_ahead = leader_laps
    for name in classified:
        lowest_laps_ahead = min(lowest_laps_ahead, laps_completed[name])
        laps_completed[name] = lowest_laps_ahead
    leader_score = scores[classified[0]] if classified else 0
    for position, name in enumerate(classified):
        gap = 0.0 if position == 0 else (classified[position - 1] and rng.uniform(0.4, 4.5))
        if position:
            race_times[name] = race_times.get(classified[position - 1], base_race_time) + gap
        else:
            race_times[name] = base_race_time + pit_lane_time[name] + rng.uniform(-3, 3)
    fastest_lap = max(scores.keys(), key=lambda n: scores[n] + rng.gauss(0, 5)) if scores else ""

    return RaceResult(
        classified=classified,
        dnfs=dnfs,
        fastest_lap=fastest_lap,
        wet=wet,
        grid=grid,
        pit_stops=pit_stops,
        tyre_strategy=tyre_strategy,
        pit_lane_time=pit_lane_time,
        race_times=race_times,
        laps_completed=laps_completed,
        fastest_lap_times=fastest_lap_times,
    )


def award_points(race: RaceResult, teams) -> Dict[str, float]:
    """Applies championship points to drivers/teams in place; returns name->points earned."""
    driver_lookup = {d.name: (d, t) for t in teams for d in t.drivers}
    earned = {}

    for pos, name in enumerate(race.classified, start=1):
        d, t = driver_lookup[name]
        pts = POINTS.get(pos, 0)
        d.season_points += pts
        d.career_points += pts
        t.season_points += pts
        d.career_races += 1
        earned[name] = pts

        if d.best_finish is None or pos < d.best_finish:
            d.best_finish = pos
        if pos == 1:
            d.season_wins += 1
            d.career_wins += 1
            t.season_wins += 1
        if pos <= 3:
            d.season_podiums += 1

    for name in race.dnfs:
        d, t = driver_lookup[name]
        d.season_dnfs += 1
        d.career_races += 1
        earned[name] = 0

    # Pole sitter gets a poles counter bump (grid[0] of the race == pole)
    if race.grid:
        pole_driver = driver_lookup[race.grid[0]][0]
        pole_driver.season_poles += 1

    return earned


def award_sprint_points(race: RaceResult, teams) -> Dict[str, float]:
    """Applies the 8-to-1 sprint points without full-race statistics."""
    driver_lookup = {d.name: (d, t) for t in teams for d in t.drivers}
    earned = {}

    for pos, name in enumerate(race.classified, start=1):
        d, t = driver_lookup[name]
        pts = SPRINT_POINTS.get(pos, 0)
        d.season_points += pts
        d.career_points += pts
        t.season_points += pts
        earned[name] = pts

    for name in race.dnfs:
        earned[name] = 0

    return earned
