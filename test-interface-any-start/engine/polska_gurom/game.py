"""Authoritative integer payout model, independent of frontend animation."""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
import random
from .config import (
    REEL_STRIPS, PAYLINES, PAYTABLE_UNITS, REGULAR_SYMBOLS, SYMBOLS,
    WILD, SCATTER, SCATTER_PAYTABLE_UNITS, FREE_SPINS, MAX_WIN_UNITS,
    PAYOUT_SCALE, FS_LINE_MULTIPLIER, EXPANDING_WILD_NUMERATOR,
    EXPANDING_WILD_DENOMINATOR, EXPANDING_REELS,
    REFILL_STRIPS, ROWS, REELS, MAX_CASCADES,
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
    start_reel: int = 0

    @property
    def positions(self) -> tuple[tuple[int, int], ...]:
        return tuple((self.rows[reel], reel)
                     for reel in range(self.start_reel, self.start_reel + self.count))

    @property
    def payout(self) -> float:
        return self.payout_units / PAYOUT_SCALE


@dataclass(frozen=True)
class SymbolMove:
    symbol: str
    from_row: int
    to_row: int
    reel: int


@dataclass(frozen=True)
class CascadeStep:
    evaluation_grid: Grid
    line_wins: tuple[LineWin, ...]
    line_payout_units: int
    payout_units: int
    removed_positions: tuple[tuple[int, int], ...] = ()
    movements: tuple[SymbolMove, ...] = ()


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
    cascades: tuple[CascadeStep, ...] = ()
    cascade_limit_reached: bool = False

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


def tumble_grid(grid, positions, rng: random.Random) -> tuple[Grid, tuple[SymbolMove, ...]]:
    """Remove a union of cells, preserve survivor order, and refill from above.

    Only moved survivors and new symbols need animation records. A new symbol's
    negative starting row places it immediately above the visible reel.
    """
    original = _grid_snapshot(grid)
    removed = set()
    for position in positions:
        if len(position) != 2:
            raise ValueError("Removal positions must be (row, reel) pairs")
        row, reel = position
        if (not isinstance(row, int) or isinstance(row, bool) or
                not isinstance(reel, int) or isinstance(reel, bool) or
                row not in range(ROWS) or reel not in range(REELS)):
            raise ValueError("Invalid removal position")
        removed.add((row, reel))
    result = [list(row) for row in original]
    moves = []
    for reel in range(REELS):
        survivors = [(row, original[row][reel]) for row in range(ROWS)
                     if (row, reel) not in removed]
        holes = ROWS - len(survivors)
        for to_row in range(holes):
            symbol = rng.choice(REFILL_STRIPS[reel])
            result[to_row][reel] = symbol
            moves.append(SymbolMove(symbol, to_row - holes, to_row, reel))
        for index, (from_row, symbol) in enumerate(survivors):
            to_row = holes + index
            result[to_row][reel] = symbol
            if from_row != to_row:
                moves.append(SymbolMove(symbol, from_row, to_row, reel))
    return _grid_snapshot(result), tuple(moves)


def _prefix_award(symbols) -> tuple[str | None, int, int]:
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


@lru_cache(maxsize=100000)
def _line_award_with_start(symbols: tuple[str, ...]) -> tuple[str | None, int, int, int]:
    """One highest award per payline; the run may start on any of reels 1–3.

    Evaluate maximal consecutive runs, including Wild substitutions. Overlapping
    shorter windows never pay in addition to the selected award on that line.
    Equal awards use the leftmost starting reel for deterministic highlighting.
    """
    best = (None, 0, 0, 0)
    for start in range(len(symbols) - 2):
        symbol, count, units = _prefix_award(symbols[start:])
        if units > best[2]:
            best = (symbol, count, units, start)
    return best


def _line_award(symbols) -> tuple[str | None, int, int]:
    return _line_award_with_start(tuple(symbols))[:3]


def _line_best_win(symbols) -> float:
    return _line_award(symbols)[2] / PAYOUT_SCALE


def evaluate_line_wins(grid, multiplier: int = 1) -> tuple[LineWin, ...]:
    if not isinstance(multiplier, int) or isinstance(multiplier, bool) or multiplier < 1:
        raise ValueError("Line multiplier must be a positive integer")
    wins = []
    for line_id, rows in enumerate(PAYLINES, start=1):
        symbols = tuple(grid[rows[reel]][reel] for reel in range(5))
        symbol, count, units, start = _line_award_with_start(symbols)
        if units:
            wins.append(LineWin(line_id, rows, symbol, count, units * multiplier, multiplier, start))
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


def _cascade_result(original: Grid, initial: Grid, rng: random.Random,
                    scatter_count: int, scatter_units: int, free_spins: int,
                    reel: int | None, multiplier: int,
                    payout_limit_units: int) -> SpinResult:
    if (not isinstance(payout_limit_units, int) or isinstance(payout_limit_units, bool)
            or not 0 <= payout_limit_units <= MAX_WIN_UNITS):
        raise ValueError("Spin payout limit must be an integer within the round cap")
    steps = []
    current = initial
    raw_lines = 0
    credited = min(scatter_units, payout_limit_units)
    limit_reached = False
    for index in range(MAX_CASCADES):
        wins = evaluate_line_wins(current, multiplier)
        raw = sum(win.payout_units for win in wins)
        raw_lines += raw
        line_credit = min(raw, payout_limit_units - credited)
        credited += line_credit
        removed, moves = (), ()
        next_grid = None
        if wins and credited < payout_limit_units:
            if index + 1 == MAX_CASCADES:
                limit_reached = True
            else:
                removed = tuple(sorted({position for win in wins for position in win.positions}))
                next_grid, moves = tumble_grid(current, removed, rng)
        steps.append(CascadeStep(current, wins, raw, line_credit, removed, moves))
        if next_grid is None:
            break
        current = next_grid
    return SpinResult(
        grid=original, evaluation_grid=initial, line_wins=steps[0].line_wins,
        line_payout_units=raw_lines, scatter_payout_units=scatter_units,
        raw_payout_units=raw_lines + scatter_units, payout_units=credited,
        scatter_count=scatter_count, bonus_triggered=free_spins > 0,
        free_spins_awarded=free_spins, expanding_reel=reel,
        line_multiplier=multiplier, cascades=tuple(steps),
        cascade_limit_reached=limit_reached,
    )


def evaluate_paid_spin(grid, rng: random.Random | None = None, *,
                       payout_limit_units: int = MAX_WIN_UNITS) -> SpinResult:
    original = _grid_snapshot(grid)
    sc = count_scatter(original)
    sp = SCATTER_PAYTABLE_UNITS.get(min(sc, 5), 0) if sc >= 3 else 0
    fs = free_spins_for_scatter(sc)
    return _cascade_result(original, original, rng if rng is not None else random.Random(),
                           sc, sp, fs, None, 1, payout_limit_units)


def _should_expand(rng, probability: float | None) -> bool:
    if probability is None:
        return rng.randrange(EXPANDING_WILD_DENOMINATOR) < EXPANDING_WILD_NUMERATOR
    if not 0 <= probability <= 1:
        raise ValueError("Expansion probability must be in [0, 1]")
    return rng.random() < probability


def evaluate_free_spin(grid, rng: random.Random,
                       expansion_probability: float | None = None, *,
                       payout_limit_units: int = MAX_WIN_UNITS) -> SpinResult:
    original = _grid_snapshot(grid)
    sc = count_scatter(original)  # Count Scatter BEFORE the Wild expansion.
    sp = SCATTER_PAYTABLE_UNITS.get(min(sc, 5), 0) if sc >= 3 else 0
    reel = rng.choice(EXPANDING_REELS) if _should_expand(rng, expansion_probability) else None
    transformed = _grid_snapshot(apply_expanding_wild(original, reel)) if reel is not None else original
    return _cascade_result(original, transformed, rng, sc, sp, 0,
                           reel, FS_LINE_MULTIPLIER, payout_limit_units)


def play_round(rng: random.Random,
               expansion_probability: float | None = None) -> RoundResult:
    base = evaluate_paid_spin(generate_grid(rng), rng)
    free_spins, credits = [], []
    remaining = MAX_WIN_UNITS - base.payout_units
    for _ in range(base.free_spins_awarded):
        if remaining <= 0:
            break
        spin = evaluate_free_spin(generate_grid(rng), rng, expansion_probability,
                                  payout_limit_units=remaining)
        free_spins.append(spin)
        credited = min(spin.payout_units, remaining)
        credits.append(credited)
        remaining -= credited
    raw = base.raw_payout_units + sum(spin.raw_payout_units for spin in free_spins)
    bonus_units = sum(credits)
    total = base.payout_units + bonus_units
    return RoundResult(base, tuple(free_spins), tuple(credits), raw, total, bonus_units, raw - total)
