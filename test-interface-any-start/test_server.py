"""HTTP integration checks: run ``python -m unittest -v test_server.py``."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime
import http.client
import json
import random
import tempfile
import threading
from pathlib import Path
import unittest
from unittest.mock import patch
import uuid

import server


class Client:
    def __init__(self, port, cookie=None):
        self.port, self.cookie = port, cookie
        self.session_id = None

    def request(self, method, path, body=None, *, raw=None, headers=None):
        extra = dict(headers or {})
        if self.cookie:
            extra.setdefault("Cookie", self.cookie)
        if raw is None and body is not None:
            raw = json.dumps(body).encode("utf-8")
        if raw is not None:
            extra.setdefault("Content-Type", "application/json")
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        connection.request(method, path, body=raw, headers=extra)
        response = connection.getresponse()
        response_headers = dict(response.getheaders())
        if response_headers.get("Set-Cookie"):
            self.cookie = response_headers["Set-Cookie"].split(";", 1)[0]
        data = response.read()
        status = response.status
        connection.close()
        if response_headers.get("Content-Type", "").startswith("application/json") and data:
            data = json.loads(data)
            if data.get("session_id"):
                self.session_id = data["session_id"]
        return status, data, response_headers

    def spin(self, mode="random", bet=500, request_id=None):
        if not self.session_id:
            self.state()
        return self.request("POST", "/api/spin", {
            "mode": mode, "bet_cents": bet, "request_id": request_id or str(uuid.uuid4())},
            headers={"X-Game-Session": self.session_id})

    def state(self):
        status, body, _ = self.request("GET", "/api/state")
        assert status == 200
        return body


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.web = Path(cls.temp.name)
        (cls.web / "index.html").write_text("<h1>Local test UI</h1>", encoding="utf-8")
        cls.server = server.InterfaceServer(("127.0.0.1", 0), web_root=cls.web)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.temp.cleanup()

    def setUp(self):
        self.client = Client(self.server.server_port)

    def assert_round_integrity(self, result):
        self.assertEqual(result["payout_units"], result["base"]["payout_units"] + sum(result["free_spin_credits"]))
        self.assertEqual(result["bonus_payout_units"], sum(result["free_spin_credits"]))
        self.assertEqual(result["raw_payout_units"], result["base"]["raw_payout_units"] + sum(spin["raw_payout_units"] for spin in result["free_spins"]))
        self.assertLessEqual(result["payout_units"], server.config.MAX_WIN_UNITS)
        self.assertEqual(result["cap_reduction_units"], result["raw_payout_units"] - result["payout_units"])
        available = server.config.MAX_WIN_UNITS
        for spin in [result["base"], *result["free_spins"]]:
            steps = spin["cascades"]
            self.assertTrue(steps)
            self.assertEqual(spin["evaluation_grid"], steps[0]["evaluation_grid"])
            self.assertEqual(spin["line_wins"], steps[0]["line_wins"])
            self.assertFalse(spin["cascade_limit_reached"])
            self.assertEqual(spin["line_payout_units"], sum(step["line_payout_units"] for step in steps))
            self.assertEqual(spin["raw_payout_units"], spin["scatter_payout_units"] + spin["line_payout_units"])
            self.assertEqual(spin["payout_units"], min(spin["raw_payout_units"], available))
            stage_remaining = available - min(spin["scatter_payout_units"], available)
            for index, step in enumerate(steps):
                self.assertEqual(step["line_payout_units"], sum(win["payout_units"] for win in step["line_wins"]))
                self.assertEqual(step["payout_units"], min(step["line_payout_units"], stage_remaining))
                stage_remaining -= step["payout_units"]
                if index + 1 == len(steps):
                    self.assertEqual(step["removed_positions"], [])
                    self.assertEqual(step["movements"], [])
                    if step["line_wins"]:
                        self.assertEqual(stage_remaining, 0)
                    continue
                removed = {(win["rows"][reel], reel) for win in step["line_wins"]
                           for reel in range(win.get("start_reel", 0), win.get("start_reel", 0) + win["count"])}
                self.assertEqual({tuple(position) for position in step["removed_positions"]}, removed)
                next_grid = steps[index + 1]["evaluation_grid"]
                spawned = [move for move in step["movements"] if move["from_row"] < 0]
                self.assertEqual(len(spawned), len(removed))
                self.assertTrue(all(move["symbol"] != "SCATTER" for move in spawned))
                for reel in range(5):
                    survivors = [step["evaluation_grid"][row][reel] for row in range(3)
                                 if (row, reel) not in removed]
                    if survivors:
                        self.assertEqual([row[reel] for row in next_grid][-len(survivors):], survivors)
                for move in step["movements"]:
                    self.assertEqual(next_grid[move["to_row"]][move["reel"]], move["symbol"])
                    if move["from_row"] >= 0:
                        self.assertGreater(move["to_row"], move["from_row"])
                        self.assertEqual(step["evaluation_grid"][move["from_row"]][move["reel"]], move["symbol"])
            self.assertEqual(spin["payout_units"], min(spin["scatter_payout_units"], available)
                             + sum(step["payout_units"] for step in steps))
            available -= spin["payout_units"]
        remaining = server.config.MAX_WIN_UNITS - result["base"]["payout_units"]
        for spin, credit in zip(result["free_spins"], result["free_spin_credits"]):
            self.assertEqual(credit, min(spin["payout_units"], remaining))
            self.assertGreaterEqual(credit, 0)
            remaining -= credit
            self.assertEqual(spin["line_multiplier"], 4)
            self.assertFalse(spin["bonus_triggered"])
            if spin["expanding_reel"] is not None:
                self.assertIn(spin["expanding_reel"], (1, 2, 3))
                reel = spin["expanding_reel"]
                self.assertTrue(all(row[reel] == "WILD" for row in spin["evaluation_grid"]))
            self.assertEqual(spin["scatter_count"], sum(cell == "SCATTER" for row in spin["grid"] for cell in row))

    def test_config_static_files_and_cookie(self):
        status, config, headers = self.client.request("GET", "/api/config")
        self.assertEqual(status, 200)
        self.assertEqual(config["payout_scale"], 100)
        self.assertEqual(len(config["paylines"]), 20)
        self.assertEqual(config["bet_options_cents"], list(server.BET_OPTIONS_CENTS))
        self.assertEqual(config["math_version"], server.config.MATH_VERSION)
        self.assertTrue(config["cascades_enabled"])
        self.assertEqual(config["max_cascades"], 1000)
        self.assertEqual(config["theoretical_rtp"], 0.96)
        self.assertEqual(config["selection_model"], "weighted_complete_round_books")
        self.assertEqual(self.client.request("GET", "/api/health")[1],
                         {"ok": True, "engine": "polska_gurom", "math_version": server.config.MATH_VERSION})
        self.assertEqual(headers["Cache-Control"], "no-store")
        status, state, headers = self.client.request("GET", "/api/state")
        self.assertEqual(state["balance_cents"], 1_000_000)
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        self.assertIn("SameSite=Strict", headers["Set-Cookie"])
        self.assertEqual(self.client.state(), state)
        self.assertEqual(self.client.request("GET", "/")[0], 200)
        self.assertEqual(self.client.request("HEAD", "/")[1], b"")
        self.assertEqual(self.client.request("GET", "/../server.py")[0], 404)
        self.assertEqual(self.client.request("GET", "/%2e%2e/server.py")[0], 404)

    def test_random_wallet_exact_settlement_and_session_isolation(self):
        before = self.client.state()
        status, result, _ = self.client.spin(bet=200)
        self.assertEqual(status, 200)
        self.assertFalse(result["is_scenario"])
        self.assertIsInstance(result["book_id"], int)
        manifest, _, _ = server.selection.load_distribution()
        expected = asdict(server.selection.replay_spec(manifest["books"][result["book_id"]]))
        self.assertEqual(result["round"], json.loads(json.dumps(expected)))
        self.assertEqual(result["win_cents"], 200 * result["round"]["payout_units"] // 100)
        self.assertEqual(result["balance_cents"], before["balance_cents"] - 200 + result["win_cents"])
        self.assertEqual(result["stats"], {"rounds": 1, "total_bet_cents": 200, "total_win_cents": result["win_cents"]})
        self.assertEqual(self.client.state()["balance_cents"], result["balance_cents"])
        self.assert_round_integrity(result["round"])
        other = Client(self.server.server_port).state()
        self.assertNotEqual(other["session_id"], before["session_id"])
        self.assertEqual(other["balance_cents"], 1_000_000)

    def test_scenarios_replay_real_engine_without_wallet_changes(self):
        before = self.client.state()
        for mode in ("win", "bonus", "expansion"):
            with self.subTest(mode=mode):
                status, result, _ = self.client.spin(mode, bet=10000)
                self.assertEqual(status, 200)
                self.assertTrue(result["is_scenario"])
                self.assertEqual(result["balance_cents"], before["balance_cents"])
                self.assertEqual(result["stats"]["rounds"], 0)
                expected = asdict(server.game.play_round(random.Random(server.SCENARIO_SEEDS[mode])))
                self.assertEqual(result["round"], json.loads(json.dumps(expected)))
                self.assert_round_integrity(result["round"])
                if mode == "win":
                    self.assertTrue(result["round"]["base"]["line_wins"])
                else:
                    self.assertTrue(result["round"]["base"]["bonus_triggered"])
                    self.assertLessEqual(len(result["round"]["free_spins"]), result["round"]["base"]["free_spins_awarded"])
                    if result["round"]["payout_units"] < server.config.MAX_WIN_UNITS:
                        self.assertEqual(len(result["round"]["free_spins"]), result["round"]["base"]["free_spins_awarded"])
                if mode == "expansion":
                    self.assertTrue(any(spin["expanding_reel"] is not None for spin in result["round"]["free_spins"]))
        after = self.client.state()
        self.assertEqual({key: value for key, value in after.items() if key != "recent_rounds"},
                         {key: value for key, value in before.items() if key != "recent_rounds"})
        self.assertEqual([record["mode"] for record in after["recent_rounds"]],
                         ["expansion", "bonus", "win"])

    def test_history_survives_page_reload_is_bounded_and_newest_first(self):
        self.client.state()
        _, paid, _ = self.client.spin()
        _, scenario, _ = self.client.spin("win")
        # A fresh HTTP client with the same browser cookie represents a page reload.
        reloaded = Client(self.server.server_port, self.client.cookie).state()
        self.assertEqual(reloaded["recent_rounds"], [scenario, paid])
        self.assertEqual(reloaded["rounds"], 1)
        for record in reloaded["recent_rounds"]:
            self.assertTrue(record["created_at"].endswith("Z"))
            self.assertEqual(datetime.fromisoformat(record["created_at"]).utcoffset().total_seconds(), 0)
        latest = scenario
        for index in range(100):
            status, latest, _ = self.client.spin("win", request_id=f"history-{index}")
            self.assertEqual(status, 200)
        history = self.client.state()["recent_rounds"]
        self.assertEqual(len(history), 100)
        self.assertEqual(history[0]["round_id"], latest["round_id"])
        self.assertNotIn(paid["round_id"], [record["round_id"] for record in history])
        self.assertNotIn(scenario["round_id"], [record["round_id"] for record in history])
        self.assertTrue(all(record["mode"] == "win" for record in history))
        self.assertEqual(self.client.state()["rounds"], 1)
        status, reset, _ = self.client.request("POST", "/api/reset", {})
        self.assertEqual(status, 200)
        self.assertEqual(reset["recent_rounds"], [])
        self.assertEqual(self.client.state()["recent_rounds"], [])

    def test_cascade_endpoint_preserves_falls_and_charges_one_paid_round(self):
        before = self.client.state()
        token = self.client.cookie.split("=", 1)[1]
        session = self.server.sessions[token]
        with session.lock:
            manifest, cdf, _ = server.selection.load_distribution()
            book = next(i for i,spec in enumerate(manifest["books"]) if spec == {"seed": 2})
            class FixedTicket:
                def randrange(self, stop): return cdf[book-1] if book else 0
            session.rng = FixedTicket()
        request_id = "paid-cascade"
        status, paid, _ = self.client.spin(bet=200, request_id=request_id)
        self.assertEqual(status, 200)
        self.assertFalse(paid["is_scenario"])
        self.assert_round_integrity(paid["round"])
        steps = paid["round"]["base"]["cascades"]
        self.assertGreaterEqual(len(steps), 3)
        self.assertGreater(sum(bool(step["line_wins"]) for step in steps), 1)
        self.assertTrue(any(move["from_row"] >= 0 and move["to_row"] > move["from_row"]
                            for step in steps for move in step["movements"]))
        self.assertEqual(paid["win_cents"], 200 * paid["round"]["payout_units"] // 100)
        self.assertEqual(paid["balance_cents"], before["balance_cents"] - 200 + paid["win_cents"])
        self.assertEqual(paid["stats"], {"rounds": 1, "total_bet_cents": 200,
                                        "total_win_cents": paid["win_cents"]})
        self.assertEqual(self.client.spin(bet=200, request_id=request_id)[1], paid)
        status, scenario, _ = self.client.spin("cascade", bet=200, request_id="show-cascade")
        self.assertEqual(status, 200)
        self.assertTrue(scenario["is_scenario"])
        self.assertEqual(scenario["scenario_seed"], 2)
        self.assertEqual(scenario["round"], paid["round"])
        self.assertEqual(scenario["balance_cents"], paid["balance_cents"])
        self.assertEqual(scenario["stats"], paid["stats"])
        self.assertEqual(self.client.spin("cascade", bet=200, request_id="show-cascade")[1], scenario)
        after = self.client.state()
        self.assertEqual(after["rounds"], 1)
        self.assertEqual(after["recent_rounds"], [scenario, paid])

    def test_idempotence_and_conflicting_reuse(self):
        self.client.state()
        request_id = str(uuid.uuid4())
        first = self.client.spin(request_id=request_id)
        repeated = self.client.spin(request_id=request_id)
        self.assertEqual(first[:2], repeated[:2])
        self.assertEqual(self.client.state()["rounds"], 1)
        conflict = self.client.spin(bet=1000, request_id=request_id)
        self.assertEqual(conflict[0], 409)
        self.assertEqual(conflict[1]["code"], "request_conflict")
        self.assertEqual(self.client.state()["rounds"], 1)

    def test_simultaneous_retries_charge_once(self):
        self.client.state()
        cookie = self.client.cookie
        request_id = str(uuid.uuid4())
        def retry(_):
            return Client(self.server.server_port, cookie).spin(request_id=request_id)
        with ThreadPoolExecutor(max_workers=8) as executor:
            responses = list(executor.map(retry, range(8)))
        self.assertTrue(all(response[0] == 200 for response in responses))
        self.assertTrue(all(response[1] == responses[0][1] for response in responses))
        self.assertEqual(self.client.state()["rounds"], 1)

    def test_validation_and_cross_origin_requests_do_not_change_wallet(self):
        before = self.client.state()
        valid = {"bet_cents": 100, "mode": "random", "request_id": "valid"}
        for bad in (True, 100.0, "100", -100, 1, 101, None):
            with self.subTest(bet=bad):
                status, body, _ = self.client.request("POST", "/api/spin", {**valid, "bet_cents": bad})
                self.assertEqual(status, 400)
                self.assertEqual(body["code"], "invalid_bet")
        for body in ([], {}, {**valid, "mode": "forced"}, {**valid, "mode": []},
                     {**valid, "request_id": ""}, {**valid, "request_id": "x" * 129}):
            self.assertEqual(self.client.request("POST", "/api/spin", body)[0], 400)
        for raw in (b"{broken", b"null", b'{"a":NaN}', b"\xff"):
            self.assertEqual(self.client.request("POST", "/api/spin", raw=raw)[0], 400)
        self.assertEqual(self.client.request("POST", "/api/spin", raw=b"x" * 4097)[0], 413)
        self.assertEqual(self.client.request("POST", "/api/spin", valid, headers={"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.client.request("POST", "/api/spin", valid, headers={"Origin": "https://example.com"})[0], 403)
        self.assertEqual(self.client.request("GET", "/api/state", headers={"Host": "example.com"})[0], 403)
        self.assertEqual(self.client.request("POST", "/api/spin", valid, headers={"Sec-Fetch-Site": "cross-site"})[0], 403)
        self.assertEqual(self.client.request("OPTIONS", "/api/spin")[0], 405)
        self.assertEqual(self.client.state(), before)

    def test_reset_and_insufficient_funds(self):
        self.client.state()
        self.client.spin()
        status, reset, _ = self.client.request("POST", "/api/reset", {})
        self.assertEqual(status, 200)
        self.assertEqual(reset["balance_cents"], 1_000_000)
        self.assertEqual(reset["rounds"], 0)
        token = self.client.cookie.split("=", 1)[1]
        session = self.server.sessions[token]
        with session.lock:
            session.balance_cents = 99
        status, body, _ = self.client.spin(bet=100)
        self.assertEqual(status, 409)
        self.assertEqual(body["code"], "insufficient_funds")
        self.assertEqual(self.client.state()["balance_cents"], 99)
        # Showcase scenarios remain available even when the virtual wallet is empty.
        self.assertEqual(self.client.spin("expansion")[0], 200)
        self.assertEqual(self.client.state()["balance_cents"], 99)

    def test_cap_credits_are_settled_once_at_total_bet(self):
        base = (("SCATTER", "SCATTER", "SCATTER", "L1", "L2"),
                ("P1", "P2", "P3", "P4", "L4"),
                ("L2", "L3", "L4", "P1", "P2"))
        free = (("WILD",) * 5,) * 3
        class ExpansionRng:
            def random(self): return 0.0
            def choice(self, eligible): return 2 if isinstance(eligible[0], int) else "WILD"
        with patch.object(server.game, "generate_grid", side_effect=[base, free]):
            capped = server.game.play_round(ExpansionRng(), expansion_probability=1)
        self.assertEqual(capped.payout_units, 500000)
        self.assertGreater(capped.cap_reduction_units, 0)
        self.client.state()
        with patch.object(server.selection, "select_round", return_value=(100020, capped)):
            status, result, _ = self.client.spin(bet=200, request_id="cap-round")
        self.assertEqual(status, 200)
        self.assert_round_integrity(result["round"])
        self.assertEqual(result["win_cents"], 1_000_000)
        self.assertEqual(result["balance_cents"], 1_999_800)
        self.assertEqual(result["round"]["free_spin_credits"], [499900])
        self.assertEqual(len(result["round"]["free_spins"]), 1)
        self.assertEqual(result["round"]["free_spins"][-1]["cascades"][-1]["movements"], [])
        self.assertEqual(self.client.spin(bet=200, request_id="cap-round")[1], result)
        self.assertEqual(self.client.state()["rounds"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
