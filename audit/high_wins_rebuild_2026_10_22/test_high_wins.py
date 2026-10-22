"""Selectors and wallet settlement against the current exported high-win bank.

This is local integration QA. It does not claim live-platform approval.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument("--interface", type=Path, default=ROOT / "test-interface-any-start")
parser.add_argument("--output", type=Path, default=Path(__file__).with_name("high_win_regressions.json"))
args = parser.parse_args()
sys.dont_write_bytecode = True
sys.path.insert(0, str(args.interface.resolve()))
import server
from test_server import Client

selection, config = server.selection, server.config
DETAILS = {}


class Ticket:
    def __init__(self, value, total):
        self.value, self.total, self.calls = value, total, 0

    def randrange(self, total):
        assert total == self.total
        self.calls += 1
        return self.value


class HighWinRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.cumulative, cls.payouts = selection.load_distribution()
        cls.weights = [b - a for a, b in zip([0] + cls.cumulative[:-1], cls.cumulative)]
        cls.bonus_ids = {int(fs): group["book_ids"]
                         for fs, group in cls.manifest["bonus_coverage"].items()}
        cls.caps = {i: selection.replay_spec(cls.manifest["books"][i])
                    for i, payout in enumerate(cls.payouts) if payout == config.MAX_WIN_UNITS}

    def test_every_integer_ticket_boundary_selects_correct_book(self):
        # Replay is stubbed only here to isolate interval selection from game
        # evaluation. The high-win tests below replay the actual chosen books.
        identities = {id(spec): i for i, spec in enumerate(self.manifest["books"])}
        observed = []

        def record(spec):
            index = identities[id(spec)]
            observed.append(index)
            return SimpleNamespace(payout_units=self.payouts[index])

        checks = 0
        with patch.object(selection, "replay_spec", new=record):
            for index, upper in enumerate(self.cumulative):
                lower = self.cumulative[index - 1] if index else 0
                for value in {lower, upper - 1}:
                    ticket = Ticket(value, self.manifest["total_weight"])
                    selected, result = selection.select_round(ticket)
                    self.assertEqual(selected, index)
                    self.assertEqual(observed[-1], index)
                    self.assertEqual(result.payout_units, self.payouts[index])
                    self.assertEqual(ticket.calls, 1)
                    checks += 1
        DETAILS["ticket_boundary_checks"] = checks

    def test_actual_high_wins_replay_at_both_ticket_edges(self):
        count = 0
        for index, payout in enumerate(self.payouts):
            if payout < 500 * config.PAYOUT_SCALE:
                continue
            expected = selection.replay_spec(self.manifest["books"][index])
            for value in {self.cumulative[index - 1] if index else 0, self.cumulative[index] - 1}:
                selected, result = selection.select_round(Ticket(value, self.manifest["total_weight"]))
                self.assertEqual(selected, index)
                self.assertEqual(result, expected)
                self.assertEqual(result.payout_units, payout)
                count += 1
        self.assertGreater(count, 0)
        DETAILS["actual_high_win_edge_replays"] = count

    def test_cap_mass_and_actual_free_spin_termination(self):
        self.assertEqual(sum(self.weights[i] for i in self.caps), 125_000)
        self.assertTrue(any(not result.base.bonus_triggered for result in self.caps.values()))
        bonus_caps = {i: result for i, result in self.caps.items() if result.base.bonus_triggered}
        self.assertTrue(bonus_caps)
        partial, early = [], []
        variants = {}
        for fs in (8, 10, 12):
            ids = self.bonus_ids[fs]
            self.assertTrue(ids)
            self.assertTrue(all(self.weights[i] > 0 for i in ids))
            variants[str(fs)] = [i for i in ids if i in bonus_caps]
        for index, result in bonus_caps.items():
            self.assertLess(result.base.payout_units, config.MAX_WIN_UNITS)
            self.assertGreater(len(result.free_spins), 0)
            self.assertLessEqual(len(result.free_spins), result.base.free_spins_awarded)
            self.assertEqual(len(result.free_spins), len(result.free_spin_credits))
            remaining = config.MAX_WIN_UNITS - result.base.payout_units
            for spin, credit in zip(result.free_spins, result.free_spin_credits):
                self.assertGreater(remaining, 0, "no FS executes after round cap")
                self.assertEqual(credit, spin.payout_units)
                self.assertEqual(credit, min(spin.raw_payout_units, remaining))
                self.assertEqual(spin.line_multiplier, config.FS_LINE_MULTIPLIER)
                if spin.raw_payout_units > credit:
                    partial.append(index)
                remaining -= credit
            self.assertEqual(remaining, 0)
            self.assertEqual(result.bonus_payout_units, sum(result.free_spin_credits))
            self.assertEqual(result.raw_payout_units - result.payout_units, result.cap_reduction_units)
            if len(result.free_spins) < result.base.free_spins_awarded:
                early.append(index)
        self.assertTrue(partial, "weighted bank exercises partial final FS credit")
        self.assertTrue(early, "weighted bank exercises termination of unplayed awarded FS")
        DETAILS["bonus_cap_ids_by_variant"] = variants
        DETAILS["partial_final_fs_book_ids"] = sorted(set(partial))
        DETAILS["early_fs_termination_book_ids"] = sorted(set(early))

    def test_http_cap_settles_once_for_paid_round_and_retries(self):
        httpd = server.InterfaceServer(("127.0.0.1", 0))
        thread = threading.Thread(target=lambda: httpd.serve_forever(poll_interval=.02), daemon=True)
        thread.start()
        cases = []
        bonus_caps = {}
        for index, result in self.caps.items():
            if result.base.bonus_triggered:
                bonus_caps.setdefault(result.base.free_spins_awarded, (index, result))
        base_cap = next((i, result) for i, result in self.caps.items() if not result.base.bonus_triggered)
        try:
            for index, result in [base_cap, *bonus_caps.values()]:
                for bet in (min(server.BET_OPTIONS_CENTS), max(server.BET_OPTIONS_CENTS)):
                    client = Client(httpd.server_port)
                    before = client.state()
                    request_id = f"high-win-{index}-{bet}"
                    with patch.object(selection, "select_round", return_value=(index, result)) as selected:
                        status, response, _ = client.spin(bet=bet, request_id=request_id)
                        self.assertEqual(status, 200)
                        self.assertFalse(response["is_scenario"])
                        self.assertEqual(response["book_id"], index)
                        self.assertEqual(response["round"], json.loads(json.dumps(asdict(result))))
                        self.assertEqual(response["win_cents"], bet * 5000)
                        self.assertEqual(response["balance_cents"], before["balance_cents"] - bet + bet * 5000)
                        self.assertEqual(response["stats"], {
                            "rounds": 1, "total_bet_cents": bet, "total_win_cents": bet * 5000})
                        self.assertEqual(client.spin(bet=bet, request_id=request_id)[1], response)
                        self.assertEqual(selected.call_count, 1)
                        after = client.state()
                        self.assertEqual(after["rounds"], 1)
                        self.assertEqual(after["balance_cents"], response["balance_cents"])
                        self.assertEqual(client.spin(bet=bet * 2, request_id=request_id)[0], 400
                                         if bet * 2 not in server.BET_OPTIONS_CENTS else 409)
                    cases.append({"book_id": index, "bet_cents": bet,
                                  "awarded": result.base.free_spins_awarded,
                                  "played": len(result.free_spins)})
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=3)
        DETAILS["http_settlement_cases"] = cases


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(HighWinRegressions)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "math_version": config.MATH_VERSION,
        "method": "All selector ticket boundaries, actual exported high-win replays and local HTTP wallet cap settlement; no live-platform claim.",
        "tests_run": result.testsRun,
        "passed": result.wasSuccessful(),
        "failures": [{"test": str(test), "traceback": trace}
                     for test, trace in [*result.failures, *result.errors]],
        "details": DETAILS,
        "source_sha256": {name: hashlib.sha256((args.interface / name).read_bytes()).hexdigest()
                          for name in ("engine/polska_gurom/selection.py", "server.py", "stake_math/lookUpTable_base_0.csv")},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(not result.wasSuccessful())
