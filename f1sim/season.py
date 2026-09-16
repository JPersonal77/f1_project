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

    @staticmethod
    def _tyre_labels(track, wet=False):
        if wet:
            return "I"
        if track.tyre_selection:
            labels = "S M H".split()
            return "/".join(labels[:len(track.tyre_selection)])
        return "I/W"

    @staticmethod
    def _time(seconds):
        minutes, remainder = divmod(seconds, 60)
        return f"{int(minutes)}:{remainder:06.3f}"

    @staticmethod
    def _gap(seconds):
        minutes, remainder = divmod(max(0.0, seconds), 60)
        if minutes:
            return f"+{int(minutes):02d}:{remainder:06.3f}"
        return f"+{remainder:.3f}"

    def _print_practice(self, practice):
        for number, session in enumerate(practice.sessions, start=1):
            self._p(f"\nPractice {number}:")
            for result in session:
                print(f"  P{result['position']:2d}  {result['name']:<22} "
                      f"{self._time(result['time'])}  {result['laps']:2d} laps")

    def _print_qualifying(self, quali, title="Qualifying"):
        session_name = "SQ" if title == "Sprint Qualifying" else "Q1"
        self._p(f"\n{title} ({'WET' if quali.wet else 'Dry'}):")
        if title == "Sprint Qualifying":
            names = sorted(quali.session_times[session_name],
                           key=quali.session_times[session_name].get)
            for position, name in enumerate(names, start=1):
                print(f"  P{position:2d}  {name:<22} "
                      f"{self._time(quali.session_times[session_name][name])}")
            return
        for phase, cutoff in (("Q1", 15), ("Q2", 10), ("Q3", 10)):
            names = sorted(quali.session_times[phase],
                           key=quali.session_times[phase].get)
            for position, name in enumerate(names[:cutoff], start=1):
                print(f"  {phase} P{position:2d} {name:<22} "
                      f"{self._time(quali.session_times[phase][name])}")
            if phase != "Q3":
                print(f"  ------{phase.lower()} eliminated------")
                for name in names[cutoff:]:
                    print(f"  {phase} OUT {name:<18} "
                          f"{self._time(quali.session_times[phase][name])}")

    def _print_race(self, race, earned, title="Race"):
        cond = "WET" if race.wet else "Dry"
        self._p(f"\n{title} ({cond}):")
        winner_time = race.race_times[race.classified[0]] if race.classified else 0
        for position, name in enumerate(race.classified, start=1):
            if position == 1:
                display_time = self._time(winner_time)
            elif race.laps_completed[name] < race.laps_completed[race.classified[0]]:
                laps_down = race.laps_completed[race.classified[0]] - race.laps_completed[name]
                display_time = f"+{laps_down} lap" + ("s" if laps_down != 1 else "")
            else:
                display_time = self._gap(race.race_times[name] - winner_time)
            print(f"  P{position:2d}  {name:<22} {display_time:<14} "
                  f"{race.laps_completed[name]:2d} laps +{earned.get(name, 0):.0f} pts")
        for name in race.dnfs:
            laps_down = max(0, max(race.laps_completed.values()) - race.laps_completed[name])
            print(f"  DNF   {name:<22} +{laps_down} laps")
        total_stops = sum(race.pit_stops.values())
        print(f"  Pit stops: {total_stops} total; tyres: {self._tyre_labels(self._active_track, race.wet)}; "
              f"pit lane transit: {self._active_track.pit_lane_time_seconds:.1f}s")
        print("  Fastest laps:")
        for name in race.grid:
            print(f"    {name:<22} {self._time(race.fastest_lap_times[name])}")
        print(f"  Overall fastest lap: {race.fastest_lap} "
              f"{self._time(race.fastest_lap_times[race.fastest_lap])}")

    def run_weekend(self, round_no: int, track):
        self._p(f"\n=== Round {round_no}: {track.name} ({track.country}) ===")

        self._active_track = track
        practice = sim.simulate_practice(
            self.teams, track, self.rng, session_count=1 if track.is_sprint else 3
        )
        if not self.quiet:
            self._print_practice(practice)
        sprint_quali = None
        sprint_race = None
        sprint_earned = {}
        if track.is_sprint:
            sprint_quali = sim.simulate_sprint_qualifying(self.teams, track, self.rng)
            if not self.quiet:
                self._print_qualifying(sprint_quali, "Sprint Qualifying")
            sprint_race = sim.simulate_race(self.teams, track, sprint_quali.grid, self.rng)
            sprint_earned = sim.award_sprint_points(sprint_race, self.teams)
            if not self.quiet:
                self._print_race(sprint_race, sprint_earned, "Sprint")

        quali = sim.simulate_qualifying(self.teams, track, self.rng)
        if not self.quiet:
            self._print_qualifying(quali)

        race = sim.simulate_race(self.teams, track, quali.grid, self.rng)
        earned = sim.award_points(race, self.teams)

        if not self.quiet:
            self._print_race(race, earned)

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

    def run_round(self, round_no: int):
        """Simulate one calendar round for a standalone race weekend."""
        if not 1 <= round_no <= len(self.calendar):
            raise ValueError(f"round must be between 1 and {len(self.calendar)}")
        self._p(f"\n{'#' * 60}\n  {self.year} ROUND {round_no} ONLY\n{'#' * 60}")
        self.run_weekend(round_no, self.calendar[round_no - 1])
        self.print_standings()

    def print_standings(self):
        print(f"\n--- {self.year} Final Drivers' Championship ---")
        for i, d in enumerate(self.driver_standings(), start=1):
            print(f"  {i:2d}. {d.name:<22} {d.team:<18} {d.season_points:5.0f} pts "
                  f"({d.season_wins}W, {d.season_podiums}P, {d.season_dnfs} DNF)")

        print(f"\n--- {self.year} Final Constructors' Championship ---")
        for i, t in enumerate(self.constructor_standings(), start=1):
            print(f"  {i:2d}. {t.name:<18} {t.season_points:5.0f} pts ({t.season_wins}W)")
