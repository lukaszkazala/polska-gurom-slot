"""Real local HTTP/socket failures, without disabling the computer's network.

Run from any directory: python test-interface/qa/test_network_faults.py
The fault relay is test-only. Every paid result comes from the unmodified server.
Documented temporary-server limits are observations, not durability guarantees.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import sys
import threading
import time
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server as app


OBSERVATIONS = []


class Client:
    def __init__(self, port, cookie=None, timeout=3, session_id=None):
        self.port, self.cookie, self.timeout = port, cookie, timeout
        self.session_id = session_id

    def request(self, method, path, body=None):
        data = None if body is None else json.dumps(body).encode()
        headers = {}
        if self.cookie:
            headers["Cookie"] = self.cookie
        if method == "POST" and path == "/api/spin" and self.session_id:
            headers["X-Game-Session"] = self.session_id
        if data is not None:
            headers["Content-Type"] = "application/json"
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=self.timeout)
        try:
            connection.request(method, path, data, headers)
            response = connection.getresponse()
            cookie = response.getheader("Set-Cookie")
            if cookie:
                self.cookie = cookie.split(";", 1)[0]
            raw = response.read()
            decoded = json.loads(raw)
            if response.status == 200 and path in ("/api/state", "/api/reset"):
                self.session_id = decoded["session_id"]
            return response.status, decoded
        finally:
            connection.close()

    def state(self):
        status, data = self.request("GET", "/api/state")
        if status != 200:
            raise AssertionError((status, data))
        return data

    def spin(self, request_id, bet=100):
        return self.request("POST", "/api/spin", {
            "request_id": request_id, "mode": "random", "bet_cents": bet})


class Relay(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, upstream_port):
        self.upstream_port = upstream_port
        self.fault = None
        self.guard = threading.Lock()
        self.forwarded = []
        self.settled = threading.Event()
        self.release = threading.Event()
        super().__init__(("127.0.0.1", 0), RelayHandler)

    def arm(self, fault):
        with self.guard:
            self.fault = fault
            self.settled.clear()
            self.release.clear()


class RelayHandler(BaseHTTPRequestHandler):
    """Forward real HTTP; fail before forwarding or after a complete upstream reply."""
    def log_message(self, *_):
        pass

    def do_GET(self):
        self.forward()

    def do_POST(self):
        self.forward()

    def forward(self):
        relay = self.server
        with relay.guard:
            fault = relay.fault if self.command == "POST" else None
            if self.command == "POST":
                relay.fault = None
        if fault == "503_before":
            return self.reply(503, b'{"error":"test relay unavailable"}')
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        headers = {key: value for key, value in self.headers.items()
                   if key.lower() not in ("host", "connection", "content-length")}
        headers["Host"] = f"127.0.0.1:{relay.upstream_port}"
        upstream = http.client.HTTPConnection("127.0.0.1", relay.upstream_port, timeout=5)
        try:
            upstream.request(self.command, self.path, body or None, headers)
            response = upstream.getresponse()
            payload = response.read()
            status = response.status
            cookie = response.getheader("Set-Cookie")
        except (ConnectionError, OSError, http.client.HTTPException):
            return self.reply(503, b'{"error":"test upstream unavailable"}')
        finally:
            upstream.close()
        if self.command == "POST":
            with relay.guard:
                relay.forwarded.append({"request": json.loads(body), "status": status,
                                        "response": json.loads(payload)})
            relay.settled.set()
        if fault == "drop_after":
            self.close_connection = True
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            return
        if fault == "503_after":
            return self.reply(503, b'{"error":"test response lost after settlement"}')
        if fault == "delay_after":
            relay.release.wait(timeout=3)
        return self.reply(status, payload, cookie, truncate=(fault == "truncate_after"))

    def reply(self, status, payload, cookie=None, truncate=False):
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            if cookie:
                self.send_header("Set-Cookie", cookie)
            self.end_headers()
            self.wfile.write(payload[:len(payload) // 2] if truncate else payload)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        self.close_connection = True


def run_thread(server):
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.02), daemon=True)
    thread.start()
    return thread


def stop(server, thread):
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)


class NetworkFaultTests(unittest.TestCase):
    def setUp(self):
        self.upstream = app.InterfaceServer(("127.0.0.1", 0))
        self.upstream_thread = run_thread(self.upstream)
        self.relay = Relay(self.upstream.server_port)
        self.relay_thread = run_thread(self.relay)
        self.client = Client(self.relay.server_port)
        self.before = self.client.state()

    def tearDown(self):
        self.relay.release.set()
        stop(self.relay, self.relay_thread)
        stop(self.upstream, self.upstream_thread)

    def note(self, scenario, outcome, *, limitation=False):
        OBSERVATIONS.append({"test": self._testMethodName, "scenario": scenario,
                             "outcome": outcome, "limitation": limitation})

    def assert_settled_once(self, data):
        state = self.client.state()
        self.assertEqual(data["session_id"], state["session_id"])
        self.assertIsInstance(data["request_id"], str)
        self.assertTrue(data["request_id"])
        self.assertEqual(state["rounds"], 1)
        self.assertEqual(state["total_bet_cents"], data["bet_cents"])
        self.assertEqual(state["total_win_cents"], data["win_cents"])
        self.assertEqual(state["balance_cents"], self.before["balance_cents"] - data["bet_cents"] + data["win_cents"])
        self.assertEqual(state["recent_rounds"], [data])

    def test_01_response_dropped_after_settlement_retry_same_id(self):
        request_id = str(uuid.uuid4())
        self.relay.arm("drop_after")
        with self.assertRaises((http.client.RemoteDisconnected, ConnectionResetError)):
            self.client.spin(request_id)
        self.assertTrue(self.relay.settled.wait(2))
        settled = self.relay.forwarded[-1]["response"]
        status, retried = self.client.spin(request_id)
        self.assertEqual(status, 200)
        self.assertEqual(retried, settled)
        self.assert_settled_once(retried)
        self.note("Connection disappears after debit/result, before response", "Same-ID retry returned identical round; one debit and one settlement")

    def test_02_truncated_response_retry_same_id(self):
        request_id = str(uuid.uuid4())
        self.relay.arm("truncate_after")
        with self.assertRaises(http.client.IncompleteRead):
            self.client.spin(request_id)
        status, retried = self.client.spin(request_id)
        self.assertEqual(status, 200)
        self.assertEqual(retried, self.relay.forwarded[0]["response"])
        self.assert_settled_once(retried)
        self.note("Only half the JSON response arrives", "Retry recovered complete identical round; no duplicate debit")

    def test_03_unavailable_before_forwarding_then_recovery(self):
        request_id = str(uuid.uuid4())
        self.relay.arm("503_before")
        self.assertEqual(self.client.spin(request_id)[0], 503)
        self.assertEqual(self.client.state(), self.before)
        status, recovered = self.client.spin(request_id)
        self.assertEqual(status, 200)
        self.assert_settled_once(recovered)
        self.note("Gateway 503 before request reaches engine", "No wallet change during outage; same-ID recovery settled once")

    def test_04_gateway_503_after_settlement_then_recovery(self):
        request_id = str(uuid.uuid4())
        self.relay.arm("503_after")
        self.assertEqual(self.client.spin(request_id)[0], 503)
        status, recovered = self.client.spin(request_id)
        self.assertEqual(status, 200)
        self.assertEqual(recovered, self.relay.forwarded[0]["response"])
        self.assert_settled_once(recovered)
        self.note("Gateway 503 after engine has already settled", "Same-ID recovery returned settled result without second charge")

    def test_05_delayed_response_client_timeout_and_retry(self):
        request_id = str(uuid.uuid4())
        self.relay.arm("delay_after")
        slow = Client(self.relay.server_port, self.client.cookie, timeout=0.08,
                      session_id=self.client.session_id)
        with self.assertRaises((TimeoutError, socket.timeout)):
            slow.spin(request_id)
        self.assertTrue(self.relay.settled.wait(2))
        status, recovered = self.client.spin(request_id)
        self.assertEqual(status, 200)
        self.assertEqual(recovered, self.relay.forwarded[0]["response"])
        self.relay.release.set()
        self.assert_settled_once(recovered)
        self.note("Response delayed beyond client timeout while original socket remains open", "Concurrent same-ID retry recovered one settled round")

    def test_06_parallel_retries_after_lost_response(self):
        request_id = str(uuid.uuid4())
        self.relay.arm("drop_after")
        with self.assertRaises((http.client.RemoteDisconnected, ConnectionResetError)):
            self.client.spin(request_id)
        cookie = self.client.cookie
        def retry(_):
            return Client(self.relay.server_port, cookie,
                          session_id=self.client.session_id).spin(request_id)
        with ThreadPoolExecutor(max_workers=8) as workers:
            results = list(workers.map(retry, range(8)))
        self.assertTrue(all(status == 200 for status, _ in results))
        self.assertTrue(all(data == results[0][1] for _, data in results))
        self.assert_settled_once(results[0][1])
        self.note("Eight simultaneous reconnect retries after response loss", "All eight received same round ID and one wallet settlement")

    def raw_request(self, payload):
        with socket.create_connection(("127.0.0.1", self.upstream.server_port), timeout=2) as connection:
            connection.sendall(payload)
            connection.shutdown(socket.SHUT_WR)
            connection.settimeout(2)
            chunks = []
            while True:
                chunk = connection.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
            return b"".join(chunks)

    def test_07_connection_closes_before_headers_complete(self):
        # Closing before the blank line never supplies a valid POST body.
        self.raw_request((f"POST /api/spin HTTP/1.1\r\nHost: 127.0.0.1:{self.upstream.server_port}\r\n"
                          "Content-Type: application/json\r\n").encode())
        self.assertEqual(self.client.state(), self.before)
        self.note("Connection closes before HTTP headers/body complete", "Incomplete request caused no debit or round")

    def test_08_connection_closes_during_request_body(self):
        raw = json.dumps({"request_id": "partial-body", "bet_cents": 100, "mode": "random"}).encode()
        headers = (f"POST /api/spin HTTP/1.1\r\nHost: 127.0.0.1:{self.upstream.server_port}\r\n"
                   f"Cookie: {self.client.cookie}\r\nX-Game-Session: {self.client.session_id}\r\nContent-Type: application/json\r\nContent-Length: {len(raw)}\r\n\r\n").encode()
        response = self.raw_request(headers + raw[:len(raw) // 2])
        self.assertIn(b"400 Bad Request", response)
        self.assertEqual(self.client.state(), self.before)
        status, complete = self.client.spin("partial-body")
        self.assertEqual(status, 200)
        self.assert_settled_once(complete)
        self.note("Upload closes halfway through JSON request", "400 response with no debit; complete retry settled once")

    def test_09_server_unavailable_then_new_instance(self):
        old_port = self.upstream.server_port
        stop(self.upstream, self.upstream_thread)
        request_id = "unavailable-before-round"
        self.assertEqual(self.client.spin(request_id)[0], 503)
        self.upstream = app.InterfaceServer(("127.0.0.1", old_port))
        self.upstream_thread = run_thread(self.upstream)
        status, rejected = self.client.spin(request_id)
        self.assertEqual(status, 409)
        self.assertEqual(rejected["code"], "session_expired")
        self.assertEqual(len(self.upstream.sessions), 0)
        fresh = self.client.state()
        self.assertEqual(fresh["rounds"], 0)
        status, result = self.client.spin("explicit-round-after-reconnect")
        self.assertEqual(status, 200)
        self.assert_settled_once(result)
        self.assertNotEqual(self.client.state()["session_id"], self.before["session_id"])
        self.note("Local engine unavailable before a round, then restarted", "Outage produced 503; stale-cookie replay rejected409 without creating or charging a session; explicit state reload allowed fresh play", limitation=True)

    def test_10_restart_blocks_silent_resettlement_of_lost_result(self):
        request_id = "settled-before-restart"
        old_session = self.client.session_id
        self.relay.arm("drop_after")
        with self.assertRaises((http.client.RemoteDisconnected, ConnectionResetError)):
            self.client.spin(request_id)
        first = self.relay.forwarded[-1]["response"]
        old_port = self.upstream.server_port
        stop(self.upstream, self.upstream_thread)
        self.upstream = app.InterfaceServer(("127.0.0.1", old_port))
        self.upstream_thread = run_thread(self.upstream)
        status, rejected = self.client.spin(request_id)
        self.assertEqual(status, 409)
        self.assertEqual(rejected["code"], "session_expired")
        self.assertEqual(len(self.upstream.sessions), 0)
        fresh = self.client.state()
        self.assertNotEqual(fresh["session_id"], old_session)
        self.assertEqual(fresh["balance_cents"], app.INITIAL_BALANCE_CENTS)
        self.assertEqual(fresh["rounds"], 0)
        status, after_restart = self.client.spin("new-explicit-round-after-restart")
        self.assertEqual(status, 200)
        self.assertNotEqual(after_restart["round_id"], first["round_id"])
        self.assertEqual(self.client.state()["rounds"], 1)
        self.note("Restart after paid settlement and lost response, then replay old request ID", "Stale session rejected409 and never resettled automatically; original virtual wallet/history remain unrecoverable because memory was lost", limitation=True)

    def test_11_missing_cookie_cannot_start_unrecoverable_spin(self):
        request_id = "first-spin-without-session"
        fresh = Client(self.relay.server_port)
        before_sessions = len(self.upstream.sessions)
        status, rejected = fresh.spin(request_id)
        self.assertEqual(status, 409)
        self.assertEqual(rejected["code"], "session_expired")
        self.assertIsNone(fresh.cookie)
        self.assertEqual(len(self.upstream.sessions), before_sessions)
        fresh.state()
        status, retried = fresh.spin("explicit-after-state-bootstrap")
        self.assertEqual(status, 200)
        self.assertEqual(fresh.state()["rounds"], 1)
        self.note("Spin attempted with no established session cookie", "409 session_expired with no new session or debit; state bootstrap required before first paid spin")

    def test_12_recent_cache_eviction_rejects_old_id_without_charge(self):
        status, first = self.client.spin("old-paid-id")
        self.assertEqual(status, 200)
        # Scenario requests exercise the real bounded cache without 100 paid draws.
        for index in range(app.MAX_RESULTS):
            status, _ = self.client.request("POST", "/api/spin", {
                "request_id": f"cache-filler-{index}", "mode": "win", "bet_cents": 100})
            self.assertEqual(status, 200)
        before_retry = self.client.state()
        self.assertNotIn(first["round_id"], [entry["round_id"] for entry in before_retry["recent_rounds"]])
        status, old_id_again = self.client.spin("old-paid-id")
        self.assertEqual(status, 409)
        self.assertEqual(old_id_again["code"], "result_expired")
        self.assertEqual(self.client.state(), before_retry)
        self.assertEqual(self.client.state()["rounds"], 1)
        self.note("Retry old paid ID after its full result leaves the 100-entry response cache", "Tombstone retained:409 result_expired and no duplicate settlement; old full response is no longer replayable", limitation=True)

    def test_13_page_reload_with_same_cookie_recovers_lost_result(self):
        request_id = "reload-after-disconnect"
        self.relay.arm("drop_after")
        with self.assertRaises((http.client.RemoteDisconnected, ConnectionResetError)):
            self.client.spin(request_id)
        reloaded = Client(self.relay.server_port, self.client.cookie)
        state = reloaded.state()
        settled = self.relay.forwarded[-1]["response"]
        self.assertEqual(state["recent_rounds"], [settled])
        self.assertEqual(state["rounds"], 1)
        self.assertEqual(state["balance_cents"], settled["balance_cents"])
        self.note("Page reload after lost response with existing session cookie", "State endpoint recovered settled round and balance without another spin")

    def test_14_expired_session_rejected_before_new_settlement(self):
        token = self.client.cookie.split("=", 1)[1]
        session = self.upstream.sessions[token]
        # Age the fixture instead of waiting24hours; the request uses realHTTP.
        with self.upstream.sessions_lock:
            session.last_access = time.monotonic() - 86401
        status, rejected = self.client.spin("session-expired-in-fixture")
        self.assertEqual(status, 409)
        self.assertEqual(rejected["code"], "session_expired")
        self.assertEqual(session.rounds, 0)
        self.assertEqual(session.balance_cents, self.before["balance_cents"])
        self.assertEqual(len(self.upstream.sessions), 1)
        self.note("24h expiry simulated by aging isolated session fixture", "RealHTTP spin rejected409 without debit or replacement session; no 24h wall-clock wait was used")

    def test_15_missing_or_mismatched_session_header_rejected(self):
        for session_id in (None, "incorrect-session-id"):
            client = Client(self.relay.server_port, self.client.cookie, session_id=session_id)
            status, rejected = client.spin("missing-or-stale-header")
            self.assertEqual(status, 409)
            self.assertEqual(rejected["code"], "session_changed")
        self.assertEqual(self.client.state(), self.before)
        self.note("Cookie survives but session-identity header is missing or stale", "Both rejected409 session_changed; zero wallet changes")

    def test_16_reset_blocks_retry_from_old_session_epoch(self):
        stale = Client(self.relay.server_port, self.client.cookie,
                       session_id=self.client.session_id)
        self.relay.arm("drop_after")
        with self.assertRaises((http.client.RemoteDisconnected, ConnectionResetError)):
            stale.spin("settled-before-reset")
        old_epoch = self.client.session_id
        status, reset = self.client.request("POST", "/api/reset", {})
        self.assertEqual(status, 200)
        self.assertNotEqual(reset["session_id"], old_epoch)
        status, rejected = stale.spin("settled-before-reset")
        self.assertEqual(status, 409)
        self.assertEqual(rejected["code"], "session_changed")
        self.assertEqual(self.client.state(), reset)
        self.note("Another tab resets while disconnected tab retries old paid request", "Rotated session identity blocked stale retry409; reset wallet remained untouched")

    def test_17_idempotency_capacity_rejects_and_explicit_reset_recovers(self):
        token = self.client.cookie.split("=", 1)[1]
        session = self.upstream.sessions[token]
        # Fill only the isolated bookkeeping fixture; exercising100k network
        # requests adds no coverage to the capacity branch itself.
        with session.lock:
            session.processed_ids.update(f"already-processed-{index}"
                                         for index in range(app.MAX_PROCESSED_IDS))
        status, rejected = self.client.spin("after-idempotency-capacity")
        self.assertEqual(status, 409)
        self.assertEqual(rejected["code"], "session_limit")
        self.assertEqual(self.client.state(), self.before)
        status, reset = self.client.request("POST", "/api/reset", {})
        self.assertEqual(status, 200)
        self.assertNotEqual(reset["session_id"], self.before["session_id"])
        status, recovered = self.client.spin("explicit-round-after-capacity-reset")
        self.assertEqual(status, 200)
        self.assert_settled_once(recovered)
        self.note("100k processed-ID guard simulated by filling isolated bookkeeping fixture", "New paid request rejected409 without debit; explicit reset rotated identity and allowed fresh play")


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append({"test": test._testMethodName, "status": "passed"})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records.append({"test": test._testMethodName, "status": "failed", "detail": self._exc_info_to_string(err, test)})

    def addError(self, test, err):
        super().addError(test, err)
        self.records.append({"test": test._testMethodName, "status": "error", "detail": self._exc_info_to_string(err, test)})


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NetworkFaultTests)
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordingResult).run(suite)
    payload = {
        "math_version": app.config.MATH_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "Real local HTTP and TCP sockets, unmodified InterfaceServer, isolated test-only fault relay",
        "machine_internet_changed": False,
        "live_user_server_touched": False,
        "paid_mode": "random with current weighted complete-round distribution",
        "tests_run": result.testsRun,
        "passed": sum(item["status"] == "passed" for item in result.records),
        "failed": len(result.failures), "errors": len(result.errors),
        "tests": result.records, "observations": OBSERVATIONS,
        "scope": "Loopback client-server transport failures; no real Stake RGS or wallet provider is connected",
        "limitations": [item for item in OBSERVATIONS if item["limitation"]],
    }
    report_directory = Path(os.environ.get("PG_QA_OUT_DIR", Path(__file__).parent))
    report_directory.mkdir(parents=True, exist_ok=True)
    output = report_directory / "network_faults_results.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
