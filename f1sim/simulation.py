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


def _session_score(driver, team, wet: bool, rng: random.Random) -> float:
    base = team.car_performance * 0.55
    if wet:
        base += driver.wet_skill * 0.30 + driver.pace * 0.10 + driver.consistency * 0.05
    else:
        base += driver.pace * 0.30 + driver.consistency * 0.10 + driver.experience * 0.05
    noise = rng.gauss(0, 3.2)
    return base + noise


def simulate_practice(teams, track, rng: random.Random) -> Dict[str, float]:
    """Returns a dict of driver_name -> best practice score (flavour/logging only)."""
    wet = rng.random() < track.wet_chance * 0.5  # practice is rarely fully wet
    results = {}
    for team in teams:
        for d in team.drivers:
            best = max(_session_score(d, team, wet, rng) for _ in range(3))  # FP1-3
            results[d.name] = best
    return results


@dataclass
class QualifyingResult:
    grid: List[str]                 # driver names, pole first
    q3_order: List[str]
    eliminated_in_q1: List[str]
    eliminated_in_q2: List[str]
    wet: bool


def simulate_qualifying(teams, track, rng: random.Random) -> QualifyingResult:
    wet = rng.random() < track.wet_chance
    all_drivers = [(d, _team_of(d, teams)) for t in teams for d in t.drivers]

    def timed(pool):
        scored = [(d, _session_score(d, t, wet, rng)) for d, t in pool]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    # Q1: everyone runs, bottom drop to fill grid positions 16-22 (for 22 cars)
    q1 = timed(all_drivers)
    n_drop_q1 = max(len(q1) - 15, 0)
    q1_out = q1[-n_drop_q1:] if n_drop_q1 else []
    q1_through = q1[: len(q1) - n_drop_q1]

    # Q2: bottom drop to fill grid positions 11-15
    q2_pool = [(d, _team_of(d, teams)) for d, _ in q1_through]
    q2 = timed(q2_pool)
    n_drop_q2 = max(len(q2) - 10, 0)
    q2_out = q2[-n_drop_q2:] if n_drop_q2 else []
    q2_through = q2[: len(q2) - n_drop_q2]

    # Q3: top 10 fight for pole
    q3_pool = [(d, _team_of(d, teams)) for d, _ in q2_through]
    q3 = timed(q3_pool)

    grid = [d.name for d, _ in q3] + [d.name for d, _ in reversed(q2_out)] + [d.name for d, _ in reversed(q1_out)]
    return QualifyingResult(
        grid=grid,
        q3_order=[d.name for d, _ in q3],
        eliminated_in_q1=[d.name for d, _ in q1_out],
        eliminated_in_q2=[d.name for d, _ in q2_out],
        wet=wet,
    )


def simulate_sprint_qualifying(teams, track, rng: random.Random) -> QualifyingResult:
    """Runs one timed session for the sprint grid instead of Q1/Q2/Q3."""
    wet = rng.random() < track.wet_chance
    scored = []
    for team in teams:
        for driver in team.drivers:
            scored.append((driver, _session_score(driver, team, wet, rng)))
    scored.sort(key=lambda item: item[1], reverse=True)
    grid = [driver.name for driver, _ in scored]
    return QualifyingResult(
        grid=grid,
        q3_order=grid,
        eliminated_in_q1=[],
        eliminated_in_q2=[],
        wet=wet,
    )


@dataclass
class RaceResult:
    classified: List[str]           # finishing order, names, classified finishers only
    dnfs: List[str]
    fastest_lap: str
    wet: bool
    grid: List[str]


def simulate_race(teams, track, grid: List[str], rng: random.Random) -> RaceResult:
    wet = rng.random() < track.wet_chance
    driver_lookup = {d.name: (d, t) for t in teams for d in t.drivers}

    dnfs = []
    scores = {}
    for pos, name in enumerate(grid, start=1):
        d, t = driver_lookup[name]

        # Mechanical DNF chance
        dnf_chance = (100 - t.reliability) * 0.0028
        # Driver-error DNF chance: aggression up, consistency down = more crashes
        dnf_chance += max(0, (d.aggression - d.consistency)) * 0.0009
        if wet:
            dnf_chance += (100 - d.wet_skill) * 0.0007

        if rng.random() < dnf_chance:
            dnfs.append(name)
            continue

        perf = _session_score(d, t, wet, rng) + d.racecraft * 0.20
        # Grid position advantage: harder to overtake tracks reward qualifying more
        grid_bonus = (len(grid) - pos) * (1.4 + track.overtaking_difficulty * 2.2)
        # A touch of race-day chaos (strategy, safety cars, etc.)
        chaos = rng.gauss(0, 4.0)
        scores[name] = perf + grid_bonus + chaos

    classified = sorted(scores.keys(), key=lambda n: scores[n], reverse=True)
    fastest_lap = max(scores.keys(), key=lambda n: scores[n] + rng.gauss(0, 5)) if scores else ""

    return RaceResult(classified=classified, dnfs=dnfs, fastest_lap=fastest_lap, wet=wet, grid=grid)


def award_points(race: RaceResult, teams) -> Dict[str, float]:
    """Applies championship points to drivers/teams in place; returns name->points earned."""
    driver_lookup = {d.name: (d, t) for t in teams for d in t.drivers}
    earned = {}

    for pos, name in enumerate(race.classified, start=1):
        d, t = driver_lookup[name]
        pts = POINTS.get(pos, 0)
        if name == race.fastest_lap and pos <= 10:
            pts += 1
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
