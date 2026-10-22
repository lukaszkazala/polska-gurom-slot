"""Regression for a reachable 5-Scatter complete round and HTTP settlement.

The temporary server uses the production request handler, selector and replay.
Only ``load_distribution`` is replaced with a one-book fixture in this process;
there is no forced-outcome endpoint and no production configuration change.
Run with ``--require-exported`` after rebuilding to also require an actual
positive-weight 12-FS book from the published distribution.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from dataclasses import asdict
import http.client
import json
import os
from pathlib import Path
import random
import sys
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server as app

REQUIRE_EXPORTED = "--require-exported" in sys.argv
if REQUIRE_EXPORTED:
    sys.argv.remove("--require-exported")
OUT = Path(os.environ.get("PG_QA_OUT_DIR", ROOT.parent / "audit" / "bonus12_fix_2026_10_20"))
CHECKS = []
REAL_LOAD = app.selection.load_distribution


def fixture(wilds=0):
    spec = {"recipe": {
        "fallback_seed": 0,
        "stops": [strip.index(app.config.SCATTER) for strip in app.config.REEL_STRIPS],
        "wild_refill_limit": wilds,
    }}
    result = app.selection.replay_spec(spec)
    manifest = {"math_version": app.config.MATH_VERSION,
                "total_weight": 1, "books": [spec]}
    return (manifest, [1], [result.payout_units]), result


class Client:
    def __init__(self, port, cookie=None, session_id=None):
        self.port, self.cookie, self.session_id = port, cookie, session_id

    def call(self, method, path, payload=None):
        data = None if payload is None else json.dumps(payload).encode()
        headers = {}
        if self.cookie:
            headers["Cookie"] = self.cookie
        if data is not None:
            headers["Content-Type"] = "application/json"
        if path == "/api/spin" and self.session_id:
            headers["X-Game-Session"] = self.session_id
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request(method, path, data, headers)
            response = connection.getresponse()
            cookie = response.getheader("Set-Cookie")
            if cookie:
                self.cookie = cookie.split(";", 1)[0]
            result = json.loads(response.read())
            if response.status == 200 and path in ("/api/state", "/api/reset"):
                self.session_id = result["session_id"]
            return response.status, result
        finally:
            connection.close()

    def state(self):
        status, result = self.call("GET", "/api/state")
        if status != 200:
            raise AssertionError((status, result))
        return result

    def spin(self, request_id="bonus12", bet=100):
        return self.call("POST", "/api/spin", {
            "request_id": request_id, "mode": "random", "bet_cents": bet,
        })


class Bonus12Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.distribution, cls.round = fixture()
        cls.load_patch = patch.object(app.selection, "load_distribution",
                                      return_value=cls.distribution)
        cls.load_patch.start()
        cls.server = app.InterfaceServer(("127.0.0.1", 0))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.load_patch.stop()

    def setUp(self):
        self.client = Client(self.server.server_port)
        self.before = self.client.state()

    def assert_settled_once(self, data, bet=100):
        self.assertEqual(data["stats"]["rounds"], 1)
        self.assertEqual(data["stats"]["total_bet_cents"], bet)
        self.assertEqual(data["stats"]["total_win_cents"], data["win_cents"])
        self.assertEqual(data["balance_cents"], self.before["balance_cents"] - bet + data["win_cents"])
        self.assertEqual(data["win_cents"], bet * data["round"]["payout_units"] // app.config.PAYOUT_SCALE)

    def test_01_five_scatter_recipe_plays_twelve_reachable_free_spins(self):
        result = self.round
        self.assertEqual(result.base.scatter_count, 5)
        self.assertEqual(result.base.free_spins_awarded, 12)
        self.assertEqual(len(result.free_spins), 12)
        self.assertEqual(len(result.free_spin_credits), 12)
        self.assertFalse(result.cap_reduction_units)
        self.assertEqual(result.payout_units, result.base.payout_units + sum(result.free_spin_credits))
        self.assertTrue(all(not spin.bonus_triggered and spin.free_spins_awarded == 0
                            for spin in result.free_spins))

    def test_02_production_selector_replays_complete_fixture_book(self):
        book_id, result = app.selection.select_round(random.Random(736))
        self.assertEqual(book_id, 0)
        self.assertEqual(result, self.round)

    def test_03_http_settles_all_twelve_spins_with_one_bet(self):
        status, result = self.client.spin()
        self.assertEqual(status, 200)
        self.assertEqual(result["round"]["base"]["scatter_count"], 5)
        self.assertEqual(len(result["round"]["free_spins"]), 12)
        self.assertEqual(len(result["round"]["free_spin_credits"]), 12)
        self.assertEqual(result["round"]["bonus_payout_units"], sum(result["round"]["free_spin_credits"]))
        self.assert_settled_once(result)

    def test_04_lost_reply_retry_keeps_round_id_and_single_charge(self):
        first_status, discarded_reply = self.client.spin()
        retry_status, retry = self.client.spin()
        self.assertEqual((first_status, retry_status), (200, 200))
        self.assertEqual(retry, discarded_reply)
        self.assertEqual(retry["session_id"], self.client.session_id)
        self.assertEqual(retry["math_version"], app.config.MATH_VERSION)
        self.assert_settled_once(retry)
        state = self.client.state()
        self.assertEqual(state["rounds"], 1)
        self.assertEqual(state["total_bet_cents"], 100)
        self.assertEqual(state["balance_cents"], retry["balance_cents"])

    def test_05_concurrent_same_id_retries_settle_only_once(self):
        def submit(_):
            client = Client(self.server.server_port, self.client.cookie, self.client.session_id)
            return client.spin("bonus12-concurrent")
        with ThreadPoolExecutor(max_workers=4) as pool:
            replies = list(pool.map(submit, range(4)))
        self.assertTrue(all(status == 200 for status, _ in replies))
        self.assertTrue(all(result == replies[0][1] for _, result in replies))
        self.assert_settled_once(replies[0][1])
        self.assertEqual(self.client.state()["rounds"], 1)

    def test_06_state_restores_complete_twelve_spin_book(self):
        status, first = self.client.spin()
        self.assertEqual(status, 200)
        restored = self.client.state()
        self.assertEqual(restored["recent_rounds"], [first])
        self.assertEqual(len(restored["recent_rounds"][0]["round"]["free_spins"]), 12)

    def test_07_conflicting_retry_cannot_charge_another_bet(self):
        _, first = self.client.spin()
        status, conflict = self.client.spin(bet=200)
        self.assertEqual(status, 409)
        self.assertEqual(conflict["code"], "request_conflict")
        self.assertEqual(self.client.state()["balance_cents"], first["balance_cents"])
        self.assertEqual(self.client.state()["total_bet_cents"], 100)

    def test_08_global_cap_also_bounds_five_scatter_round_and_its_retry(self):
        capped_distribution, capped = fixture(wilds=None)
        self.assertEqual(capped.base.scatter_count, 5)
        self.assertEqual(capped.base.free_spins_awarded, 12)
        self.assertEqual(capped.payout_units, app.config.MAX_WIN_UNITS)
        self.assertGreater(capped.cap_reduction_units, 0)
        self.assertLess(len(capped.free_spins), 12, "The whole-round cap can end an awarded bonus early")
        with patch.object(app.selection, "load_distribution", return_value=capped_distribution):
            status, first = self.client.spin("bonus12-cap")
            retry_status, retry = self.client.spin("bonus12-cap")
        self.assertEqual((status, retry_status), (200, 200))
        self.assertEqual(first, retry)
        self.assertEqual(first["win_cents"], 5000 * first["bet_cents"])
        self.assert_settled_once(first)

    def test_09_old_session_cannot_replay_book_into_reset_wallet(self):
        _, first = self.client.spin()
        old_session = self.client.session_id
        status, reset = self.client.call("POST", "/api/reset", {})
        self.assertEqual(status, 200)
        self.assertNotEqual(reset["session_id"], old_session)
        self.client.session_id = old_session
        status, failure = self.client.spin()
        self.assertEqual(status, 409)
        self.assertEqual(failure["code"], "session_changed")
        self.assertEqual(self.client.state()["rounds"], 0)
        self.assertEqual(self.client.state()["balance_cents"], self.before["balance_cents"])


class PublishedDistributionTests(unittest.TestCase):
    def test_10_published_distribution_contains_positive_weight_twelve_spin_book(self):
        manifest, cumulative, payouts = REAL_LOAD()
        candidates = []
        previous = 0
        for index, (spec, upper, payout) in enumerate(zip(manifest["books"], cumulative, payouts)):
            weight = upper - previous
            previous = upper
            result = app.selection.replay_spec(spec)
            if result.base.scatter_count == 5 and result.base.free_spins_awarded == 12:
                candidates.append((index, weight, payout, len(result.free_spins)))
                if len(result.free_spins) == 12 and weight > 0:
                    break
        complete = [row for row in candidates if row[3] == 12 and row[1] > 0]
        if not complete and not REQUIRE_EXPORTED:
            self.skipTest("No 12-FS book in existing export; rerun with --require-exported after rebuilding")
        self.assertTrue(complete, "The final weighted export needs a positive-weight reachable complete 12-FS book")
        index, weight, payout, length = complete[0]
        start = 0 if index == 0 else cumulative[index - 1]
        class Ticket:
            def randrange(self, stop):
                assert stop == manifest["total_weight"]
                return start
        # Use unmodified selector against the actual current manifest, not the fixture.
        with patch.object(app.selection, "load_distribution", return_value=(manifest, cumulative, payouts)):
            selected_id, result = app.selection.select_round(Ticket())
        self.assertEqual(selected_id, index)
        self.assertEqual(len(result.free_spins), 12)
        self.assertEqual(result.payout_units, payout)
        # Exercise the real exported book through the HTTP boundary as well.
        # Inject a ticket only into this isolated server's session RNG, never an endpoint.
        server = app.InterfaceServer(("127.0.0.1", 0))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = Client(server.server_port)
            before = client.state()
            session = next(iter(server.sessions.values()))
            session.rng = Ticket()
            status, paid = client.spin("actual-export-12fs")
            retry_status, retry = client.spin("actual-export-12fs")
            self.assertEqual((status, retry_status), (200, 200))
            self.assertEqual(paid, retry)
            self.assertEqual(paid["book_id"], index)
            self.assertEqual(paid["round"]["base"]["scatter_count"], 5)
            self.assertEqual(len(paid["round"]["free_spins"]), 12)
            self.assertEqual(paid["stats"]["rounds"], 1)
            self.assertEqual(paid["stats"]["total_bet_cents"], 100)
            self.assertEqual(paid["balance_cents"], before["balance_cents"] - 100 + payout)
            self.assertEqual(client.state()["rounds"], 1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
        (OUT / "actual_export_12fs_fixture.json").write_text(json.dumps({
            "scope": "Actual positively weighted complete round, selected by fixed test ticket; not natural frequencies",
            "math_version": manifest["math_version"], "book_id": index,
            "weight": weight, "round": asdict(result),
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        CHECKS.append({"evidence": "actual_export_12fs_witness", "book_id": index,
                       "weight": weight, "math_version": manifest["math_version"],
                       "played_free_spins": length, "payout_units": payout})


class ReportingResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        CHECKS.append({"name": test.id(), "status": "pass"})
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        CHECKS.append({"name": test.id(), "status": "skip", "reason": reason})
    def addFailure(self, test, err):
        super().addFailure(test, err)
        CHECKS.append({"name": test.id(), "status": "fail", "error": self._exc_info_to_string(err, test)})
    def addError(self, test, err):
        super().addError(test, err)
        CHECKS.append({"name": test.id(), "status": "error", "error": self._exc_info_to_string(err, test)})


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    outcome = unittest.TextTestRunner(verbosity=2, resultclass=ReportingResult).run(suite)
    report = {"generated_at": datetime.now(timezone.utc).isoformat(),
              "status": "pass" if outcome.wasSuccessful() else "fail",
              "math_version": app.config.MATH_VERSION,
              "tests_run": outcome.testsRun, "passed": outcome.testsRun - len(outcome.failures) - len(outcome.errors) - len(outcome.skipped),
              "skipped": len(outcome.skipped), "require_exported": REQUIRE_EXPORTED,
              "scope": "Real HTTP against production handler and selector with isolated reachable one-book fixture; final test uses real export",
              "checks": CHECKS}
    (OUT / "api_12fs_results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(not outcome.wasSuccessful())
