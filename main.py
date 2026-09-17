#!/usr/bin/env python3
"""
CLI entry point.

Usage:
    python main.py                       # simulate 1 season, full detail
    python main.py --seasons 5           # simulate 5 seasons with transfers between them
    python main.py --seasons 3 --quiet   # only print standings + transfer news, not every race
    python main.py --seed 42             # reproducible run

Run from the f1sim project root (the folder containing this file).
"""
import argparse
import io
import random
import contextlib
from collections import Counter, defaultdict

from f1sim.data import academy_policy_report, build_2026_grid, build_2026_calendar
from f1sim.season import Season
from f1sim.transfers import run_offseason, REGULATION_CYCLE_SEASONS
from f1sim import simulation as sim


def _ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def main():
    parser = argparse.ArgumentParser(description="F1 season simulator")
    parser.add_argument("--seasons", type=int, default=1, help="Number of seasons to simulate")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--randomize", action="store_true",
                        help="Force a fresh random simulation, ignoring --seed")
    parser.add_argument("--quiet", action="store_true", help="Only print standings and transfer news")
    parser.add_argument("--start-year", type=int, default=2026, help="First season's year")
    parser.add_argument("--round", type=int, help="Simulate one calendar round only (1-24)")
    parser.add_argument("--show-academies", action="store_true",
                        help="Show team academy preferences and junior appetite")
    parser.add_argument("--until-champion", type=str,
                        help="Keep simulating seasons (with off-season transfers) until this driver wins the drivers' championship")
    parser.add_argument("--until-constructor-champion", type=str,
                        help="Keep simulating seasons until this team wins the constructors' championship")
    parser.add_argument("--until-win", type=str,
                        help="Keep simulating seasons until this driver wins any race")
    parser.add_argument("--max-seasons", type=int, default=1000,
                        help="Safety cap on seasons when using --until-*  (default 1000)")
    parser.add_argument("--history", action="store_true",
                        help="Simulate --seasons seasons back-to-back, printing only notable "
                             "events (titles, records, upsets) instead of full detail or standings")
    parser.add_argument("--predict", type=int, metavar="ROUND",
                        help="Simulate one calendar round many times and report the most likely "
                             "outcomes (win/podium/points probabilities) instead of one result")
    parser.add_argument("--trials", type=int, default=1000,
                        help="Number of Monte Carlo trials for --predict (default 1000)")
    args = parser.parse_args()

    if args.show_academies:
        print("--- Academy Preferences ---")
        for policy in academy_policy_report():
            print(f"  {policy['team']:<18} academies: {policy['preferred_academies']:<16} "
                  f"junior appetite: {policy['junior_appetite']}")
        if args.seasons == 0:
            return

    rng = random.Random(None if args.randomize else args.seed)
    teams = build_2026_grid()
    calendar = build_2026_calendar()

    until_conditions = (args.until_champion, args.until_constructor_champion, args.until_win)
    if any(until_conditions):
        run_until(teams, calendar, rng, args)
        return

    if args.history:
        run_history(teams, calendar, rng, args)
        return

    if args.predict:
        run_prediction(teams, calendar, rng, args)
        return

    for i in range(args.seasons):
        year = args.start_year + i
        season_seed = rng.randint(0, 10**9)
        season = Season(year, teams, calendar, seed=season_seed, quiet=args.quiet)
        if args.round is None:
            season.run()
        else:
            season.run_round(args.round)
            break

        if i < args.seasons - 1:
            regulation_change = (i + 1) % REGULATION_CYCLE_SEASONS == 0
            run_offseason(teams, rng, quiet=args.quiet, regulation_change=regulation_change)


def run_until(teams, calendar, rng, args):
    """Simulates seasons back-to-back (with off-season transfers) until one of the
    --until-* conditions is met, --max-seasons is reached, or a watched driver
    (--until-champion / --until-win) leaves the grid for good after having raced."""
    year = args.start_year
    season_count = 0
    watched_drivers = {name for name in (args.until_champion, args.until_win) if name}
    # Only flag a driver as "gone" once they've actually appeared on the grid -
    # junior/rookie targets may not be promoted into a seat until a later season.
    watched_seen = {d.name for t in teams for d in t.drivers} & watched_drivers
    while True:
        season_seed = rng.randint(0, 10**9)
        season = Season(year, teams, calendar, seed=season_seed, quiet=args.quiet)
        season.run()
        season_count += 1

        champion = season.driver_standings()[0]
        constructor_champion = season.constructor_standings()[0]
        race_winners = set()
        for entry in season.race_log:
            for key in ("race", "sprint_race"):
                result = entry[key]
                if result and result.classified:
                    race_winners.add(result.classified[0])

        met = (
            (args.until_champion and champion.name == args.until_champion)
            or (args.until_constructor_champion and constructor_champion.name == args.until_constructor_champion)
            or (args.until_win and args.until_win in race_winners)
        )

        if met or season_count >= args.max_seasons:
            print(f"\n{'#' * 60}")
            if met:
                print(f"  Condition met after {season_count} season(s) — {season.year}")
            else:
                print(f"  Stopped after reaching the {args.max_seasons}-season cap without meeting the condition")
                never_seen = watched_drivers - watched_seen
                if never_seen:
                    print(f"  Note: {', '.join(sorted(never_seen))} never appeared on the grid "
                          f"(check the spelling of the driver name).")
            print(f"{'#' * 60}")
            return

        news = run_offseason(teams, rng, quiet=args.quiet, regulation_change=season_count % REGULATION_CYCLE_SEASONS == 0)
        year += 1

        if watched_drivers:
            active_names = {d.name for t in teams for d in t.drivers}
            watched_seen |= (watched_drivers & active_names)
            gone = (watched_drivers & watched_seen) - active_names
            if gone:
                print(f"\n{'#' * 60}")
                print(f"  Stopped after {season_count} season(s) — {', '.join(sorted(gone))} "
                      f"left the grid (retired or released) before the condition was met")
                print(f"{'#' * 60}")
                return


def run_history(teams, calendar, rng, args):
    """Simulates --seasons seasons back-to-back, forcing quiet race output and
    printing only notable events as they happen (titles, records, upsets),
    followed by a final all-time summary."""
    records = {}  # label -> (value, year, extra)
    driver_titles = defaultdict(int)
    team_titles = defaultdict(int)
    teams_with_a_win = set()
    last_driver_champion = None
    driver_streak = 0
    last_team_champion = None
    team_streak = 0

    def note_record(label, value, year, extra, higher_is_better=True):
        best = records.get(label)
        is_new_best = best is None or (value > best[0] if higher_is_better else value < best[0])
        if is_new_best:
            records[label] = (value, year, extra)
        return is_new_best

    for i in range(args.seasons):
        year = args.start_year + i
        season_seed = rng.randint(0, 10**9)
        season = Season(year, teams, calendar, seed=season_seed, quiet=True)
        # Season.run() always prints final standings even when quiet; swallow
        # that here since history mode only wants notable events + the summary.
        with contextlib.redirect_stdout(io.StringIO()):
            season.run()

        standings = season.driver_standings()
        champion = standings[0]
        runner_up = standings[1] if len(standings) > 1 else None
        constructor_champion = season.constructor_standings()[0]

        notes = []

        driver_titles[champion.name] += 1
        if driver_titles[champion.name] == 1:
            notes.append(f"{champion.name} claims a maiden drivers' title, driving for {constructor_champion.name}.")
        team_titles[constructor_champion.name] += 1
        if team_titles[constructor_champion.name] == 1:
            notes.append(f"{constructor_champion.name} win their first constructors' title.")

        if champion.name == last_driver_champion:
            driver_streak += 1
        else:
            if driver_streak >= 3:
                notes.append(f"{last_driver_champion}'s run of {driver_streak} straight titles comes to an end.")
            driver_streak = 1
            last_driver_champion = champion.name
        if driver_streak in (3, 5, 7, 10):
            notes.append(f"{champion.name} wins a {_ordinal(driver_streak)} consecutive drivers' title!")

        if constructor_champion.name == last_team_champion:
            team_streak += 1
        else:
            if team_streak >= 3:
                notes.append(f"{last_team_champion}'s run of {team_streak} straight constructors' titles comes to an end.")
            team_streak = 1
            last_team_champion = constructor_champion.name
        if team_streak in (3, 5, 7, 10):
            notes.append(f"{constructor_champion.name} wins a {_ordinal(team_streak)} consecutive constructors' title!")

        if runner_up is not None:
            margin = champion.season_points - runner_up.season_points
            if margin <= 5:
                notes.append(f"Nail-biter: {champion.name} takes the {year} title by just "
                              f"{margin:.0f} points over {runner_up.name}.")
            if note_record("biggest_title_margin", margin, year, champion.name):
                notes.append(f"{champion.name} wins the {year} title by a record {margin:.0f} points.")

        if note_record("driver_points", champion.season_points, year, champion.name):
            notes.append(f"{champion.name} sets a new single-season points record: {champion.season_points:.0f}.")
        if note_record("team_points", constructor_champion.season_points, year, constructor_champion.name):
            notes.append(f"{constructor_champion.name} set a new constructors' points record: "
                          f"{constructor_champion.season_points:.0f}.")
        if note_record("driver_wins", champion.season_wins, year, champion.name):
            notes.append(f"{champion.name} sets a new single-season wins record: {champion.season_wins}.")

        if champion.age <= 21:
            notes.append(f"{champion.name} becomes champion at just {champion.age} years old.")
        if champion.age >= 40:
            notes.append(f"{champion.name} wins the title at {champion.age}, defying Father Time.")

        for entry in season.race_log:
            for key in ("race", "sprint_race"):
                result = entry[key]
                if not result or not result.classified:
                    continue
                winner = next((d for d in season.drivers() if d.name == result.classified[0]), None)
                if winner and winner.team not in teams_with_a_win:
                    teams_with_a_win.add(winner.team)
                    notes.append(f"{winner.team} scores their first-ever race win, with {winner.name} at {entry['track']}.")

        for note in notes:
            print(f"  [{year}] {note}")

        if i < args.seasons - 1:
            regulation_change = (i + 1) % REGULATION_CYCLE_SEASONS == 0
            run_offseason(teams, rng, quiet=True, regulation_change=regulation_change)

    print(f"\n{'#' * 60}\n  {args.seasons}-season history summary\n{'#' * 60}")
    print("\nMost drivers' titles:")
    for name, count in sorted(driver_titles.items(), key=lambda x: -x[1])[:5]:
        print(f"  {name:<25} {count}")
    print("\nMost constructors' titles:")
    for name, count in sorted(team_titles.items(), key=lambda x: -x[1])[:5]:
        print(f"  {name:<18} {count}")
    print("\nRecords:")
    for label, (value, year, extra) in records.items():
        print(f"  {label:<20} {value:8.1f}  ({extra}, {year})")


def run_prediction(teams, calendar, rng, args):
    """Simulates a single calendar round many times (fresh grid, no season carry-over)
    and reports win/podium/points probabilities instead of a single result."""
    if not 1 <= args.predict <= len(calendar):
        print(f"--predict must be between 1 and {len(calendar)}")
        return
    track = calendar[args.predict - 1]
    trials = max(1, args.trials)

    drivers = [d for t in teams for d in t.drivers]
    driver_team = {d.name: d.team for d in drivers}
    win_counts = Counter()
    podium_counts = Counter()
    points_counts = Counter()
    pole_counts = Counter()
    dnf_counts = Counter()
    position_sum = defaultdict(float)
    field_size = len(drivers)

    for _ in range(trials):
        for team in teams:
            team.weekend_form = rng.gauss(0.0, 2.0)
        quali = sim.simulate_qualifying(teams, track, rng)
        race = sim.simulate_race(teams, track, quali.grid, rng)

        pole_counts[quali.grid[0]] += 1
        for position, name in enumerate(race.classified, start=1):
            position_sum[name] += position
            if position == 1:
                win_counts[name] += 1
            if position <= 3:
                podium_counts[name] += 1
            if position <= 10:
                points_counts[name] += 1
        for name in race.dnfs:
            dnf_counts[name] += 1
            position_sum[name] += field_size  # treat a DNF as a back-of-field result

    print(f"\n{'#' * 60}\n  Prediction: Round {args.predict} — {track.name} ({track.country}) "
          f"[{trials} simulated trials]\n{'#' * 60}")

    top_pole = pole_counts.most_common(1)
    top_win = win_counts.most_common(1)
    if top_pole:
        print(f"\nMost likely pole sitter: {top_pole[0][0]} ({top_pole[0][1] / trials:.1%})")
    if top_win:
        print(f"Most likely race winner: {top_win[0][0]} ({top_win[0][1] / trials:.1%})")

    print("\nProjected finishing order (by average simulated position):")
    ranking = sorted(drivers, key=lambda d: position_sum[d.name] / trials)
    print(f"  {'':<4}{'Driver':<25}{'Team':<18}{'Win%':>7}{'Podium%':>9}{'Points%':>9}"
          f"{'Avg P':>7}{'DNF%':>7}")
    for position, d in enumerate(ranking, start=1):
        avg_pos = position_sum[d.name] / trials
        print(f"  P{position:<3}{d.name:<25}{driver_team.get(d.name, ''):<18}"
              f"{win_counts[d.name] / trials:>6.1%} {podium_counts[d.name] / trials:>8.1%} "
              f"{points_counts[d.name] / trials:>8.1%} {avg_pos:>6.1f} "
              f"{dnf_counts[d.name] / trials:>6.1%}")


if __name__ == "__main__":
    main()
