"""Independent acceptance tests for v0.2 scoring and auditable round events.

These functions use only the standard library, so the small built-in runner or
pytest can execute them. Expected scoring does not call the production scorer.
"""
from __future__ import annotations

import itertools
import random
from collections import Counter
from unittest.mock import patch

from polska_gurom import config, game


EXPECTED_PAYTABLE = {
    "L1": {3: 16, 4: 80, 5: 250},
    "L2": {3: 25, 4: 100, 5: 350},
    "L3": {3: 30, 4: 120, 5: 450},
    "L4": {3: 40, 4: 160, 5: 600},
    "P1": {3: 60, 4: 250, 5: 1000},
    "P2": {3: 80, 4: 350, 5: 1500},
    "P3": {3: 120, 4: 550, 5: 2500},
    "P4": {3: 200, 4: 1000, 5: 5000},
}
EXPECTED_LINES = (
    (1, 1, 1, 1, 1), (1, 1, 1, 0, 0), (1, 1, 1, 2, 2),
    (0, 0, 0, 0, 0), (2, 2, 2, 2, 2),
    (0, 0, 0, 1, 1), (2, 2, 2, 1, 1),
    (0, 1, 1, 1, 0), (2, 1, 1, 1, 2),
    (0, 1, 1, 2, 2), (2, 1, 1, 0, 0),
    (1, 1, 0, 0, 1), (1, 1, 2, 2, 1),
    (1, 1, 0, 1, 2), (1, 1, 2, 1, 0), (0, 0, 0, 1, 2),
    (0, 1, 2, 1, 0), (2, 1, 0, 1, 2),
    (0, 1, 2, 2, 1), (2, 1, 0, 0, 1),
)
ALL_SYMBOLS = (*EXPECTED_PAYTABLE, "WILD", "SCATTER")


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _oracle_options(symbols):
    """Keep the possible targets of each prefix, then choose one best payment."""
    possible = set(EXPECTED_PAYTABLE)
    options = []
    for count, symbol in enumerate(symbols, start=1):
        if symbol != "WILD":
            possible.intersection_update((symbol,))
        if not possible:
            break
        if count >= 3:
            for target in sorted(possible):
                options.append((EXPECTED_PAYTABLE[target][count], target, count))
    return options


def _oracle_amount(symbols):
    return max((item[0] for item in _oracle_options(symbols)), default=0)


def _oracle_grid(grid, multiplier=1):
    expected = {}
    for line_id, rows in enumerate(EXPECTED_LINES, start=1):
        sequence = [grid[row][reel] for reel, row in enumerate(rows)]
        options = _oracle_options(sequence)
        if options:
            amount = max(item[0] for item in options)
            expected[line_id] = (amount * multiplier, options)
    return expected


def _assert_line_events(grid, actual, multiplier=1):
    expected = _oracle_grid(grid, multiplier)
    assert len({event.line_id for event in actual}) == len(actual)
    assert {event.line_id for event in actual} == set(expected)
    for event in actual:
        assert 1 <= event.line_id <= 20
        rows = EXPECTED_LINES[event.line_id - 1]
        amount, options = expected[event.line_id]
        assert tuple(event.rows) == rows
        assert event.line_multiplier == multiplier
        assert event.payout_units == amount
        assert type(event.payout_units) is int
        assert (amount // multiplier, event.symbol, event.count) in options
        assert event.count in (3, 4, 5)
        assert event.positions == tuple((rows[c], c) for c in range(event.count))
    assert sum(event.payout_units for event in actual) == sum(item[0] for item in expected.values())


def _assert_spin(result):
    assert isinstance(result.grid, tuple)
    assert isinstance(result.evaluation_grid, tuple)
    assert all(isinstance(row, tuple) for row in result.grid)
    assert all(isinstance(row, tuple) for row in result.evaluation_grid)
    _assert_line_events(result.evaluation_grid, result.line_wins, result.line_multiplier)
    assert result.line_payout_units == sum(event.payout_units for event in result.line_wins)
    assert result.raw_payout_units == result.line_payout_units + result.scatter_payout_units
    assert result.payout_units == min(result.raw_payout_units, 500_000)
    assert result.payout == result.payout_units / 100
    assert result.line_payout == result.line_payout_units / 100
    assert result.scatter_payout == result.scatter_payout_units / 100
    for name in ("payout_units", "line_payout_units", "scatter_payout_units", "raw_payout_units"):
        assert type(getattr(result, name)) is int


def _scatter_grid(count):
    grid = [["L1", "L2", "L3", "L4", "P1"] for _ in range(3)]
    first = [(0, 0), (2, 4), (1, 2), (0, 3), (2, 1)]
    cells = first + [(r, c) for r in range(3) for c in range(5) if (r, c) not in first]
    for row, reel in cells[:count]:
        grid[row][reel] = "SCATTER"
    return grid


def _grid_from_stops(stops):
    return [[config.REEL_STRIPS[c][(stops[c] + r) % 36] for c in range(5)] for r in range(3)]


class _ExpansionRng:
    def __init__(self, reel):
        self.reel = reel
        self.choices = 0

    def random(self):
        return 0.0

    def randrange(self, limit):
        assert limit > 0
        return 0

    def choice(self, values):
        assert tuple(values) == (1, 2, 3)
        self.choices += 1
        return self.reel


def test_frozen_config_and_payline_geometry():
    assert config.PAYOUT_SCALE == 100
    assert config.PAYTABLE_UNITS == EXPECTED_PAYTABLE
    assert config.PAYLINES == EXPECTED_LINES
    assert len(set(config.PAYLINES)) == 20
    assert len({line[:3] for line in config.PAYLINES}) == 9
    assert config.FREE_SPINS == {3: 8, 4: 10, 5: 12}
    assert config.FS_LINE_MULTIPLIER == 4
    assert config.MAX_WIN == 5000
    assert 0 <= config.EXPANDING_WILD_PROBABILITY <= 1
    for symbol, values in EXPECTED_PAYTABLE.items():
        assert config.PAYTABLE[symbol] == {count: amount / 100 for count, amount in values.items()}
    for rows in config.PAYLINES:
        assert len(rows) == 5
        assert all(row in (0, 1, 2) for row in rows)
        assert all(abs(left - right) <= 1 for left, right in zip(rows, rows[1:]))


def test_strips_and_cyclic_window_generation():
    composition = {"L1": 7, "L2": 5, "L3": 5, "L4": 4, "P1": 4, "P2": 3,
                   "P3": 3, "P4": 2, "WILD": 2, "SCATTER": 1}
    assert len(config.REEL_STRIPS) == 5
    for strip in config.REEL_STRIPS:
        assert len(strip) == 36
        assert Counter(strip) == composition
        for stop in range(36):
            expected = tuple(strip[(stop + row) % 36] for row in range(3))
            assert game.window_for_stop(strip, stop) == expected
    class Stops:
        values = iter((35, 34, 0, 7, 19))
        calls = 0
        def randrange(self, length):
            assert length == 36
            self.calls += 1
            return next(self.values)
    rng = Stops()
    grid = game.generate_grid(rng)
    assert rng.calls == 5
    for reel, stop in enumerate((35, 34, 0, 7, 19)):
        assert [grid[row][reel] for row in range(3)] == [config.REEL_STRIPS[reel][(stop + row) % 36] for row in range(3)]


def test_exhaustive_100000_line_sequences_against_independent_oracle():
    count = 0
    for symbols in itertools.product(ALL_SYMBOLS, repeat=5):
        assert game._line_best_win(list(symbols)) == _oracle_amount(symbols) / 100, symbols
        count += 1
    assert count == 100_000


def test_explicit_left_anchor_interruption_and_best_wild_once():
    cases = [
        (["L1", "P4", "P4", "P4", "P4"], 0),
        (["P4", "P4", "L1", "P4", "P4"], 0),
        (["SCATTER", "WILD", "WILD", "WILD", "WILD"], 0),
        (["P4", "P4", "P4", "SCATTER", "P4"], 200),
        (["WILD", "WILD", "WILD", "L1", "L2"], 200),
        (["WILD", "WILD", "WILD", "L1", "L1"], 250),
        (["WILD"] * 5, 5000),
        (["L1", "L1", "WILD", "L2", "L1"], 16),
    ]
    for symbols, units in cases:
        assert game._line_best_win(symbols) == units / 100


def test_every_payline_event_matches_oracle_with_overlapping_prefixes():
    for rows in EXPECTED_LINES:
        grid = [["SCATTER"] * 5 for _ in range(3)]
        for reel, row in enumerate(rows):
            grid[row][reel] = "P4"
        for multiplier in (1, 4):
            actual = game.evaluate_line_wins(grid, multiplier=multiplier)
            _assert_line_events(grid, actual, multiplier)
        assert game.evaluate_lines(grid) == sum(item[0] for item in _oracle_grid(grid).values()) / 100


def test_total_bet_units_are_not_divided_by_twenty():
    grid = [["L1"] * 5 for _ in range(3)]
    base = game.evaluate_paid_spin(grid)
    _assert_spin(base)
    assert len(base.line_wins) == 20
    assert base.line_payout_units == 5000
    assert base.payout == 50
    assert base.line_multiplier == 1
    fs = game.evaluate_free_spin(grid, _ExpansionRng(1), expansion_probability=0)
    _assert_spin(fs)
    assert fs.line_payout_units == 20000
    assert fs.payout == 200


def test_scatter_anywhere_pays_and_awards_only_in_paid_game():
    for count in range(16):
        grid = _scatter_grid(count)
        expected_pay = 0 if count < 3 else {3: 100, 4: 500, 5: 2000}[min(count, 5)]
        expected_fs = 0 if count < 3 else {3: 8, 4: 10, 5: 12}[min(count, 5)]
        assert game.count_scatter(grid) == count
        base = game.evaluate_paid_spin(grid)
        _assert_spin(base)
        assert base.scatter_count == count
        assert base.scatter_payout_units == expected_pay
        assert base.free_spins_awarded == expected_fs
        assert base.bonus_triggered == (count >= 3)
        fs = game.evaluate_free_spin(grid, _ExpansionRng(1), expansion_probability=0)
        _assert_spin(fs)
        assert fs.scatter_count == count
        assert fs.scatter_payout_units == expected_pay
        assert fs.free_spins_awarded == 0
        assert fs.bonus_triggered is False
    assert game.count_scatter([["WILD"] * 5 for _ in range(3)]) == 0


def test_expansion_uses_exactly_one_inner_reel_and_preserves_input():
    grid = _scatter_grid(3)
    snapshot = _frozen(grid)
    for reel in (1, 2, 3):
        rng = _ExpansionRng(reel)
        fs = game.evaluate_free_spin(grid, rng, expansion_probability=1)
        expected = tuple(tuple("WILD" if c == reel else grid[r][c] for c in range(5)) for r in range(3))
        assert rng.choices == 1
        assert fs.expanding_reel == reel
        assert fs.grid == snapshot
        assert fs.evaluation_grid == expected
        assert fs.scatter_count == 3
        assert fs.scatter_payout_units == 100
        assert fs.bonus_triggered is False
        assert fs.free_spins_awarded == 0
        assert _frozen(grid) == snapshot
        _assert_spin(fs)
    rng = _ExpansionRng(1)
    fs = game.evaluate_free_spin(grid, rng, expansion_probability=0)
    assert rng.choices == 0
    assert fs.expanding_reel is None
    assert fs.grid == fs.evaluation_grid == snapshot


def test_result_snapshot_does_not_change_if_callers_grid_changes():
    grid = _scatter_grid(3)
    snapshot = _frozen(grid)
    result = game.evaluate_paid_spin(grid)
    grid[0][0] = "WILD"
    assert result.grid == result.evaluation_grid == snapshot


def test_default_expansion_uses_exact_integer_threshold():
    assert type(config.EXPANDING_WILD_NUMERATOR) is int
    assert type(config.EXPANDING_WILD_DENOMINATOR) is int
    assert 0 < config.EXPANDING_WILD_NUMERATOR < config.EXPANDING_WILD_DENOMINATOR
    class ExactChance:
        def __init__(self, value):
            self.value = value
            self.calls = []
        def randrange(self, limit):
            self.calls.append(limit)
            return self.value
        def choice(self, eligible):
            assert eligible == (1, 2, 3)
            return 2
        def random(self):
            raise AssertionError("Production default must use its exact integer probability")
    grid = _scatter_grid(0)
    below = ExactChance(config.EXPANDING_WILD_NUMERATOR - 1)
    boundary = ExactChance(config.EXPANDING_WILD_NUMERATOR)
    assert game.evaluate_free_spin(grid, below).expanding_reel == 2
    assert game.evaluate_free_spin(grid, boundary).expanding_reel is None
    assert below.calls == boundary.calls == [config.EXPANDING_WILD_DENOMINATOR]


def test_round_history_awards_8_10_12_without_retriggers():
    for scatter_count, awarded in ((3, 8), (4, 10), (5, 12)):
        base_grid = _scatter_grid(scatter_count)
        free_grid = _scatter_grid(5)
        with patch.object(game, "generate_grid", side_effect=[base_grid] + [free_grid] * awarded) as generate:
            result = game.play_round(_ExpansionRng(1), expansion_probability=0)
        assert generate.call_count == awarded + 1
        assert len(result.free_spins) == awarded
        assert len(result.free_spin_credits) == awarded
        assert result.base.free_spins_awarded == awarded
        for fs in result.free_spins:
            _assert_spin(fs)
            assert not fs.bonus_triggered
            assert fs.free_spins_awarded == 0
            assert fs.scatter_payout_units == 2000
        assert result.raw_payout_units == result.base.raw_payout_units + sum(fs.raw_payout_units for fs in result.free_spins)
        assert result.bonus_payout_units == sum(result.free_spin_credits)
        assert result.payout_units == result.base.payout_units + result.bonus_payout_units
        assert result.cap_reduction_units == result.raw_payout_units - result.payout_units
        assert result.expansions == 0


def test_history_distinguishes_equal_payment_different_expansion():
    base_grid = _scatter_grid(3)
    free_grid = [["L1"] * 5 for _ in range(3)]
    def forced(reel):
        with patch.object(game, "generate_grid", side_effect=[base_grid] + [free_grid] * 8):
            return game.play_round(_ExpansionRng(reel), expansion_probability=1)
    a, b = forced(1), forced(2)
    assert a.payout_units == b.payout_units
    assert a != b
    assert a.expansions == b.expansions == 8
    assert all(fs.expanding_reel == 1 for fs in a.free_spins)
    assert all(fs.expanding_reel == 2 for fs in b.free_spins)


def test_round_cap_reconciles_base_bonus_and_every_credit():
    # These are reachable windows, not arbitrary all-Wild artificial boards.
    # The FS witness is independently obtained from the exhaustive joint counts.
    base_grid = _grid_from_stops((35, 28, 22, 7, 19))
    assert game.count_scatter(base_grid) == 3
    free_grid = _grid_from_stops((21, 15, 0, 3, 30))
    fs_witness = game.evaluate_free_spin(free_grid, _ExpansionRng(2), expansion_probability=1)
    assert fs_witness.scatter_count == 0
    assert fs_witness.line_payout_units == 71400
    with patch.object(game, "generate_grid", side_effect=[base_grid] + [free_grid] * 8):
        result = game.play_round(_ExpansionRng(2), expansion_probability=1)
    _assert_spin(result.base)
    assert len(result.free_spins) == 8
    assert result.raw_payout_units > 500_000
    assert result.payout_units == 500_000
    assert result.bonus_payout_units == 500_000 - result.base.payout_units
    assert sum(result.free_spin_credits) == result.bonus_payout_units
    assert result.cap_reduction_units == result.raw_payout_units - 500_000
    remaining = 500_000 - result.base.payout_units
    for fs, credited in zip(result.free_spins, result.free_spin_credits):
        _assert_spin(fs)
        assert credited == min(fs.payout_units, remaining)
        assert 0 <= credited <= fs.payout_units
        remaining -= credited
    assert remaining == 0
    assert game.cap_payout_units(500_001) == 500_000
    assert game.cap_payout_units(499_999) == 499_999
    assert game.cap_payout(5001) == 5000


def test_reachable_twelve_free_spin_maximum_witness_caps_8618_22():
    base_grid = _grid_from_stops((33, 26, 20, 14, 6))
    free_grid = _grid_from_stops((21, 15, 0, 3, 30))
    assert base_grid == [["P3"] * 5, ["L1"] * 5, ["SCATTER"] * 5]
    with patch.object(game, "generate_grid", side_effect=[base_grid] + [free_grid] * 12) as generate:
        result = game.play_round(_ExpansionRng(2), expansion_probability=1)
    assert generate.call_count == 13
    assert result.base.scatter_count == 5
    assert result.base.payout_units == 5022
    assert result.base.free_spins_awarded == 12
    assert len(result.free_spins) == 12
    assert all(fs.raw_payout_units == 71400 for fs in result.free_spins)
    assert result.raw_payout_units == 861822
    assert result.payout_units == 500000
    assert result.cap_reduction_units == 361822
    assert result.free_spin_credits == (71400,) * 6 + (66578,) + (0,) * 5
    assert sum(result.free_spin_credits) + result.base.payout_units == 500000


def test_round_full_history_is_seed_deterministic():
    def rounds(seed):
        rng = random.Random(seed)
        return tuple(game.play_round(rng) for _ in range(500))
    a = rounds(123)
    b = rounds(123)
    c = rounds(124)
    assert a == b
    assert a != c
    assert any(result.free_spins for result in a)
    for result in a:
        _assert_spin(result.base)
        assert result.raw_payout_units == result.base.raw_payout_units + sum(fs.raw_payout_units for fs in result.free_spins)
        assert result.payout_units == min(result.raw_payout_units, 500_000)
        assert result.payout_units == result.base.payout_units + sum(result.free_spin_credits)
        assert result.bonus_payout == result.bonus_payout_units / 100
        assert result.payout == result.payout_units / 100


if __name__ == "__main__":
    executed = 0
    for name, function in tuple(globals().items()):
        if name.startswith("test_") and callable(function):
            function()
            print(f"PASS {name}")
            executed += 1
    print(f"{executed} tests passed")
