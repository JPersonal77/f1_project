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
import random

from f1sim.data import build_2026_grid, build_2026_calendar
from f1sim.season import Season
from f1sim.transfers import run_offseason


def main():
    parser = argparse.ArgumentParser(description="F1 season simulator")
    parser.add_argument("--seasons", type=int, default=1, help="Number of seasons to simulate")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--quiet", action="store_true", help="Only print standings and transfer news")
    parser.add_argument("--start-year", type=int, default=2026, help="First season's year")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    teams = build_2026_grid()
    calendar = build_2026_calendar()

    for i in range(args.seasons):
        year = args.start_year + i
        season_seed = rng.randint(0, 10**9)
        season = Season(year, teams, calendar, seed=season_seed, quiet=args.quiet)
        season.run()

        if i < args.seasons - 1:
            run_offseason(teams, rng, quiet=args.quiet)


if __name__ == "__main__":
    main()
