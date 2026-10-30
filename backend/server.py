#!/usr/bin/env python3
"""Local web server and JSON API for the F1 season simulator."""

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

import services

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_BUILD = ROOT / "frontend" / "dist"

MAX_BODY_BYTES = 4096
MAX_SEASONS = 200
MAX_HISTORY_SEASONS = 1000
MAX_UNTIL_SEASONS = 5000
MAX_TRIALS = 5000
MAX_NAME_LENGTH = 60
MIN_YEAR, MAX_YEAR = 2026, 2100


def _int(payload, key, default, low, high, label):
    value = payload.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f"{label} must be an integer between {low} and {high}")
    return value


def _seed(payload):
    seed = payload.get("seed")
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
        raise ValueError("Seed must be an integer or null")
    return seed


def _year(payload):
    return _int(payload, "year", 2026, MIN_YEAR, MAX_YEAR, "Year")


def _start_year(payload):
    return _int(payload, "start_year", 2026, MIN_YEAR, MAX_YEAR, "Start year")


def _round(payload):
    return _int(payload, "round", 1, 1, len(services.build_2026_calendar()), "Round")


def _route_season(payload):
    return services.simulate_season(_year(payload), _seed(payload))


def _route_seasons(payload):
    seasons = _int(payload, "seasons", 10, 1, MAX_SEASONS, "Seasons")
    return services.simulate_multi(seasons, _seed(payload), _start_year(payload))


def _route_round(payload):
    return services.simulate_weekend(_round(payload), _seed(payload))


def _route_predict(payload):
    trials = _int(payload, "trials", 500, 1, MAX_TRIALS, "Trials")
    return services.predict_round(_round(payload), trials, _seed(payload))


def _route_history(payload):
    seasons = _int(payload, "seasons", 100, 1, MAX_HISTORY_SEASONS, "Seasons")
    return services.simulate_history(seasons, _seed(payload), _start_year(payload))


def _route_until(payload):
    condition = payload.get("condition")
    if condition not in services.UNTIL_CONDITIONS:
        raise ValueError("Condition must be one of: " + ", ".join(services.UNTIL_CONDITIONS))
    target = payload.get("target")
    if target is not None:
        if not isinstance(target, str) or len(target) > MAX_NAME_LENGTH:
            raise ValueError("Target must be a short text value")
        target = target.strip() or None
    if condition in ("champion", "constructor", "win") and not target:
        raise ValueError("Enter a driver or team name for this condition")
    threshold = None
    if condition == "winners":
        threshold = _int(payload, "threshold", 10, 1, 100, "Winner threshold")
    max_seasons = _int(payload, "max_seasons", 1000, 1, MAX_UNTIL_SEASONS, "Max seasons")
    return services.run_until(
        condition, target, threshold, _seed(payload), _start_year(payload), max_seasons
    )


POST_ROUTES = {
    "/api/simulate": _route_season,
    "/api/seasons": _route_seasons,
    "/api/round": _route_round,
    "/api/predict": _route_predict,
    "/api/history": _route_history,
    "/api/until": _route_until,
}

GET_ROUTES = {
    "/api/initial": services.initial_data,
    "/api/meta": services.meta,
    "/api/academies": services.academies,
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
        if length < 0 or length > MAX_BODY_BYTES:
            raise ValueError("Request body must be smaller than 4 KB")
        try:
            return json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError("Request body must contain valid JSON") from error

    def do_GET(self):
        path = urlsplit(self.path).path
        if path in GET_ROUTES:
            self._send_json(200, GET_ROUTES[path]())
            return
        if path.startswith("/api/"):
            self._send_json(404, {"error": "API endpoint not found"})
            return

        requested = unquote(path).lstrip("/") or "index.html"
        file_path = (FRONTEND_BUILD / requested).resolve()
        if not file_path.is_relative_to(FRONTEND_BUILD.resolve()):
            self.send_error(404, "File not found")
            return
        if not file_path.is_file() and requested == "index.html":
            self.send_error(503, "Frontend is not built. Run `cd frontend && npm run build` first.")
            return
        if not file_path.is_file():
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
        route = POST_ROUTES.get(urlsplit(self.path).path)
        if route is None:
            self._send_json(404, {"error": "API endpoint not found"})
            return
        try:
            payload = self._read_json()
            if not isinstance(payload, dict):
                raise ValueError("Request body must be a JSON object")
            result = route(payload)
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
            return
        self._send_json(200, result)

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
