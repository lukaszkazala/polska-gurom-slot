"""Deterministic requirements tests for the PROTOTYPE reconstruction.

Run: python -m unittest discover -s tests -v
The reference evaluator below enumerates literal Wild replacements rather
than reproducing the production evaluator's per-target prefix algorithm.
"""
from collections import Counter
from dataclasses import replace
from fractions import Fraction
from itertools import product
import random
import unittest
from unittest.mock import patch

from polska_gurom.bonus import draw_charge
from polska_gurom.cap import settle_cap
from polska_gurom.config import load_config, validate_config
from polska_gurom.engine import (
    assemble_round, evaluate_board, evaluate_line, evaluate_spin,
    play_round, play_spin, round_to_dict,
)
from polska_gurom.reels import board_from_stops
from polska_gurom.scatter import scatter_award
from polska_gurom.sdk_adapter import to_line_bet_paytable


def reference_line(symbols, cfg):
    """Exhaust all regular replacements of Wilds, then score literal runs."""
    regular = tuple(cfg.paytable)
    wild_positions = [i for i, symbol in enumerate(symbols) if symbol == "WILD"]
    best = None
    for replacement in product(regular, repeat=len(wild_positions)):
        literal = list(symbols)
        for index, symbol in zip(wild_positions, replacement):
            literal[index] = symbol
        if literal[0] not in cfg.paytable:
            continue
        count = 1
        while count < 5 and literal[count] == literal[0]:
            count += 1
        if count < 3:
            continue
        payout = cfg.paytable[literal[0]][count]
        candidate = (literal[0], count, payout)
        # Resolve equal payouts by the stable mathematical symbol order.
        if payout > 0 and (
            best is None or payout > best[2]
            or (payout == best[2] and regular.index(candidate[0]) < regular.index(best[0]))
        ):
            best = candidate
    return best


class QueueRng:
    """An explicit finite sequence of valid integer draws, with bound checks."""
    def __init__(self, values):
        self.values = iter(values)
        self.bounds = []

    def randrange(self, upper):
        self.bounds.append(upper)
        value = next(self.values)
        if not 0 <= value < upper:
            raise AssertionError(f"Scripted RNG value {value} outside [0, {upper})")
        return value


class MathTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_config()

    def assertLine(self, symbols, symbol, count, units):
        win = evaluate_line(tuple(symbols), self.cfg)
        self.assertIsNotNone(win)
        self.assertEqual((win.symbol, win.count, win.payout_units), (symbol, count, units))
        self.assertEqual(win.line_index, -1)

    def scatter_spin(self, count, is_free=False, charge_reel=None):
        # The versioned reconstruction groups symbols; index 35 is SCATTER.
        stops = tuple(35 if reel < count else 7 for reel in range(5))
        return evaluate_spin(self.cfg, stops, is_free, charge_reel)


class EvaluatorTests(MathTestCase):
    def test_losing_line(self):
        self.assertIsNone(evaluate_line(("L1", "L2", "L3", "L4", "P1"), self.cfg))

    def test_three_four_and_five_matching_symbols(self):
        for count in (3, 4, 5):
            with self.subTest(count=count):
                line = ["L1"] * count + ["L2"] * (5 - count)
                self.assertLine(line, "L1", count, {3: 20, 4: 80, 5: 250}[count])

    def test_match_must_start_on_first_reel(self):
        self.assertIsNone(evaluate_line(("L2", "P4", "P4", "P4", "P4"), self.cfg))

    def test_interruption_ends_run(self):
        self.assertLine(("P4", "P4", "P4", "L1", "P4"), "P4", 3, 200)
        self.assertIsNone(evaluate_line(("P4", "P4", "L1", "P4", "P4"), self.cfg))

    def test_wild_substitution_inside_run(self):
        self.assertLine(("P3", "WILD", "P3", "WILD", "L1"), "P3", 4, 550)

    def test_wild_does_not_substitute_scatter(self):
        self.assertIsNone(evaluate_line(("WILD", "WILD", "SCATTER", "P4", "P4"), self.cfg))
        self.assertIsNone(evaluate_line(("SCATTER", "WILD", "WILD", "WILD", "WILD"), self.cfg))

    def test_leading_wilds_and_all_wilds(self):
        self.assertLine(("WILD", "WILD", "P3", "P3", "L1"), "P3", 4, 550)
        self.assertLine(("WILD", "P2", "P2", "L1", "L1"), "P2", 3, 80)
        self.assertLine(("WILD",) * 5, "P4", 5, 5000)

    def test_one_highest_interpretation_per_line(self):
        # Three P4 pay 2x, but five L1 pay 2.5x TOTAL BET.
        self.assertLine(("WILD", "WILD", "WILD", "L1", "L1"), "L1", 5, 250)
        # Four P4 pay 10x, exceeding five L1 at 2.5x.
        self.assertLine(("WILD", "WILD", "WILD", "WILD", "L1"), "P4", 4, 1000)

    def test_equal_payout_interpretations_use_stable_symbol_order(self):
        paytable = {symbol: {3: 100, 4: 100, 5: 100} for symbol in self.cfg.paytable}
        win = evaluate_line(("WILD",) * 5, replace(self.cfg, paytable=paytable))
        self.assertEqual((win.symbol, win.count, win.payout_units), ("L1", 5, 100))

    def test_no_sum_of_three_four_five_on_same_line(self):
        self.assertLine(("P4",) * 5, "P4", 5, 5000)

    def test_multiple_winning_lines_and_line_indices(self):
        wins = evaluate_board(tuple(("P4",) * 3 for _ in range(5)), self.cfg)
        self.assertEqual(len(wins), 20)
        self.assertEqual({win.line_index for win in wins}, set(range(20)))
        self.assertEqual(sum(win.payout_units for win in wins), 100000)

    def test_total_bet_units_and_sdk_line_bet_equivalence(self):
        # 0.40x means 40 units directly, with no second division by 20.
        self.assertLine(("L4", "L4", "L4", "L1", "L1"), "L4", 3, 40)
        converted = to_line_bet_paytable(self.cfg)
        for symbol, payouts in self.cfg.paytable.items():
            for count, units in payouts.items():
                with self.subTest(symbol=symbol, count=count):
                    self.assertEqual(converted[symbol][count] * Fraction(1, 20), Fraction(units, self.cfg.scale))
        self.assertEqual(converted["L4"][3], Fraction(8))

    def test_reference_evaluator_exhaustive_small_alphabet(self):
        # 4^5 = 1024 lines; exhaustive assignments include 8^5 all-Wild cases.
        for line in product(("L1", "P3", "SCATTER", "WILD"), repeat=5):
            result = evaluate_line(line, self.cfg)
            actual = None if result is None else (result.symbol, result.count, result.payout_units)
            self.assertEqual(actual, reference_line(line, self.cfg), line)

    def test_reference_evaluator_seeded_all_symbols(self):
        rng = random.Random(20261017)
        symbols = tuple(self.cfg.paytable) + ("WILD", "SCATTER")
        for _ in range(1000):
            line = tuple(rng.choice(symbols) for _ in range(5))
            result = evaluate_line(line, self.cfg)
            actual = None if result is None else (result.symbol, result.count, result.payout_units)
            self.assertEqual(actual, reference_line(line, self.cfg), line)

    def test_invalid_lines_and_boards_are_rejected(self):
        for line in (("L1",) * 4, ("UNKNOWN",) * 5):
            with self.subTest(line=line), self.assertRaises(ValueError):
                evaluate_line(line, self.cfg)
        with self.assertRaises(ValueError):
            evaluate_board((("L1",) * 3,) * 4, self.cfg)


class ReelAndScatterTests(MathTestCase):
    def test_cyclic_window_wraps_at_strip_end(self):
        board = board_from_stops(self.cfg, (35, 34, 0, 1, 2))
        self.assertEqual(board[0], ("SCATTER", "L1", "L1"))
        self.assertEqual(board[1], ("WILD", "SCATTER", "L1"))
        for reel, stop in enumerate((35, 34, 0, 1, 2)):
            self.assertEqual(board[reel], tuple(self.cfg.reels[reel][(stop + row) % 36] for row in range(3)))

    def test_historical_counts_are_preserved_but_order_is_explicit(self):
        expected = Counter({"L1": 7, "L2": 5, "L3": 5, "L4": 4, "P1": 4,
                            "P2": 3, "P3": 3, "P4": 2, "WILD": 2, "SCATTER": 1})
        for reel in self.cfg.reels:
            self.assertEqual(len(reel), 36)
            self.assertEqual(Counter(reel), expected)
            self.assertEqual(reel[-3:], ("WILD", "WILD", "SCATTER"))

    def test_at_most_one_visible_scatter_per_reel(self):
        for reel in self.cfg.reels:
            counts = [sum(reel[(stop + row) % len(reel)] == "SCATTER" for row in range(3)) for stop in range(len(reel))]
            self.assertEqual(Counter(counts), Counter({0: 33, 1: 3}))

    def test_exactly_three_four_five_scatters_and_free_spin_awards(self):
        for count, award, units in ((3, 8, 100), (4, 10, 500), (5, 12, 2000)):
            with self.subTest(count=count):
                spin = self.scatter_spin(count)
                self.assertEqual(spin.scatter_count, count)
                self.assertEqual(spin.scatter_units, units)
                self.assertEqual(spin.awarded_free_spins, award)
                self.assertEqual(spin.total_units, spin.line_units + units)

    def test_fewer_than_three_scatters_do_not_trigger(self):
        for count in (0, 1, 2):
            spin = self.scatter_spin(count)
            self.assertEqual((spin.scatter_units, spin.awarded_free_spins), (0, 0))

    def test_invalid_stop_positions_and_unsupported_scatter_count(self):
        for stops in ((0,) * 4, (-1,) + (0,) * 4, (36,) + (0,) * 4, (True,) + (0,) * 4):
            with self.subTest(stops=stops), self.assertRaises(ValueError):
                board_from_stops(self.cfg, stops)
        for count in (-1, 6):
            with self.subTest(count=count), self.assertRaises(ValueError):
                scatter_award(count, self.cfg)


class BonusTests(MathTestCase):
    def test_free_spin_scatter_pays_without_retrigger(self):
        for count, units in ((3, 100), (4, 500), (5, 2000)):
            spin = self.scatter_spin(count, is_free=True)
            self.assertEqual(spin.scatter_units, units)
            self.assertEqual(spin.awarded_free_spins, 0)

    def test_play_round_has_no_retriggers(self):
        base = self.scatter_spin(3)
        free = self.scatter_spin(5, is_free=True)
        with patch("polska_gurom.engine.play_spin", side_effect=[base] + [free] * 8) as played:
            result = play_round(self.cfg, random.Random(1))
        self.assertEqual(played.call_count, 9)
        self.assertEqual(len(result.free_spins), 8)
        self.assertEqual(result.raw_bonus_units, 8 * free.total_units)

    def test_free_spin_without_charge_preserves_natural_board(self):
        spin = evaluate_spin(self.cfg, (7,) * 5, is_free=True)
        self.assertIsNone(spin.charge_reel)
        self.assertEqual(spin.board, spin.natural_board)

    def test_charge_expands_each_allowed_reel_and_only_one(self):
        for reel in (1, 2, 3):
            with self.subTest(human_reel=reel + 1):
                spin = evaluate_spin(self.cfg, (7,) * 5, is_free=True, charge_reel=reel)
                self.assertEqual(spin.charge_reel, reel)
                self.assertEqual(spin.board[reel], ("WILD",) * 3)
                self.assertEqual([index for index in range(5) if spin.board[index] != spin.natural_board[index]], [reel])
                self.assertEqual(spin.line_units, sum(win.payout_units for win in spin.line_wins))

    def test_charge_rejects_reels_one_five_and_base_game(self):
        for reel in (-1, 0, 4, 5):
            with self.subTest(reel=reel), self.assertRaises(ValueError):
                evaluate_spin(self.cfg, (7,) * 5, is_free=True, charge_reel=reel)
        with self.assertRaises(ValueError):
            evaluate_spin(self.cfg, (7,) * 5, charge_reel=2)

    def test_charge_resets_before_next_free_spin(self):
        # Two sequential real play_spin calls: first forced Charge, then no Charge.
        charged = play_spin(self.cfg, QueueRng([7] * 5 + [0, 1]), is_free=True)
        following = play_spin(self.cfg, QueueRng([7] * 5 + [1]), is_free=True)
        self.assertEqual(charged.charge_reel, 2)
        self.assertEqual(following.board, charged.natural_board)
        self.assertIsNone(following.charge_reel)
        self.assertNotEqual(charged.board, following.board)

    def test_scatter_hidden_by_charge_still_pays_from_natural_board(self):
        spin = self.scatter_spin(3, is_free=True, charge_reel=1)
        self.assertEqual(spin.natural_board[1][0], "SCATTER")
        self.assertEqual(spin.board[1], ("WILD",) * 3)
        self.assertEqual(sum(symbol == "SCATTER" for reel in spin.board for symbol in reel), 2)
        self.assertEqual((spin.scatter_count, spin.scatter_units), (3, 100))

    def test_charge_probability_and_reel_weights_have_exact_integer_draws(self):
        self.assertEqual(self.cfg.charge_probability, Fraction(1, 4))
        for trial in (1, 2, 3):
            rng = QueueRng([trial])
            self.assertIsNone(draw_charge(self.cfg, rng))
            self.assertEqual(rng.bounds, [4])
        cfg = replace(self.cfg, charge_weights=(1, 2, 3))
        for draw, expected in enumerate((1, 2, 2, 3, 3, 3)):
            rng = QueueRng([0, draw])
            self.assertEqual(draw_charge(cfg, rng), expected)
            self.assertEqual(rng.bounds, [4, 6])


class RoundAndCapTests(MathTestCase):
    def witness(self):
        base = evaluate_spin(self.cfg, (33,) * 5)
        free = evaluate_spin(self.cfg, (31,) * 5, is_free=True)
        return base, free

    def test_full_round_aggregation(self):
        base = self.scatter_spin(3)
        free = evaluate_spin(self.cfg, (7,) * 5, is_free=True)
        result = assemble_round(self.cfg, base, [free] * 8)
        self.assertEqual(result.raw_base_units, base.total_units)
        self.assertEqual(result.raw_bonus_units, sum(spin.total_units for spin in result.free_spins))
        self.assertEqual(result.raw_total_units, result.raw_base_units + result.raw_bonus_units)
        self.assertEqual(result.paid_total_units, min(result.raw_total_units, self.cfg.cap_units))

    def test_round_without_bonus_has_no_free_spins(self):
        base = evaluate_spin(self.cfg, (7,) * 5)
        result = assemble_round(self.cfg, base, ())
        self.assertEqual(result.raw_bonus_units, 0)
        self.assertEqual(result.paid_total_units, base.total_units)

    def test_cap_below_equal_and_above_five_thousand_total_bet(self):
        cap = self.cfg.cap_units
        for raw, expected_cap in ((cap - 1, False), (cap, True), (cap + 1, True)):
            with self.subTest(raw_units=raw):
                settlement = settle_cap(100, raw - 100, cap)
                self.assertEqual(settlement["paid_total_units"], min(raw, cap))
                self.assertEqual(settlement["cap_reduction_units"], max(raw - cap, 0))
                self.assertEqual(settlement["cap_reached"], expected_cap)

    def test_paid_components_sum_after_cap(self):
        cap = self.cfg.cap_units
        for base, bonus in ((0, 0), (100, 200), (100, cap), (cap + 1, 300), (cap, cap)):
            with self.subTest(base=base, bonus=bonus):
                settlement = settle_cap(base, bonus, cap)
                self.assertEqual(settlement["paid_base_units"] + settlement["paid_bonus_units"], settlement["paid_total_units"])
                self.assertEqual(settlement["paid_total_units"] + settlement["cap_reduction_units"], base + bonus)
                self.assertEqual(settlement["paid_base_units"], min(base, cap))

    def test_reachable_positive_probability_cap_witness(self):
        base, free = self.witness()
        self.assertEqual(base.awarded_free_spins, 12)
        result = assemble_round(self.cfg, base, [free] * 12)
        self.assertEqual(result.raw_total_units, 1232400)
        self.assertEqual(result.paid_total_units, 500000)
        self.assertTrue(result.cap_reached)
        # Specific valid stops in 13 independent spins and no Charge in 12 FS.
        probability = Fraction(1, 36) ** (5 * 13) * (1 - self.cfg.charge_probability) ** 12
        self.assertGreater(probability, 0)
        self.assertEqual(result.cap_reduction_units, 732400)

    def test_all_awarded_spins_are_simulated_after_cap(self):
        base, free = self.witness()
        with patch("polska_gurom.engine.play_spin", side_effect=[base] + [free] * 12) as played:
            result = play_round(self.cfg, random.Random(1))
        self.assertEqual(played.call_count, 13)
        self.assertEqual(len(result.free_spins), 12)
        self.assertEqual(result.raw_bonus_units, 12 * free.total_units)
        self.assertEqual(result.paid_total_units, self.cfg.cap_units)

    def test_serialized_per_spin_settlement_preserves_raw_and_paid_totals(self):
        base, free = self.witness()
        result = assemble_round(self.cfg, base, [free] * 12)
        trace = round_to_dict(result)["settlement_trace"]
        self.assertEqual(len(trace), 13)
        self.assertEqual(sum(spin["raw_total_units"] for spin in trace), result.raw_total_units)
        self.assertEqual(sum(spin["paid_total_units"] for spin in trace), result.paid_total_units)
        self.assertEqual(trace[-1]["cumulative_raw_units"], result.raw_total_units)
        self.assertEqual(trace[-1]["cumulative_paid_units"], self.cfg.cap_units)
        self.assertEqual(trace[-1]["paid_total_units"], 0)
        self.assertGreater(trace[-1]["raw_total_units"], 0)
        for spin in trace:
            self.assertEqual(spin["paid_line_units"] + spin["paid_scatter_units"], spin["paid_total_units"])

    def test_incomplete_or_retriggered_trace_is_rejected(self):
        base = self.scatter_spin(3)
        free = self.scatter_spin(5, is_free=True)
        for spins in ([free] * 7, [free] * 9, [replace(free, awarded_free_spins=8)] * 8):
            with self.subTest(length=len(spins)), self.assertRaises(ValueError):
                assemble_round(self.cfg, base, spins)
        with self.assertRaises(ValueError):
            assemble_round(self.cfg, free, ())

    def test_negative_cap_inputs_are_rejected(self):
        for args in ((-1, 0, 500000), (0, -1, 500000), (0, 0, -1)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                settle_cap(*args)

    def test_same_seed_config_and_engine_reproduce_complete_rounds(self):
        left, right = random.Random(123456789), random.Random(123456789)
        for _ in range(300):
            self.assertEqual(round_to_dict(play_round(self.cfg, left)), round_to_dict(play_round(self.cfg, right)))

    def test_round_result_does_not_depend_on_preceding_paid_round(self):
        # A fresh injected RNG defines the next complete round independently.
        expected = play_round(self.cfg, random.Random(4242))
        for _ in range(20):
            play_round(self.cfg, random.Random(7))
        self.assertEqual(play_round(self.cfg, random.Random(4242)), expected)


class ConfigTests(MathTestCase):
    def test_paylines_are_twenty_unique_complete_coordinates(self):
        self.assertEqual(len(set(self.cfg.paylines)), 20)
        self.assertTrue(all(len(line) == 5 and set(line) <= {0, 1, 2} for line in self.cfg.paylines))

    def test_config_hash_is_stable_and_covers_math_changes(self):
        self.assertEqual(load_config().config_hash, self.cfg.config_hash)
        self.assertEqual(len(self.cfg.config_hash), 64)
        self.assertNotEqual(replace(self.cfg, charge_probability=Fraction(1, 2)).config_hash, self.cfg.config_hash)
        altered = {symbol: dict(payouts) for symbol, payouts in self.cfg.paytable.items()}
        altered["L1"][3] += 1
        self.assertNotEqual(replace(self.cfg, paytable=altered).config_hash, self.cfg.config_hash)

    def test_invalid_configuration_is_rejected(self):
        bad_reel = ("SCATTER", "SCATTER", "L1")
        invalid = [
            replace(self.cfg, reels=self.cfg.reels[:4]),
            replace(self.cfg, reels=(("UNKNOWN",) * 3,) + self.cfg.reels[1:]),
            replace(self.cfg, reels=(bad_reel,) + self.cfg.reels[1:]),
            replace(self.cfg, paylines=(self.cfg.paylines[0],) * 20),
            replace(self.cfg, paylines=((3,) * 5,) + self.cfg.paylines[1:]),
            replace(self.cfg, paytable={"L1": {3: 20, 4: 80, 5: 250}}),
            replace(self.cfg, fs_awards={3: 9, 4: 10, 5: 12}),
            replace(self.cfg, scatter_pays={3: -1, 4: 500, 5: 2000}),
            replace(self.cfg, charge_probability=Fraction(5, 4)),
            replace(self.cfg, charge_weights=(0, 0, 0)),
            replace(self.cfg, charge_weights=(1, -1, 1)),
            replace(self.cfg, cap_units=499999),
            replace(self.cfg, scale=0),
        ]
        for index, cfg in enumerate(invalid):
            with self.subTest(case=index), self.assertRaises(ValueError):
                validate_config(cfg)


if __name__ == "__main__":
    unittest.main()
