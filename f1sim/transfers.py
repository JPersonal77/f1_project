"""
Off-season transfer market.

Simplified but season-aware model:
1. Every driver's contract ticks down by one year.
2. Out-of-contract drivers become free agents. Additionally, a team may
   drop a driver who badly underperformed their teammate this season
   (probabilistic "seat at risk" check) even mid-contract, simulating a
   sacking -- rare, but it happens in F1.
3. Retiring veterans (older drivers with an expiring contract and a
   rough season) may retire outright rather than re-enter the market.
4. Open seats are filled by matching remaining free agents to teams by
   tier (front-running teams chase the best available driver, etc.),
   greedily pairing the strongest free agents with the best open seats.
5. Any leftover open seats are filled by promoting a fresh junior driver
   from a small rookie pool, simulating an academy graduate.
"""
import random
from f1sim.data import (
    ACADEMY_FEEDER_TEAMS,
    F1_PROSPECTS,
    TEAM_ACADEMY_PREFERENCES,
    TEAM_JUNIOR_APPETITE,
    DRIVER_TEAM_PREFERENCES,
)
from f1sim.models import Driver

ROOKIE_FIRST_NAMES = ["Enzo", "Mateo", "Kaito", "Theo", "Noah", "Leon", "Rafael", "Milo", "Elio", "Aksel"]
ROOKIE_LAST_NAMES = ["Marchetti", "Dubois", "Nakamura", "Reyes", "Vermeer", "Kowalski", "Silva", "Larsen", "Costa", "Berg"]
ROOKIE_NATIONALITIES = ["ITA", "FRA", "JPN", "MEX", "NED", "POL", "BRA", "DEN", "POR", "NOR"]

RETIREMENT_AGE_RISK = 35
RETIREMENT_AGE_CAP = 45
RATING_FIELDS = ("pace", "racecraft", "consistency", "wet_skill")


def _retirement_probability(age: int) -> float:
    """Return increasing retirement risk from age 35, capped at 45."""
    if age >= RETIREMENT_AGE_CAP:
        return 1.0
    if age < RETIREMENT_AGE_RISK:
        return 0.0
    return min(0.98, 0.15 + (age - RETIREMENT_AGE_RISK) * 0.105)


def _rating_change(driver: Driver, teammate_points: float) -> int:
    """Return a bounded seasonal development change for a driver's core ratings."""
    if driver.age <= 25:
        age_change = 1
    elif driver.age >= 38:
        age_change = -2
    elif driver.age >= 35:
        age_change = -1
    else:
        age_change = 0

    performance_change = 0
    if driver.season_points >= teammate_points + 15 and driver.season_points >= teammate_points * 1.1:
        performance_change = 1
    elif teammate_points >= driver.season_points + 15 and teammate_points >= driver.season_points * 1.1:
        performance_change = -1

    return max(-2, min(2, age_change + performance_change))


def _update_driver_ratings(driver: Driver, teammate_points: float) -> None:
    change = _rating_change(driver, teammate_points)
    for field_name in RATING_FIELDS:
        setattr(driver, field_name, max(40, min(100, getattr(driver, field_name) + change)))
    if driver.age <= 35:
        driver.experience = min(99, driver.experience + 1)


def _generate_rookie(rng: random.Random, number_pool: set, team_name: str,
                     excluded_names=None) -> Driver:
    excluded_names = excluded_names or set()
    academy_prospects = [
        (name, profile) for name, profile in F1_PROSPECTS.items()
        if name not in excluded_names
        and team_name in ACADEMY_FEEDER_TEAMS.get(profile.get("academy"), set())
    ]
    if academy_prospects:
        name, profile = rng.choice(academy_prospects)
        number = rng.choice([n for n in range(2, 100) if n not in number_pool])
        number_pool.add(number)
        return Driver(
            name=name,
            number=number,
            nationality=profile["nationality"],
            pace=profile["pace"],
            racecraft=profile["racecraft"],
            consistency=profile["consistency"],
            wet_skill=profile["wet_skill"],
            experience=profile["experience"],
            aggression=profile["aggression"],
            age=profile["age"],
            contract_years=rng.randint(2, 3),
            academy=profile["academy"],
        )

    first = rng.choice(ROOKIE_FIRST_NAMES)
    last = rng.choice(ROOKIE_LAST_NAMES)
    nat = rng.choice(ROOKIE_NATIONALITIES)
    number = rng.choice([n for n in range(2, 100) if n not in number_pool])
    number_pool.add(number)
    return Driver(
        name=f"{first} {last}",
        number=number,
        nationality=nat,
        pace=rng.randint(70, 82),
        racecraft=rng.randint(65, 78),
        consistency=rng.randint(60, 75),
        wet_skill=rng.randint(60, 78),
        experience=rng.randint(20, 40),
        aggression=rng.randint(70, 90),
        age=rng.randint(18, 22),
        contract_years=rng.randint(2, 3),
    )


def _build_academy_driver(name: str, profile: dict, rng: random.Random,
                          number_pool: set) -> Driver:
    number = rng.choice([n for n in range(2, 100) if n not in number_pool])
    number_pool.add(number)
    return Driver(
        name=name,
        number=number,
        nationality=profile["nationality"],
        pace=profile["pace"],
        racecraft=profile["racecraft"],
        consistency=profile["consistency"],
        wet_skill=profile["wet_skill"],
        experience=profile["experience"],
        aggression=profile["aggression"],
        age=profile["age"],
        contract_years=rng.randint(2, 3),
        academy=profile["academy"],
    )


def _academy_candidate(team_name: str, rng: random.Random,
                       available_prospects: set, number_pool: set):
    preferred = TEAM_ACADEMY_PREFERENCES.get(team_name, [])
    candidates = [
        (name, F1_PROSPECTS[name]) for name in available_prospects
        if F1_PROSPECTS[name].get("academy") in preferred
    ]
    if not candidates or rng.random() >= TEAM_JUNIOR_APPETITE.get(team_name, 0):
        return None
    name, profile = max(candidates, key=lambda item: item[1]["f1_potential"])
    available_prospects.remove(name)
    return _build_academy_driver(name, profile, rng, number_pool)


def run_offseason(teams, rng: random.Random, quiet=False) -> list:
    """Mutates teams' driver rosters in place. Returns a list of news strings."""
    news = []
    used_numbers = {d.number for t in teams for d in t.drivers}

    free_agents = []
    retirements = []
    former_teams = {}
    active_names = {d.name for team in teams for d in team.drivers}
    available_prospects = set(F1_PROSPECTS) - active_names

    for team in teams:
        kept = []
        for d in team.drivers:
            d.age += 1
            d.contract_years -= 1
            teammate_points = sum(td.season_points for td in team.drivers if td is not d)
            _update_driver_ratings(d, teammate_points)
            underperformed = (
                len(team.drivers) == 2
                and d.season_points < 0.4 * teammate_points
                and teammate_points > 30
            )
            seat_at_risk = d.contract_years <= 0 or (underperformed and rng.random() < 0.35)
            retirement_risk = _retirement_probability(d.age)

            if d.age >= RETIREMENT_AGE_CAP or (seat_at_risk and (
                    retirement_risk > 0 and rng.random() < retirement_risk)):
                retirements.append(d)
                news.append(f"{d.name} announces retirement from Formula 1 after the {team.name} campaign.")
            elif seat_at_risk:
                former_teams[d.name] = d.team
                d.team = None
                d.contract_years = 0
                free_agents.append(d)
            else:
                kept.append(d)
        team.drivers = kept

    # Rank free agents by overall skill (best drivers get picked first)
    free_agents.sort(key=lambda d: d.overall, reverse=True)

    # Determine open seats, ordered so front-running teams fill first
    tier_priority = {"front": 0, "midfield": 1, "back": 2}
    open_slots = []
    for team in sorted(teams, key=lambda t: tier_priority.get(t.tier, 3)):
        while len(team.drivers) < 2:
            open_slots.append(team)
            team.drivers.append(None)  # placeholder, filled below

    for team in sorted(teams, key=lambda t: tier_priority.get(t.tier, 3)):
        for i, seat in enumerate(team.drivers):
            if seat is not None:
                continue
            academy_driver = _academy_candidate(
                team.name, rng, available_prospects, used_numbers
            )
            if academy_driver:
                academy_driver.team = team.name
                team.drivers[i] = academy_driver
                news.append(
                    f"{academy_driver.name} joins {team.name} from the "
                    f"{academy_driver.academy} academy."
                )

    open_slots = [
        (team, i) for team in sorted(teams, key=lambda t: tier_priority.get(t.tier, 3))
        for i, driver in enumerate(team.drivers) if driver is None
    ]

    while free_agents and open_slots:
        candidates = [
            (
                driver.overall
                + DRIVER_TEAM_PREFERENCES.get(driver.name, {}).get(team.name, 0)
                + (18 if former_teams.get(driver.name) == team.name else 0),
                driver,
                index,
            )
            for index, (team, _) in enumerate(open_slots)
            for driver in free_agents
        ]
        fit, driver, slot_index = max(candidates, key=lambda candidate: candidate[0])
        team, seat_index = open_slots.pop(slot_index)
        free_agents.remove(driver)
        driver.team = team.name
        driver.contract_years = rng.randint(1, 3)
        team.drivers[seat_index] = driver
        news.append(f"{driver.name} signs with {team.name} for {driver.contract_years} year(s).")

    for team, seat_index in open_slots:
        rookie = _generate_rookie(
            rng, used_numbers, team.name,
            excluded_names=active_names | {
                d.name for current_team in teams
                for d in current_team.drivers if d is not None
            },
        )
        rookie.team = team.name
        team.drivers[seat_index] = rookie
        news.append(f"{team.name} promotes junior talent {rookie.name} ({rookie.nationality}) to a race seat.")

    # Any free agents left without a seat leave the grid (no room at the inn)
    for leftover in free_agents:
        news.append(f"{leftover.name} is left without a seat for next season.")

    if not quiet:
        print("\n--- Off-season Transfer News ---")
        for line in news:
            print(f"  - {line}")

    return news
