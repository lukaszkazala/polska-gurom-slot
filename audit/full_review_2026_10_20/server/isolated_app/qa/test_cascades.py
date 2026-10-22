"""Deterministic cascade mechanics and settlement regression checks."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import random
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from polska_gurom import config, game


INITIAL = (
    ("L1", "L1", "L1", "L2", "L3"),
    ("P1", "P2", "P3", "P4", "L4"),
    ("L2", "L3", "L4", "P1", "P2"),
)


class RefillRandom(random.Random):
    """Controlled symbols without bypassing the actual removal/refill engine."""
    def __init__(self, symbols=(), default="P4"):
        super().__init__(1)
        self.symbols = iter(symbols)
        self.default = default
        self.draws = []

    def choice(self, population):
        # An expansion chooses a reel, whereas refills choose a strip symbol.
        if population and isinstance(population[0], int):
            return population[0]
        value = next(self.symbols, self.default)
        if value not in population:
            raise AssertionError("Refill must be possible on its original strip")
        self.draws.append(value)
        return value


class CascadeTests(unittest.TestCase):
    def test_actual_fall_with_holes_above_and_below_survivors(self):
        grid = (
            ("L1", "P1", "P2", "P3", "P4"),
            ("L2", "SCATTER", "L3", "L4", "P1"),
            ("L3", "L4", "P1", "P2", "P3"),
        )
        rng = RefillRandom(("WILD", "P4", "P2"))
        after, moves = game.tumble_grid(grid, ((1, 0), (2, 0), (2, 1)), rng)
        self.assertEqual(tuple(row[0] for row in after), ("WILD", "P4", "L1"))
        self.assertEqual(tuple(row[1] for row in after), ("P2", "P1", "SCATTER"))
        self.assertEqual(tuple(row[2:] for row in after), tuple(row[2:] for row in grid))
        self.assertIn(game.SymbolMove("L1", 0, 2, 0), moves)
        self.assertIn(game.SymbolMove("SCATTER", 1, 2, 1), moves)
        self.assertEqual([(m.from_row, m.to_row) for m in moves if m.from_row < 0],
                         [(-2, 0), (-1, 1), (-1, 0)])
        self.assertEqual(grid[0][0], "L1")
        self.assertIsInstance(after, tuple)
        self.assertTrue(all(isinstance(row, tuple) for row in after))

    def test_duplicates_remove_one_cell_and_survivor_order_is_stable(self):
        rng = RefillRandom(("WILD",))
        after, moves = game.tumble_grid(INITIAL, ((2, 0), (2, 0)), rng)
        self.assertEqual(tuple(row[0] for row in after), ("WILD", "L1", "P1"))
        self.assertEqual(len(rng.draws), 1)
        self.assertEqual([(m.from_row, m.to_row) for m in moves], [(-1, 0), (0, 1), (1, 2)])
        same, moves = game.tumble_grid(INITIAL, (), rng)
        self.assertEqual(same, INITIAL)
        self.assertEqual(moves, ())

    def test_overlapping_lines_remove_union_once_and_award_new_wins(self):
        rng = RefillRandom(("L2", "L2", "L2", "P1", "P2", "P3"))
        spin = game.evaluate_paid_spin(INITIAL, rng)
        self.assertEqual(len(spin.cascades), 3)
        first, second, terminal = spin.cascades
        self.assertGreater(len(first.line_wins), 1)
        self.assertEqual(first.removed_positions, ((0, 0), (0, 1), (0, 2)))
        self.assertEqual(second.evaluation_grid[0][:3], ("L2", "L2", "L2"))
        self.assertTrue(second.line_wins)
        self.assertEqual(terminal.line_wins, ())
        self.assertEqual(terminal.removed_positions, ())
        self.assertEqual(terminal.movements, ())
        self.assertEqual(spin.line_wins, first.line_wins)
        self.assertEqual(spin.payout_units, sum(s.payout_units for s in spin.cascades))
        self.assertEqual(spin.line_payout_units, sum(s.line_payout_units for s in spin.cascades))
        # The second L2 win extends to reel four, so that stage refills four cells.
        self.assertEqual(len(rng.draws), 7)

    def test_scatter_is_initial_only_and_never_spawned(self):
        grid = [list(row) for row in INITIAL]
        grid[2][2:] = ["SCATTER"] * 3
        spin = game.evaluate_paid_spin(grid, RefillRandom(("L2", "L2", "L2", "P1", "P2", "P3")))
        self.assertEqual(spin.scatter_count, 3)
        self.assertEqual(spin.scatter_payout_units, 100)
        self.assertEqual(spin.free_spins_awarded, 8)
        self.assertTrue(all(game.count_scatter(s.evaluation_grid) == 3 for s in spin.cascades))
        self.assertEqual(spin.payout_units, 100 + sum(s.payout_units for s in spin.cascades))
        self.assertTrue(all("SCATTER" not in strip for strip in config.REFILL_STRIPS))
        self.assertEqual([game.free_spins_for_scatter(n) for n in (3, 4, 5)], [8, 10, 12])

    def test_free_spin_multiplier_cascades_and_expansion_only_once(self):
        rng = RefillRandom(("L2", "L2", "L2", "P1", "P2", "P3"))
        paid = game.evaluate_paid_spin(INITIAL, RefillRandom(("L2", "L2", "L2", "P1", "P2", "P3")))
        free = game.evaluate_free_spin(INITIAL, rng, 0)
        self.assertEqual(free.line_payout_units, 4 * paid.line_payout_units)
        self.assertTrue(all(w.line_multiplier == 4 for s in free.cascades for w in s.line_wins))
        self.assertFalse(free.bonus_triggered)
        self.assertEqual(free.free_spins_awarded, 0)
        with patch.object(game, "apply_expanding_wild", wraps=game.apply_expanding_wild) as expand:
            expanded = game.evaluate_free_spin(INITIAL, RefillRandom(default="L3"), 1)
        self.assertEqual(expand.call_count, 1)
        self.assertTrue(all(row[1] == "WILD" for row in expanded.evaluation_grid))
        self.assertGreater(len(expanded.cascades), 1)
        self.assertTrue(any(row[1] != "WILD" for row in expanded.cascades[1].evaluation_grid))

    def test_scatter_count_before_free_spin_expansion(self):
        grid = [list(row) for row in INITIAL]
        grid[0][1] = grid[1][1] = grid[2][1] = "SCATTER"
        spin = game.evaluate_free_spin(grid, RefillRandom(default="L3"), 1)
        self.assertEqual(spin.scatter_count, 3)
        self.assertEqual(game.count_scatter(spin.evaluation_grid), 0)
        self.assertEqual(spin.scatter_payout_units, 100)
        self.assertFalse(spin.bonus_triggered)

    def test_round_cap_applies_across_base_and_free_spins(self):
        trigger = (
            ("SCATTER", "SCATTER", "SCATTER", "L1", "L2"),
            ("P1", "P2", "P3", "P4", "L4"),
            ("L2", "L3", "L4", "P1", "P2"),
        )
        wilds = (("WILD",) * 5,) * 3
        with patch.object(game, "generate_grid", side_effect=(trigger, wilds)):
            result = game.play_round(RefillRandom(default="WILD"), 0)
        self.assertEqual(result.payout_units, config.MAX_WIN_UNITS)
        self.assertEqual(len(result.free_spins), 1)
        self.assertEqual(result.free_spin_credits, (config.MAX_WIN_UNITS - 100,))
        self.assertGreater(result.cap_reduction_units, 0)
        last = result.free_spins[-1].cascades[-1]
        self.assertTrue(last.line_wins)
        self.assertEqual(last.movements, ())
        self.assertEqual(last.removed_positions, ())

    def test_limit_caps_stage_after_scatter_before_any_removal(self):
        grid = [list(row) for row in INITIAL]
        grid[2][2:] = ["SCATTER"] * 3
        rng = RefillRandom()
        result = game.evaluate_paid_spin(grid, rng, payout_limit_units=110)
        self.assertEqual(result.payout_units, 110)
        self.assertEqual(result.cascades[0].payout_units, 10)
        self.assertEqual(result.cascades[0].removed_positions, ())
        self.assertEqual(rng.draws, [])
        self.assertGreater(result.cap_reduction_units, 0)

    def test_emergency_limit_is_explicit_and_stops_before_removal(self):
        with patch.object(game, "MAX_CASCADES", 2):
            result = game.evaluate_paid_spin(INITIAL, RefillRandom(default="L1"))
        self.assertTrue(result.cascade_limit_reached)
        self.assertEqual(len(result.cascades), 2)
        self.assertEqual(result.cascades[-1].removed_positions, ())
        self.assertEqual(result.cascades[-1].movements, ())

    def test_seeded_rounds_are_repeatable_and_settlement_matches_animation(self):
        for seed in range(250):
            with self.subTest(seed=seed):
                result = game.play_round(random.Random(seed))
                self.assertEqual(asdict(result), asdict(game.play_round(random.Random(seed))))
                self.assertEqual(result.payout_units, result.base.payout_units + sum(result.free_spin_credits))
                self.assertLessEqual(result.payout_units, config.MAX_WIN_UNITS)
                for spin in (result.base, *result.free_spins):
                    self.assertFalse(spin.cascade_limit_reached)
                    self.assertEqual(spin.line_payout_units, sum(s.line_payout_units for s in spin.cascades))
                    self.assertEqual(spin.payout_units,
                                     min(spin.scatter_payout_units, spin.payout_units) +
                                     sum(s.payout_units for s in spin.cascades))
                    for current, following in zip(spin.cascades, spin.cascades[1:]):
                        self.assertEqual(set(current.removed_positions),
                                         {p for w in current.line_wins for p in w.positions})
                        spawned = [m for m in current.movements if m.from_row < 0]
                        self.assertEqual(len(spawned), len(current.removed_positions))
                        self.assertTrue(all(m.symbol != "SCATTER" for m in spawned))
                        for move in current.movements:
                            self.assertEqual(following.evaluation_grid[move.to_row][move.reel], move.symbol)
                            if move.from_row >= 0:
                                self.assertEqual(current.evaluation_grid[move.from_row][move.reel], move.symbol)
                                self.assertGreater(move.to_row, move.from_row)
                    if spin.cascades[-1].line_wins:
                        self.assertEqual(result.payout_units, config.MAX_WIN_UNITS)


if __name__ == "__main__":
    unittest.main()
