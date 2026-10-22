"""Regression checks for real, selectable 8/10/12-spin complete bonus books.

This checks the exported events and published integer weights, rather than
assuming that a declared FREE_SPINS entry is reachable in the final game.
Historical audits are never rewritten by this script.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, replace
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import random
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT / "test-interface" / "engine"),
               str(ROOT / "test-interface" / "qa"),
               str(ROOT / "audit" / "stake_cascades_v04" / "dependencies")]
import zstandard
import check_cascade_math as independent_oracle
from polska_gurom import config, game, selection


class ExactTicket:
    """Select an actual published book through the public local selector."""
    def __init__(self, ticket):
        self.ticket = ticket
        self.calls = 0

    def randrange(self, stop):
        if not 0 <= self.ticket < stop:
            raise AssertionError("Ticket outside published distribution")
        self.calls += 1
        return self.ticket


class BonusCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        selection.load_distribution.cache_clear()
        cls.manifest, cls.cdf, cls.payouts = selection.load_distribution()
        cls.weights = [upper - lower for lower, upper in zip([0] + cls.cdf[:-1], cls.cdf)]
        cls.bonus_books = []
        cls.coverage = Counter()
        cls.counts = Counter()
        cls.total_books_read = 0
        path = ROOT / "test-interface" / "stake_math" / "books_base.jsonl.zst"
        with path.open("rb") as stream:
            with zstandard.ZstdDecompressor().stream_reader(stream) as reader:
                for line in io.TextIOWrapper(reader, encoding="utf-8"):
                    book = json.loads(line)
                    if book["id"] != cls.total_books_read:
                        raise AssertionError("Exported book IDs are not contiguous")
                    cls.total_books_read += 1
                    result = book["events"][0]["data"]
                    awarded = result["base"]["free_spins_awarded"]
                    if awarded:
                        cls.bonus_books.append(book)
                        cls.coverage[awarded] += cls.weights[book["id"]]
                        cls.counts[awarded] += 1

    def test_all_configured_bonus_lengths_have_positive_exported_weight(self):
        self.assertEqual(self.total_books_read, len(self.manifest["books"]))
        for scatter_count, awarded in config.FREE_SPINS.items():
            with self.subTest(scatter_count=scatter_count, awarded=awarded):
                self.assertGreater(self.counts[awarded], 0,
                                   f"{scatter_count} Scatter / {awarded} FS has no exported book")
                self.assertGreater(self.coverage[awarded], 0,
                                   f"{scatter_count} Scatter / {awarded} FS cannot be selected")
                declared = self.manifest["bonus_coverage"][str(awarded)]
                actual_ids = [book["id"] for book in self.bonus_books
                              if book["events"][0]["data"]["base"]["free_spins_awarded"] == awarded]
                self.assertEqual(declared["scatters"], scatter_count)
                self.assertEqual(sorted(declared["book_ids"]), actual_ids)
                self.assertEqual(declared["total_weight"], self.coverage[awarded])

    def test_natural_five_scatter_witness_is_a_real_complete_twelve_spin_round(self):
        seed = 650496
        expected_stops = [34, 27, 20, 16, 8]
        rng = random.Random(seed)
        self.assertEqual([rng.randrange(len(strip)) for strip in config.REEL_STRIPS],
                         expected_stops)
        windows = [game.window_for_stop(strip, stop)
                   for strip, stop in zip(config.REEL_STRIPS, expected_stops)]
        expected_grid = tuple(tuple(windows[reel][row] for reel in range(config.REELS))
                              for row in range(config.ROWS))
        result = game.play_round(random.Random(seed))
        self.assertEqual(result.base.grid, expected_grid)
        self.assertEqual(result.base.scatter_count, 5)
        self.assertEqual(result.base.free_spins_awarded, 12)
        self.assertEqual(len(result.free_spins), 12)
        self.assertEqual(len(result.free_spin_credits), 12)
        self.assertLess(result.payout_units, config.MAX_WIN_UNITS)
        independent_oracle.validate_round(result)

    def test_exported_bonus_trigger_matches_initial_reel_windows(self):
        for book in self.bonus_books:
            with self.subTest(book_id=book["id"]):
                base = book["events"][0]["data"]["base"]
                scatter_count = sum(symbol == config.SCATTER
                                    for row in base["grid"] for symbol in row)
                self.assertEqual(base["scatter_count"], scatter_count)
                self.assertEqual(base["free_spins_awarded"],
                                 config.FREE_SPINS[min(scatter_count, 5)])
                for reel, strip in enumerate(config.REEL_STRIPS):
                    actual = tuple(row[reel] for row in base["grid"])
                    legal = {game.window_for_stop(strip, stop) for stop in range(len(strip))}
                    self.assertIn(actual, legal)

    def test_all_exported_bonus_events_replay_and_pass_independent_mechanics(self):
        for book in self.bonus_books:
            with self.subTest(book_id=book["id"]):
                result = selection.replay_spec(self.manifest["books"][book["id"]])
                expected = [{"index": 0, "type": "roundResult", "data": asdict(result)}]
                self.assertEqual(json.loads(json.dumps(expected)), book["events"])
                self.assertEqual(result.payout_units, self.payouts[book["id"]])
                self.assertEqual(book["payoutMultiplier"], result.payout_units)
                self.assertEqual(result.payout_units,
                                 result.base.payout_units + sum(result.free_spin_credits))
                self.assertEqual(len(result.free_spins), len(result.free_spin_credits))
                if result.payout_units < config.MAX_WIN_UNITS:
                    self.assertEqual(len(result.free_spins), result.base.free_spins_awarded)
                self.assertFalse(any(spin.cascade_limit_reached
                                     for spin in (result.base, *result.free_spins)))
                independent_oracle.validate_round(result)

    def test_twelve_spins_can_be_selected_at_both_integer_ticket_boundaries(self):
        books = [book for book in self.bonus_books
                 if book["events"][0]["data"]["base"]["free_spins_awarded"] == 12]
        self.assertTrue(books, "No selectable 12 FS book")
        for book in books:
            index = book["id"]
            lower = self.cdf[index - 1] if index else 0
            upper = self.cdf[index]
            self.assertGreater(upper, lower)
            for ticket in (lower, upper - 1):
                with self.subTest(book_id=index, ticket=ticket):
                    rng = ExactTicket(ticket)
                    actual_id, result = selection.select_round(rng)
                    self.assertEqual(rng.calls, 1)
                    self.assertEqual(actual_id, index)
                    self.assertEqual(result.base.scatter_count, 5)
                    self.assertEqual(result.base.free_spins_awarded, 12)
                    self.assertEqual(result.payout_units, self.payouts[index])
                    if result.payout_units < config.MAX_WIN_UNITS:
                        self.assertEqual(len(result.free_spins), 12)

    def test_exact_published_rtp_and_maximum_win_contract_remain_valid(self):
        denominator = self.cdf[-1]
        weighted_payout = sum(weight * payout
                              for weight, payout in zip(self.weights, self.payouts))
        self.assertEqual(Fraction(weighted_payout, denominator * config.PAYOUT_SCALE),
                         Fraction(24, 25))
        self.assertEqual(max(self.payouts), config.MAX_WIN_UNITS)
        cap_weight = sum(weight for weight, payout in zip(self.weights, self.payouts)
                         if payout == config.MAX_WIN_UNITS)
        self.assertEqual(Fraction(cap_weight, denominator), Fraction(1, 8000000))
        self.assertTrue(all(weight > 0 for weight in self.weights))

    def test_adding_twelve_spin_variant_preserves_total_bonus_frequency(self):
        self.assertEqual(sum(self.coverage.values()), 4_969_935_540)
        self.assertEqual(self.coverage[12], 4_018_776)
        self.assertEqual(self.counts[12], 24)

    def test_falsified_eight_spin_award_on_five_scatters_is_rejected(self):
        real = game.play_round(random.Random(650496))
        falsified = replace(real, base=replace(real.base, free_spins_awarded=8))
        with self.assertRaisesRegex(AssertionError, "free spin trigger award"):
            independent_oracle.validate_round(falsified)

    def _load_isolated_distribution(self, manifest, weights, payouts):
        """Run the production loader against temporary files, never live data."""
        lut = "".join(f"{index},{weight},{payout}\n"
                      for index, (weight, payout) in enumerate(zip(weights, payouts)))
        manifest["lut_sha256"] = hashlib.sha256(lut.encode()).hexdigest()
        with tempfile.TemporaryDirectory(prefix="polska-gurom-bonus-coverage-") as folder:
            directory = Path(folder) / "stake_math"
            directory.mkdir()
            (directory / "selection.json").write_text(json.dumps(manifest), encoding="utf-8")
            (directory / "lookUpTable_base_0.csv").write_text(lut, encoding="utf-8", newline="")
            local_module_path = str(Path(folder) / "engine" / "polska_gurom" / "selection.py")
            selection.load_distribution.cache_clear()
            try:
                with patch.object(selection, "__file__", local_module_path), \
                        patch.object(selection, "source_fingerprint",
                                     return_value=self.manifest["source_fingerprint"]):
                    return selection.load_distribution()
            finally:
                selection.load_distribution.cache_clear()

    def test_removing_all_twelve_spin_books_is_rejected_even_with_valid_lut_hash(self):
        manifest = json.loads(json.dumps(self.manifest))
        removed = set(manifest["bonus_coverage"]["12"]["book_ids"])
        kept = [index for index in range(len(self.weights)) if index not in removed]
        new_ids = {old: new for new, old in enumerate(kept)}
        manifest["books"] = [manifest["books"][index] for index in kept]
        weights = [self.weights[index] for index in kept]
        payouts = [self.payouts[index] for index in kept]
        # Preserve total weight so the failure specifically concerns coverage.
        weights[next(i for i, payout in enumerate(payouts) if payout == 0)] += \
            sum(self.weights[index] for index in removed)
        for coverage in manifest["bonus_coverage"].values():
            coverage["book_ids"] = [new_ids[index] for index in coverage["book_ids"]
                                    if index in new_ids]
            coverage["total_weight"] = sum(weights[index] for index in coverage["book_ids"])
        with self.assertRaises((ValueError, RuntimeError)):
            self._load_isolated_distribution(manifest, weights, payouts)

    def test_zero_weight_twelve_spin_books_are_rejected_with_valid_lut_hash(self):
        manifest = json.loads(json.dumps(self.manifest))
        ids = manifest["bonus_coverage"]["12"]["book_ids"]
        weights = self.weights.copy()
        removed_mass = sum(weights[index] for index in ids)
        for index in ids:
            weights[index] = 0
        weights[next(i for i, payout in enumerate(self.payouts) if payout == 0)] += removed_mass
        manifest["bonus_coverage"]["12"]["total_weight"] = 0
        with self.assertRaises((ValueError, RuntimeError)):
            self._load_isolated_distribution(manifest, weights, self.payouts)

    def test_falsified_twelve_spin_coverage_claim_is_rejected(self):
        manifest = json.loads(json.dumps(self.manifest))
        # A genuine 8 FS round cannot be advertised as a 12 FS witness.
        claimed_id = manifest["bonus_coverage"]["8"]["book_ids"][0]
        manifest["bonus_coverage"]["12"]["book_ids"] = [claimed_id]
        manifest["bonus_coverage"]["12"]["total_weight"] = self.weights[claimed_id]
        with self.assertRaises((ValueError, RuntimeError)):
            self._load_isolated_distribution(manifest, self.weights, self.payouts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    start = time.perf_counter()
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(BonusCoverageTests))
    if args.report:
        report = {
            "status": "PASS" if result.wasSuccessful() else "FAIL",
            "tests_run": result.testsRun,
            "failures": [{"test": str(test), "details": details}
                         for test, details in result.failures],
            "errors": [{"test": str(test), "details": details}
                       for test, details in result.errors],
            "elapsed_seconds": time.perf_counter() - start,
            "math_version": config.MATH_VERSION,
            "source_fingerprint": selection.source_fingerprint(),
            "lut_sha256": getattr(BonusCoverageTests, "manifest", {}).get("lut_sha256"),
            "bonus_book_counts": dict(getattr(BonusCoverageTests, "counts", {})),
            "bonus_integer_weight": dict(getattr(BonusCoverageTests, "coverage", {})),
            "independent_oracle": dict(independent_oracle.COUNTS),
            "natural_witness_seed": 650496,
        }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
