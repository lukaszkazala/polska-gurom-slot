"""Local, dependency-free interface for the POLSKA GUROM test engine.

Run ``python server.py``. Money is virtual and held only in server memory.
The complete engine result is settled before any frontend animation starts.
"""
from __future__ import annotations

import argparse
from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import random
import re
import secrets
import sys
import threading
import time
from urllib.parse import unquote, urlsplit
import uuid
import webbrowser


ROOT = Path(__file__).resolve().parent
BUNDLED_ENGINE = ROOT / "engine"
ENGINE_ROOT = (BUNDLED_ENGINE if (BUNDLED_ENGINE / "polska_gurom").is_dir()
               else ROOT.parent / "polska_gurom_v0_2")
sys.path.insert(0, str(ENGINE_ROOT))
try:
    from polska_gurom import config, game, selection
except ImportError as exc:
    raise SystemExit("Brak silnika gry. Zachowaj folder engine obok server.py.") from exc

BET_OPTIONS_CENTS = (100, 200, 500, 1000, 2000, 5000, 10000)
INITIAL_BALANCE_CENTS = 1_000_000
COOKIE_NAME = "pg_session"
MAX_BODY_BYTES = 4096
MAX_RESULTS = 100
MAX_PROCESSED_IDS = 100_000
SCENARIO_SEEDS = {"win": 0, "bonus": 508, "expansion": 287, "cascade": 2, "middle": None}
MIDDLE_RECIPE = {"name": "middle_run_regression", "stops": [11, 8, 12, 17, 6],
                 "wild_refill_limit": 0, "fallback_seed": 20261020}
REQUEST_ID = re.compile(r"[A-Za-z0-9_.:-]{1,128}\Z")


@dataclass
class Session:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    balance_cents: int = INITIAL_BALANCE_CENTS
    rounds: int = 0
    total_bet_cents: int = 0
    total_win_cents: int = 0
    rng: random.Random = field(default_factory=random.Random)
    lock: threading.RLock = field(default_factory=threading.RLock)
    results: OrderedDict = field(default_factory=OrderedDict)
    processed_ids: set[str] = field(default_factory=set)
    last_access: float = field(default_factory=time.monotonic)

    def stats(self):
        return {"rounds": self.rounds, "total_bet_cents": self.total_bet_cents,
                "total_win_cents": self.total_win_cents}

    def state(self):
        return {"balance_cents": self.balance_cents,
                "session_id": self.session_id, **self.stats(),
                "recent_rounds": [response for _, response in reversed(self.results.values())]}

    def reset(self):
        self.session_id = str(uuid.uuid4())
        self.balance_cents = INITIAL_BALANCE_CENTS
        self.rounds = self.total_bet_cents = self.total_win_cents = 0
        self.results.clear()
        self.processed_ids.clear()


@lru_cache(maxsize=4)
def scenario_round(mode: str):
    """Replay reachable rounds with the current engine's random probabilities."""
    result = (selection.replay_spec({"recipe": MIDDLE_RECIPE}) if mode == "middle"
              else game.play_round(random.Random(SCENARIO_SEEDS[mode])))
    valid = {
        "win": bool(result.base.line_wins) and not result.free_spins,
        "bonus": result.base.bonus_triggered and bool(result.free_spins),
        "expansion": result.base.bonus_triggered and bool(result.expansions),
        "cascade": len(result.base.cascades) >= 3,
        "middle": any(w.symbol == "L1" and w.start_reel == 1 and w.count == 3
                      for w in result.base.line_wins),
    }
    if not valid[mode]:
        raise RuntimeError("Scenariusz nie pasuje do aktualnej wersji silnika.")
    return result


class InterfaceServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address=("127.0.0.1", 8765), web_root=None):
        if address[0] != "127.0.0.1":
            raise ValueError("This test server must listen on 127.0.0.1.")
        self.web_root = Path(web_root or ROOT / "web").resolve()
        self.sessions: dict[str, Session] = {}
        self.sessions_lock = threading.Lock()
        selection.load_distribution()
        super().__init__(address, InterfaceHandler)

    def session_for(self, token, *, require_existing=False):
        now = time.monotonic()
        with self.sessions_lock:
            session = self.sessions.get(token)
            if session is not None and now - session.last_access < 86400:
                session.last_access = now
                return session, None
            if require_existing:
                raise APIError(409, "session_expired", "Sesja zakończyła się. Odśwież stronę, aby rozpocząć nową sesję testową.")
            # Sessions are temporary. Bound memory if a browser sends many new cookies.
            expired = [key for key, item in self.sessions.items()
                       if now - item.last_access >= 86400]
            for key in expired:
                self.sessions.pop(key, None)
            if len(self.sessions) >= 1024:
                oldest = min(self.sessions, key=lambda key: self.sessions[key].last_access)
                self.sessions.pop(oldest, None)
            token = secrets.token_urlsafe(32)
            session = Session()
            self.sessions[token] = session
            return session, token


class APIError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message


class InterfaceHandler(BaseHTTPRequestHandler):
    server_version = "PolskaGuromLocal/1.0"

    def log_message(self, format, *args):
        # Keep the launch window useful without logging cookies or request bodies.
        if args and str(args[0]).startswith("POST"):
            return
        super().log_message(format, *args)

    def _headers(self, status, content_type, length, *, api=False, cookie=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store" if api else "no-cache")
        if cookie:
            self.send_header("Set-Cookie", f"{COOKIE_NAME}={cookie}; Path=/; HttpOnly; SameSite=Strict")
        self.end_headers()

    def _json(self, payload, status=200, cookie=None):
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
        self._headers(status, "application/json; charset=utf-8", len(data), api=True, cookie=cookie)
        if self.command != "HEAD":
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass  # The completed round stays in the idempotency cache.

    def _guard(self):
        """Reject DNS rebinding, cross-origin requests and browser cross-site posts."""
        host = self.headers.get("Host", "")
        if len(self.headers.get_all("Host", [])) != 1:
            raise APIError(403, "invalid_host", "Niedozwolony adres serwera.")
        allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        if host.lower() not in allowed:
            raise APIError(403, "invalid_host", "Użyj lokalnego adresu podanego w oknie serwera.")
        origin = self.headers.get("Origin")
        if origin is not None and origin != f"http://{host.lower()}":
            raise APIError(403, "invalid_origin", "Żądanie z innej strony zostało odrzucone.")
        if self.headers.get("Sec-Fetch-Site", "").lower() == "cross-site":
            raise APIError(403, "cross_site", "Żądanie z innej strony zostało odrzucone.")

    def _session(self, *, require_existing=False):
        cookies = SimpleCookie()
        try:
            cookies.load(self.headers.get("Cookie", ""))
        except Exception:
            pass
        morsel = cookies.get(COOKIE_NAME)
        return self.server.session_for(morsel.value if morsel else None, require_existing=require_existing)

    def _body(self):
        if self.headers.get("Transfer-Encoding"):
            raise APIError(400, "invalid_body", "Nieobsługiwany format żądania.")
        if len(self.headers.get_all("Content-Length", [])) != 1:
            raise APIError(411, "missing_length", "Brak długości żądania.")
        try:
            length = int(self.headers["Content-Length"])
        except (ValueError, TypeError):
            raise APIError(400, "invalid_length", "Nieprawidłowa długość żądania.")
        if length < 0:
            raise APIError(400, "invalid_length", "Nieprawidłowa długość żądania.")
        if length > MAX_BODY_BYTES:
            raise APIError(413, "body_too_large", "Żądanie jest zbyt duże.")
        if self.headers.get_content_type() != "application/json":
            raise APIError(415, "invalid_content_type", "Wyślij dane w formacie JSON.")
        self.connection.settimeout(5)
        try:
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise ValueError("short request")
            def reject_constant(value):
                raise ValueError("non-finite value")
            data = json.loads(raw.decode("utf-8"), parse_constant=reject_constant)
        except (ValueError, UnicodeError, TimeoutError):
            raise APIError(400, "invalid_json", "Nieprawidłowy JSON.")
        if not isinstance(data, dict):
            raise APIError(400, "invalid_json", "JSON musi być obiektem.")
        return data

    def _dispatch(self):
        try:
            self._guard()
            path = urlsplit(self.path).path
            if self.command in ("GET", "HEAD"):
                self._get(path)
            elif self.command == "POST":
                self._post(path)
            else:
                raise APIError(405, "method_not_allowed", "Niedozwolona metoda.")
        except APIError as exc:
            self._json({"error": exc.message, "code": exc.code}, exc.status)
        except (ConnectionResetError, BrokenPipeError):
            pass
        except Exception:
            self.log_error("Internal request error on %s", urlsplit(self.path).path)
            self._json({"error": "Wystąpił błąd lokalnego serwera. Spróbuj ponownie.",
                        "code": "internal_error"}, 500)

    do_GET = _dispatch
    do_HEAD = _dispatch
    do_POST = _dispatch
    do_OPTIONS = _dispatch
    do_PUT = _dispatch
    do_DELETE = _dispatch

    def _get(self, path):
        if path == "/api/config":
            self._json({
                "symbols": config.SYMBOLS, "paylines": config.PAYLINES,
                "paytable_units": config.PAYTABLE_UNITS,
                "scatter_paytable_units": config.SCATTER_PAYTABLE_UNITS,
                "free_spins": config.FREE_SPINS, "payout_scale": config.PAYOUT_SCALE,
                "max_win_units": config.MAX_WIN_UNITS,
                "fs_line_multiplier": config.FS_LINE_MULTIPLIER,
                "math_version": getattr(config, "MATH_VERSION", "0.2.0"),
                "cascades_enabled": getattr(config, "CASCADES_ENABLED", False),
                "max_cascades": getattr(config, "MAX_CASCADES", 0),
                "theoretical_rtp": config.TARGET_RTP,
                "selection_model": "weighted_complete_round_books",
                "payline_start": "any_reel",
                "award_per_line": "highest_only",
                "bet_options_cents": BET_OPTIONS_CENTS,
                "initial_balance_cents": INITIAL_BALANCE_CENTS,
            })
        elif path == "/api/state":
            session, cookie = self._session()
            with session.lock:
                self._json(session.state(), cookie=cookie)
        elif path == "/api/health":
            self._json({"ok": True, "engine": "polska_gurom", "math_version": getattr(config, "MATH_VERSION", "0.2.0")})
        elif path.startswith("/api/"):
            raise APIError(404, "not_found", "Nie znaleziono tej funkcji.")
        else:
            try:
                file = (self.server.web_root / unquote(path).lstrip("/")).resolve()
                if not file.is_relative_to(self.server.web_root):
                    raise ValueError("outside web root")
                if file.is_dir():
                    file = file / "index.html"
                if not file.is_file():
                    raise FileNotFoundError()
                data = file.read_bytes()
            except (ValueError, OSError):
                raise APIError(404, "not_found", "Nie znaleziono pliku interfejsu.")
            mime = mimetypes.guess_type(str(file))[0] or "application/octet-stream"
            if mime.startswith("text/") or mime in ("application/javascript", "application/json"):
                mime += "; charset=utf-8"
            self._headers(200, mime, len(data))
            if self.command != "HEAD":
                self.wfile.write(data)

    def _post(self, path):
        if path not in ("/api/spin", "/api/reset"):
            raise APIError(404, "not_found", "Nie znaleziono tej funkcji.")
        body = self._body()
        if path == "/api/reset":
            if body:
                raise APIError(400, "invalid_request", "Reset nie przyjmuje parametrów.")
            session, cookie = self._session()
            with session.lock:
                session.reset()
                self._json(session.state(), cookie=cookie)
            return
        if set(body) != {"bet_cents", "mode", "request_id"}:
            raise APIError(400, "invalid_request", "Podaj stawkę, tryb i identyfikator rundy.")
        bet, mode, request_id = body["bet_cents"], body["mode"], body["request_id"]
        if type(bet) is not int or bet not in BET_OPTIONS_CENTS:
            raise APIError(400, "invalid_bet", "Wybierz jedną z dostępnych stawek.")
        if not isinstance(mode, str) or mode not in ("random", *SCENARIO_SEEDS):
            raise APIError(400, "invalid_mode", "Nieznany tryb testowania.")
        if not isinstance(request_id, str) or not REQUEST_ID.fullmatch(request_id):
            raise APIError(400, "invalid_request_id", "Nieprawidłowy identyfikator rundy.")
        session, cookie = self._session(require_existing=True)
        with session.lock:
            if self.headers.get("X-Game-Session") != session.session_id:
                raise APIError(409, "session_changed", "Sesja zmieniła się. Odśwież stronę przed kolejnym obrotem.")
            previous = session.results.get(request_id)
            if previous:
                fingerprint, response = previous
                if fingerprint != (bet, mode):
                    raise APIError(409, "request_conflict", "Ten identyfikator został już użyty z innymi parametrami.")
                self._json(response, cookie=cookie)
                return
            if request_id in session.processed_ids:
                raise APIError(409, "result_expired", "Ten obrót był już rozliczony. Jego szczegóły wygasły; odśwież stronę, aby odczytać aktualne saldo.")
            if len(session.processed_ids) >= MAX_PROCESSED_IDS:
                raise APIError(409, "session_limit", "Osiągnięto limit sesji testowej. Rozpocznij nową sesję.")
            is_scenario = mode != "random"
            before = session.balance_cents
            if not is_scenario and before < bet:
                raise APIError(409, "insufficient_funds", "Za mało środków testowych. Zmień stawkę lub zresetuj sesję.")
            book_id = None
            if is_scenario:
                result = scenario_round(mode)
            else:
                book_id, result = selection.select_round(session.rng)
            win_cents = bet * result.payout_units // config.PAYOUT_SCALE
            if not is_scenario:
                session.balance_cents += win_cents - bet
                session.rounds += 1
                session.total_bet_cents += bet
                session.total_win_cents += win_cents
            response = {
                "round_id": str(uuid.uuid4()), "mode": mode, "is_scenario": is_scenario,
                "request_id": request_id, "session_id": session.session_id,
                "book_id": book_id, "math_version": config.MATH_VERSION,
                "created_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                "bet_cents": bet, "balance_before_cents": before,
                "balance_cents": session.balance_cents, "win_cents": win_cents,
                "round": asdict(result), "stats": session.stats(),
            }
            if is_scenario:
                if mode == "middle":
                    response["scenario_recipe"] = MIDDLE_RECIPE
                else:
                    response["scenario_seed"] = SCENARIO_SEEDS[mode]
            session.results[request_id] = ((bet, mode), response)
            session.processed_ids.add(request_id)
            while len(session.results) > MAX_RESULTS:
                session.results.popitem(last=False)
            self._json(response, cookie=cookie)


def main():
    parser = argparse.ArgumentParser(description="Lokalny interfejs testowy POLSKA GUROM")
    parser.add_argument("--port", type=int, default=8765, help="Port lokalny (domyślnie 8765)")
    parser.add_argument("--no-browser", action="store_true", help="Nie otwieraj przeglądarki")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Port musi mieścić się w zakresie 1–65535.")
    try:
        server = InterfaceServer(("127.0.0.1", args.port))
    except OSError as exc:
        print(f"Nie można uruchomić serwera na porcie {args.port}: {exc}")
        print("Uruchom z opcją --port 8766, jeśli ten port jest zajęty.")
        return 1
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"POLSKA GUROM — lokalne testy: {url}", flush=True)
    print("Środki są wirtualne. Zamknięcie serwera usuwa sesje. Zatrzymaj: Ctrl+C.", flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSerwer zatrzymany.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
