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
    def _position_change(race, name):
        starting_position = race.grid.index(name) + 1
        finishing_position = race.classified.index(name) + 1
        return starting_position - finishing_position

    @staticmethod
    def _position_marker(change):
        if change > 0:
            marker = f"\033[32m↑{change}\033[0m"
        if change < 0:
            marker = f"\033[31m↓{abs(change)}\033[0m"
        if change == 0:
            marker = "-"
        visible_length = 1 if change == 0 else len(str(abs(change))) + 1
        return marker + " " * (4 - visible_length)

    @staticmethod
    def _pole_text(text):
        return f"\033[35m{text}\033[0m"

    @staticmethod
    def _tyre_labels(track, wet=False, extreme_wet=False):
        if wet:
            return "W" if extreme_wet else "I"
        if track.tyre_selection:
            labels = "S M H".split()
            return "/".join(labels[:len(track.tyre_selection)])
        return "I/W"

    @staticmethod
    def _time(seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, remainder = divmod(remainder, 60)
        if hours:
            return f"{int(hours)}:{int(minutes):02d}:{remainder:06.3f}"
        return f"{int(minutes)}:{remainder:06.3f}"

    @staticmethod
    def _gap(seconds):
        minutes, remainder = divmod(max(0.0, seconds), 60)
        if minutes:
            return f"+{int(minutes):02d}:{remainder:06.3f}"
        return f"+{remainder:.3f}"

    @staticmethod
    def _qualifying_delta(seconds):
        return f"+{max(0.0, seconds):.3f}s"

    @staticmethod
    def _strategy_labels(strategy, track):
        labels = []
        for compound in strategy:
            if compound in ("INTERMEDIATE", "WET"):
                labels.append("I" if compound == "INTERMEDIATE" else "W")
            elif compound in track.tyre_selection:
                labels.append("SMH"[track.tyre_selection.index(compound)])
            else:
                labels.append(compound)
        return "-".join(labels)

    @staticmethod
    def _driver_initials(name):
        surname = name.split()[-1]
        return surname[:3].upper()

    def _driver_label(self, name):
        driver = next((d for d in self.drivers() if d.name == name), None)
        return f"{driver.flag} {name}" if driver else name

    def _print_starting_grid(self, quali):
        self._p("\nStarting grid:")
        for row in range(11):
            left_position = row * 2 + 1
            right_position = left_position + 1
            left_name = quali.grid[left_position - 1]
            right_name = quali.grid[right_position - 1]
            left = f"| P{left_position:02d} {self._driver_initials(left_name):^3} |"
            right = f"| P{right_position:02d} {self._driver_initials(right_name):^3} |"
            offset = "      " if row % 2 else ""
            print(f"  {offset}+---------+       +---------+")
            print(f"  {offset}{left}       {right}")
        print("  +---------+       +---------+")

    def _print_practice(self, practice):
        for number, session in enumerate(practice.sessions, start=1):
            self._p(f"\nPractice {number}:")
            best_time = session[0]["time"]
            for result in session:
                display_time = (self._time(best_time) if result["position"] == 1
                                else self._qualifying_delta(result["time"] - best_time))
                print(f"  P{result['position']:2d}  {self._driver_label(result['name']):<25} "
                      f"{display_time:<10}  {result['laps']:2d} laps")

    def _print_qualifying(self, quali, title="Qualifying"):
        session_name = "SQ" if title == "Sprint Qualifying" else "Q1"
        self._p(f"\n{title} ({'WET' if quali.wet else 'Dry'}):")
        if title == "Sprint Qualifying":
            times = quali.session_times[session_name]
            names = sorted(times, key=times.get)
            pole_time = times[names[0]]
            for position, name in enumerate(names, start=1):
                position_text = self._pole_text(f"P{position:2d}") if position == 1 else f"P{position:2d}"
                print(f"  {position_text}  {self._driver_label(name):<25} "
                      f"{self._time(times[name])} {self._qualifying_delta(times[name] - pole_time)}")
            return

        q1_times = quali.session_times["Q1"]
        q2_times = quali.session_times["Q2"]
        q3_times = quali.session_times["Q3"]
        q3_names = sorted(q3_times, key=q3_times.get)
        q2_names = sorted(quali.eliminated_in_q2, key=q2_times.get)
        q1_names = sorted(quali.eliminated_in_q1, key=q1_times.get)
        pole_time = q3_times[q3_names[0]]
        position = 1
        previous_gap = 0.0
        for name in q3_names:
            raw_gap = q3_times[name] - pole_time
            display_time = (self._time(q3_times[name]) if position == 1
                        else self._qualifying_delta(max(raw_gap, previous_gap + 0.001)))
            previous_gap = max(raw_gap, previous_gap + 0.001)
            position_text = self._pole_text(f"P{position:2d}") if position == 1 else f"P{position:2d}"
            print(f"  {position_text}  {self._driver_label(name):<25} {display_time}")
            position += 1
        print("  ----------------Q2----------------")
        for name in q2_names:
            previous_gap = max(q2_times[name] - pole_time, previous_gap + 0.001)
            print(f"  P{position:2d}  {self._driver_label(name):<25} "
                f"{self._qualifying_delta(previous_gap)}")
            position += 1
        print("  ----------------Q1----------------")
        for name in q1_names:
            previous_gap = max(q1_times[name] - pole_time, previous_gap + 0.001)
            print(f"  P{position:2d}  {self._driver_label(name):<25} "
                f"{self._qualifying_delta(previous_gap)}")
            position += 1

    def _print_race(self, race, earned, title="Race"):
        cond = "EXTREME WET" if race.extreme_wet else ("WET" if race.wet else "Dry")
        self._p(f"\n{title} ({cond}):")
        if race.safety_cars:
            label = "Safety car" if race.safety_cars == 1 else f"{race.safety_cars} safety cars"
            self._p(f"  \033[33m⚠ {label} deployed — field bunched up\033[0m")
        winner_time = race.race_times[race.classified[0]] if race.classified else 0
        for position, name in enumerate(race.classified, start=1):
            if position == 1:
                display_time = self._time(winner_time)
            elif race.laps_completed[name] < race.laps_completed[race.classified[0]]:
                laps_down = race.laps_completed[race.classified[0]] - race.laps_completed[name]
                display_time = f"+{laps_down} lap" + ("s" if laps_down != 1 else "")
            else:
                display_time = self._gap(race.race_times[name] - winner_time)
            fastest_marker = " (F)" if name == race.fastest_lap else ""
            strategy = self._strategy_labels(race.tyre_strategy[name], self._active_track)
            change = self._position_change(race, name)
            marker = self._position_marker(change)
            print(f"  P{position:2d}  {self._driver_label(name) + fastest_marker:<30} {marker} "
                f"{strategy:<7} {display_time:<14} "
                  f"{race.laps_completed[name]:2d} laps +{earned.get(name, 0):.0f} pts")
        for name in race.dnfs:
            laps_down = max(0, max(race.laps_completed.values()) - race.laps_completed[name])
            print(f"  DNF   {self._driver_label(name):<25} +{laps_down} laps")
        total_stops = sum(race.pit_stops.values())
        print(f"  Pit stops: {total_stops} total; "
              f"tyres: {self._tyre_labels(self._active_track, race.wet, race.extreme_wet)}; "
              f"pit lane transit: {self._active_track.pit_lane_time_seconds:.1f}s")
        overtakes = sorted(
            ((self._position_change(race, name), name) for name in race.classified),
            reverse=True,
        )
        print("  Most overtakes:")
        for change, name in overtakes[:5]:
            if change <= 0:
                break
            print(f"    {self._driver_label(name):<25} {self._position_marker(change)} positions")

    def _find_driver(self, name):
        return next((d for d in self.drivers() if d.name == name), None)

    def _print_race_report(self, race, title="Race"):
        if not race.classified:
            return
        winner_name = race.classified[0]
        winner = self._find_driver(winner_name)
        start_pos = race.grid.index(winner_name) + 1

        sentences = []
        if start_pos == 1:
            sentences.append(f"{self._driver_label(winner_name)} converts pole into victory for {winner.team}.")
        else:
            sentences.append(
                f"{self._driver_label(winner_name)} storms from P{start_pos} to win for {winner.team}."
            )

        if len(race.classified) > 1:
            runner_up = race.classified[1]
            if race.laps_completed[runner_up] < race.laps_completed[winner_name]:
                laps_down = race.laps_completed[winner_name] - race.laps_completed[runner_up]
                margin = f"by {laps_down} lap" + ("s" if laps_down != 1 else "")
            else:
                margin = self._gap(race.race_times[runner_up] - race.race_times[winner_name])
            sentences.append(f"{self._driver_label(runner_up)} finishes second, {margin} behind.")

        if race.extreme_wet:
            sentences.append("Torrential conditions forced full wet tyres for the whole field.")

        if race.safety_cars:
            label = "A safety car" if race.safety_cars == 1 else f"{race.safety_cars} safety cars"
            sentences.append(f"{label} bunched the field and shook up the running order.")

        if race.dnfs:
            names = ", ".join(self._driver_label(name) for name in race.dnfs)
            sentences.append(f"Retirements: {names}.")

        movers = sorted(
            ((self._position_change(race, name), name) for name in race.classified),
            reverse=True,
        )
        if movers and movers[0][0] > 0:
            change, name = movers[0]
            sentences.append(f"{self._driver_label(name)} was the standout mover, gaining {change} places.")

        if race.fastest_lap:
            sentences.append(f"Fastest lap: {self._driver_label(race.fastest_lap)}.")

        self._p(f"\n{title} report:")
        self._p("  " + " ".join(sentences))

    def run_weekend(self, round_no: int, track):
        self._p(f"\n=== Round {round_no}: {track.name} ({track.country}) ===")

        self._active_track = track
        for team in self.teams:
            team.weekend_form = self.rng.gauss(0.0, 2.0)
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
                self._print_race_report(sprint_race, "Sprint")

        quali = sim.simulate_qualifying(self.teams, track, self.rng)
        if not self.quiet:
            self._print_qualifying(quali)
            self._print_starting_grid(quali)

        race = sim.simulate_race(self.teams, track, quali.grid, self.rng)
        earned = sim.award_points(race, self.teams)

        if not self.quiet:
            self._print_race(race, earned)
            self._print_race_report(race)

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
            print(f"  {i:2d}. {d.flag} {d.name:<22} {d.team:<18} {d.season_points:5.0f} pts "
                  f"({d.season_wins}W, {d.season_podiums}P, {d.season_dnfs} DNF)")

        print(f"\n--- {self.year} Final Constructors' Championship ---")
        for i, t in enumerate(self.constructor_standings(), start=1):
            print(f"  {i:2d}. {t.name:<18} {t.season_points:5.0f} pts ({t.season_wins}W)")
