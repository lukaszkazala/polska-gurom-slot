"""Authoritative integer payout model, independent of frontend animation."""
from __future__ import annotations
from dataclasses import dataclass
import random
from .config import (
    REEL_STRIPS, PAYLINES, PAYTABLE_UNITS, REGULAR_SYMBOLS, SYMBOLS,
    WILD, SCATTER, SCATTER_PAYTABLE_UNITS, FREE_SPINS, MAX_WIN_UNITS,
    PAYOUT_SCALE, FS_LINE_MULTIPLIER, EXPANDING_WILD_NUMERATOR,
    EXPANDING_WILD_DENOMINATOR, EXPANDING_REELS,
)

Grid = tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class LineWin:
    line_id: int
    rows: tuple[int, ...]
    symbol: str
    count: int
    payout_units: int
    line_multiplier: int = 1

    @property
    def positions(self) -> tuple[tuple[int, int], ...]:
        return tuple((self.rows[reel], reel) for reel in range(self.count))

    @property
    def payout(self) -> float:
        return self.payout_units / PAYOUT_SCALE


@dataclass(frozen=True)
class SpinResult:
    grid: Grid
    evaluation_grid: Grid
    line_wins: tuple[LineWin, ...]
    line_payout_units: int
    scatter_payout_units: int
    raw_payout_units: int
    payout_units: int
    scatter_count: int
    bonus_triggered: bool
    free_spins_awarded: int
    expanding_reel: int | None = None
    line_multiplier: int = 1

    @property
    def payout(self) -> float:
        return self.payout_units / PAYOUT_SCALE

    @property
    def line_payout(self) -> float:
        return self.line_payout_units / PAYOUT_SCALE

    @property
    def scatter_payout(self) -> float:
        return self.scatter_payout_units / PAYOUT_SCALE

    @property
    def cap_reduction_units(self) -> int:
        return self.raw_payout_units - self.payout_units


@dataclass(frozen=True)
class RoundResult:
    base: SpinResult
    free_spins: tuple[SpinResult, ...]
    free_spin_credits: tuple[int, ...]
    raw_payout_units: int
    payout_units: int
    bonus_payout_units: int
    cap_reduction_units: int

    @property
    def expansions(self) -> int:
        return sum(spin.expanding_reel is not None for spin in self.free_spins)

    @property
    def payout(self) -> float:
        return self.payout_units / PAYOUT_SCALE

    @property
    def bonus_payout(self) -> float:
        return self.bonus_payout_units / PAYOUT_SCALE


def _grid_snapshot(grid) -> Grid:
    if len(grid) != 3 or any(len(row) != 5 for row in grid):
        raise ValueError("Expected a 3-row, 5-reel grid")
    if any(symbol not in SYMBOLS for row in grid for symbol in row):
        raise ValueError("Unknown symbol")
    return tuple(tuple(row) for row in grid)


def window_for_stop(strip: tuple[str, ...], stop: int) -> tuple[str, str, str]:
    return tuple(strip[(stop + row) % len(strip)] for row in range(3))


def generate_grid(rng: random.Random) -> list[list[str]]:
    cols = [window_for_stop(strip, rng.randrange(len(strip))) for strip in REEL_STRIPS]
    return [[cols[reel][row] for reel in range(5)] for row in range(3)]


def _line_award(symbols) -> tuple[str | None, int, int]:
    """Best regular-symbol interpretation once, including all-Wild prefixes."""
    best_symbol, best_count, best_units = None, 0, 0
    for target in REGULAR_SYMBOLS:
        count = 0
        for symbol in symbols:
            if symbol not in (target, WILD):
                break
            count += 1
        if count >= 3:
            units = PAYTABLE_UNITS[target][count]
            if units > best_units:
                best_symbol, best_count, best_units = target, count, units
    return best_symbol, best_count, best_units


def _line_best_win(symbols) -> float:
    return _line_award(symbols)[2] / PAYOUT_SCALE


def evaluate_line_wins(grid, multiplier: int = 1) -> tuple[LineWin, ...]:
    if not isinstance(multiplier, int) or isinstance(multiplier, bool) or multiplier < 1:
        raise ValueError("Line multiplier must be a positive integer")
    wins = []
    for line_id, rows in enumerate(PAYLINES, start=1):
        symbols = tuple(grid[rows[reel]][reel] for reel in range(5))
        symbol, count, units = _line_award(symbols)
        if units:
            wins.append(LineWin(line_id, rows, symbol, count, units * multiplier, multiplier))
    return tuple(wins)


def evaluate_lines(grid) -> float:
    return sum(win.payout_units for win in evaluate_line_wins(grid)) / PAYOUT_SCALE


def count_scatter(grid) -> int:
    return sum(cell == SCATTER for row in grid for cell in row)


def scatter_payout(count: int) -> float:
    return SCATTER_PAYTABLE_UNITS.get(min(count, 5), 0) / PAYOUT_SCALE if count >= 3 else 0.0


def free_spins_for_scatter(count: int) -> int:
    return FREE_SPINS.get(min(count, 5), 0) if count >= 3 else 0


def apply_expanding_wild(grid, reel_index: int) -> list[list[str]]:
    if reel_index not in range(5):
        raise ValueError("Invalid reel index")
    out = [list(row) for row in grid]
    for row in range(3):
        out[row][reel_index] = WILD
    return out


def cap_payout_units(value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError("Payout must be a non-negative integer")
    return min(value, MAX_WIN_UNITS)


def cap_payout(value: float) -> float:
    """Compatibility view; integer cap_payout_units is used for settlement."""
    return min(value, MAX_WIN_UNITS / PAYOUT_SCALE)


def evaluate_paid_spin(grid) -> SpinResult:
    original = _grid_snapshot(grid)
    sc = count_scatter(original)
    wins = evaluate_line_wins(original)
    lp = sum(win.payout_units for win in wins)
    sp = SCATTER_PAYTABLE_UNITS.get(min(sc, 5), 0) if sc >= 3 else 0
    fs = free_spins_for_scatter(sc)
    raw = lp + sp
    return SpinResult(original, original, wins, lp, sp, raw, cap_payout_units(raw), sc, fs > 0, fs)


def _should_expand(rng, probability: float | None) -> bool:
    if probability is None:
        return rng.randrange(EXPANDING_WILD_DENOMINATOR) < EXPANDING_WILD_NUMERATOR
    if not 0 <= probability <= 1:
        raise ValueError("Expansion probability must be in [0, 1]")
    return rng.random() < probability


def evaluate_free_spin(grid, rng: random.Random,
                       expansion_probability: float | None = None) -> SpinResult:
    original = _grid_snapshot(grid)
    sc = count_scatter(original)  # Count Scatter BEFORE the Wild expansion.
    sp = SCATTER_PAYTABLE_UNITS.get(min(sc, 5), 0) if sc >= 3 else 0
    reel = rng.choice(EXPANDING_REELS) if _should_expand(rng, expansion_probability) else None
    transformed = _grid_snapshot(apply_expanding_wild(original, reel)) if reel is not None else original
    wins = evaluate_line_wins(transformed, FS_LINE_MULTIPLIER)
    lp = sum(win.payout_units for win in wins)
    raw = lp + sp
    return SpinResult(original, transformed, wins, lp, sp, raw, cap_payout_units(raw),
                      sc, False, 0, reel, FS_LINE_MULTIPLIER)


def play_round(rng: random.Random,
               expansion_probability: float | None = None) -> RoundResult:
    base = evaluate_paid_spin(generate_grid(rng))
    free_spins, credits = [], []
    remaining = MAX_WIN_UNITS - base.payout_units
    for _ in range(base.free_spins_awarded):
        spin = evaluate_free_spin(generate_grid(rng), rng, expansion_probability)
        free_spins.append(spin)
        credited = min(spin.payout_units, remaining)
        credits.append(credited)
        remaining -= credited
    raw = base.raw_payout_units + sum(spin.raw_payout_units for spin in free_spins)
    bonus_units = sum(credits)
    total = base.payout_units + bonus_units
    return RoundResult(base, tuple(free_spins), tuple(credits), raw, total, bonus_units, raw - total)
