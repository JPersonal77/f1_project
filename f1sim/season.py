"""
Season: runs a full calendar of race weekends, tracks standings, and
prints summaries. Designed to be driven from main.py but usable directly.
"""
import random
from f1sim import simulation as sim


class Season:
    def __init__(self, year: int, teams: list, calendar: list, seed=None, quiet=False):
        self.year = year
        self.teams = teams
        self.calendar = calendar
        self.rng = random.Random(seed)
        self.quiet = quiet
        self.race_log = []  # list of dicts, one per round

        for t in self.teams:
            t.reset_season()

    def drivers(self):
        return [d for t in self.teams for d in t.drivers]

    def driver_standings(self):
        return sorted(self.drivers(), key=lambda d: d.season_points, reverse=True)

    def constructor_standings(self):
        return sorted(self.teams, key=lambda t: t.season_points, reverse=True)

    def _p(self, *args):
        if not self.quiet:
            print(*args)

    def run_weekend(self, round_no: int, track):
        self._p(f"\n=== Round {round_no}: {track.name} ({track.country}) ===")

        sim.simulate_practice(self.teams, track, self.rng)  # flavour only for now
        sprint_quali = None
        sprint_race = None
        sprint_earned = {}
        if track.is_sprint:
            sprint_quali = sim.simulate_sprint_qualifying(self.teams, track, self.rng)
            self._p(f"Sprint qualifying ({'WET' if sprint_quali.wet else 'Dry'}) — "
                    f"Pole: {sprint_quali.grid[0]}")
            sprint_race = sim.simulate_race(self.teams, track, sprint_quali.grid, self.rng)
            sprint_earned = sim.award_sprint_points(sprint_race, self.teams)
            self._p(f"Sprint race ({'WET' if sprint_race.wet else 'Dry'}) result:")
            if not self.quiet:
                for i, name in enumerate(sprint_race.classified[:8], start=1):
                    print(f"  {i:2d}. {name:<22} +{sprint_earned.get(name, 0):.0f} pts")
                if sprint_race.dnfs:
                    print(f"  DNF: {', '.join(sprint_race.dnfs)}")

        quali = sim.simulate_qualifying(self.teams, track, self.rng)
        cond = "WET" if quali.wet else "Dry"
        self._p(f"Qualifying ({cond}) — Pole: {quali.grid[0]}")
        if not self.quiet:
            for i, name in enumerate(quali.grid[:10], start=1):
                print(f"  P{i:2d}  {name}")

        race = sim.simulate_race(self.teams, track, quali.grid, self.rng)
        earned = sim.award_points(race, self.teams)

        cond = "WET" if race.wet else "Dry"
        self._p(f"\nRace ({cond}, {track.laps} laps) result:")
        if not self.quiet:
            for i, name in enumerate(race.classified[:10], start=1):
                print(f"  {i:2d}. {name:<22} +{earned.get(name, 0):.0f} pts")
            if race.dnfs:
                print(f"  DNF: {', '.join(race.dnfs)}")
            print(f"  Fastest lap: {race.fastest_lap}")

        self.race_log.append({
            "round": round_no,
            "track": track.name,
            "laps": track.laps,
            "sprint_quali": sprint_quali,
            "sprint_race": sprint_race,
            "sprint_points": sprint_earned,
            "quali": quali,
            "race": race,
            "points": earned,
        })

    def run(self):
        self._p(f"\n{'#' * 60}\n  {self.year} SEASON START — {len(self.calendar)} rounds\n{'#' * 60}")
        for i, track in enumerate(self.calendar, start=1):
            self.run_weekend(i, track)
        self.print_standings()

    def print_standings(self):
        print(f"\n--- {self.year} Final Drivers' Championship ---")
        for i, d in enumerate(self.driver_standings(), start=1):
            print(f"  {i:2d}. {d.name:<22} {d.team:<18} {d.season_points:5.0f} pts "
                  f"({d.season_wins}W, {d.season_podiums}P, {d.season_dnfs} DNF)")

        print(f"\n--- {self.year} Final Constructors' Championship ---")
        for i, t in enumerate(self.constructor_standings(), start=1):
            print(f"  {i:2d}. {t.name:<18} {t.season_points:5.0f} pts ({t.season_wins}W)")
