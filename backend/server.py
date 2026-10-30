#!/usr/bin/env python3
"""Local web server and JSON API for the F1 season simulator."""

import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
sys.path.insert(0, str(ROOT))

from f1sim.data import build_2026_calendar, build_2026_grid
from f1sim.season import Season


def _driver_data(driver):
    return {
        "name": driver.name,
        "number": driver.number,
        "nationality": driver.nationality,
        "flag": driver.flag,
        "team": driver.team,
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
    classified = [
        {
            "name": name,
            "team": driver_teams[name],
            "position": position,
            "grid": race.grid.index(name) + 1,
            "points": points.get(name, 0),
            "status": "Finished",
            "fastest_lap": name == race.fastest_lap,
            "time": round(race.race_times.get(name, 0), 3),
            "laps": race.laps_completed.get(name, 0),
            "pit_stops": race.pit_stops.get(name, 0),
            "strategy": race.tyre_strategy.get(name, []),
        }
        for position, name in enumerate(race.classified, start=1)
    ]
    retired = [
        {
            "name": name,
            "team": driver_teams[name],
            "position": None,
            "grid": race.grid.index(name) + 1,
            "points": points.get(name, 0),
            "status": "DNF",
            "fastest_lap": False,
            "time": round(race.race_times.get(name, 0), 3),
            "laps": race.laps_completed.get(name, 0),
            "pit_stops": race.pit_stops.get(name, 0),
            "strategy": race.tyre_strategy.get(name, []),
        }
        for name in race.dnfs
    ]
    return {
        "winner": race.classified[0] if race.classified else None,
        "fastest_lap": race.fastest_lap,
        "wet": race.wet,
        "extreme_wet": race.extreme_wet,
        "safety_cars": race.safety_cars,
        "results": classified + retired,
    }


def simulate_season(year=2026, seed=None):
    teams = build_2026_grid()
    calendar = build_2026_calendar()
    season = Season(year, teams, calendar, seed=seed, quiet=True)
    driver_teams = {
        driver.name: team.name
        for team in teams
        for driver in team.drivers
    }

    races = []
    for round_number, track in enumerate(calendar, start=1):
        season.run_weekend(round_number, track)
        weekend = season.race_log[-1]
        race = weekend["race"]
        qualifying = weekend["quali"]
        sprint_race = weekend["sprint_race"]
        races.append({
            "round": round_number,
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
        "calendar": [
            {
                "round": round_number,
                "name": track.name,
                "country": track.country,
                "laps": track.laps,
                "is_sprint": track.is_sprint,
            }
            for round_number, track in enumerate(build_2026_calendar(), start=1)
        ],
    }


class SimulatorHandler(BaseHTTPRequestHandler):
    server_version = "F1Simulator/1.0"

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Invalid Content-Length header") from error
        if length < 0 or length > 4096:
            raise ValueError("Request body must be smaller than 4 KB")
        try:
            return json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError("Request body must contain valid JSON") from error

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/initial":
            self._send_json(200, initial_data())
            return
        if path.startswith("/api/"):
            self._send_json(404, {"error": "API endpoint not found"})
            return

        requested = unquote(path).lstrip("/") or "index.html"
        file_path = (FRONTEND / requested).resolve()
        if not file_path.is_relative_to(FRONTEND.resolve()) or not file_path.is_file():
            self.send_error(404, "File not found")
            return
        body = file_path.read_bytes()
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/simulate":
            self._send_json(404, {"error": "API endpoint not found"})
            return
        try:
            payload = self._read_json()
            if not isinstance(payload, dict):
                raise ValueError("Request body must be a JSON object")
            year = payload.get("year", 2026)
            seed = payload.get("seed")
            if isinstance(year, bool) or not isinstance(year, int) or not 2026 <= year <= 2100:
                raise ValueError("Year must be an integer between 2026 and 2100")
            if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
                raise ValueError("Seed must be an integer or null")
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
            return
        self._send_json(200, simulate_season(year, seed))

    def log_message(self, format_string, *args):
        print(f"{self.address_string()} - {format_string % args}")


def main():
    host = "127.0.0.1"
    port = 8000
    server = ThreadingHTTPServer((host, port), SimulatorHandler)
    print(f"F1 Season Simulator running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping F1 Season Simulator.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
