"""Independent reference scorer, intentionally not importing production game logic.

Amounts are integer units of 1 / 1_000_000 total bet.  The caller supplies its
paytable, but the scoring algorithm and the traversal of paylines are separate.
This also works against v0.1 for regression/mutation checks.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from itertools import product
from typing import Iterable, Mapping, Sequence

UNIT = 1_000_000
REGULAR_SYMBOLS = ("L1", "L2", "L3", "L4", "P1", "P2", "P3", "P4")
ALL_SYMBOLS = (*REGULAR_SYMBOLS, "WILD", "SCATTER")

# Frozen values from the agreed original table. Their explicit duplication is
# deliberate: importing production PAYTABLE alone would not detect table drift.
FROZEN_PAYTABLE_UNITS = {
    "L1": {3: 200_000, 4: 800_000, 5: 2_500_000},
    "L2": {3: 250_000, 4: 1_000_000, 5: 3_500_000},
    "L3": {3: 300_000, 4: 1_200_000, 5: 4_500_000},
    "L4": {3: 400_000, 4: 1_600_000, 5: 6_000_000},
    "P1": {3: 600_000, 4: 2_500_000, 5: 10_000_000},
    "P2": {3: 800_000, 4: 3_500_000, 5: 15_000_000},
    "P3": {3: 1_200_000, 4: 5_500_000, 5: 25_000_000},
    "P4": {3: 2_000_000, 4: 10_000_000, 5: 50_000_000},
}


@dataclass(frozen=True)
class OracleLine:
    amount_units: int
    symbol: str
    count: int


def units(value: object) -> int:
    """Convert x-bet decimal values without accepting fractional unit rounding."""
    amount = Decimal(str(value)) * UNIT
    if amount != amount.to_integral_value():
        raise ValueError(f"Value cannot be represented in 1/{UNIT} units: {value}")
    return int(amount)


def line_options(
    symbols: Sequence[str],
    paytable: Mapping[str, Mapping[int, int]] = FROZEN_PAYTABLE_UNITS,
) -> tuple[OracleLine, ...]:
    """Enumerate valid target sets for every left-anchored prefix.

    A SCATTER clears the set, whereas WILD leaves it unchanged. This differs
    structurally from the production target-by-target matching loop.
    """
    possible = set(paytable)
    options = []
    for count, current in enumerate(symbols, start=1):
        if current != "WILD":
            possible.intersection_update((current,))
        if not possible:
            break
        if count >= 3:
            for target in sorted(possible):
                amount = paytable[target].get(count, 0)
                if amount:
                    options.append(OracleLine(amount, target, count))
    return tuple(options)


def best_line(
    symbols: Sequence[str],
    paytable: Mapping[str, Mapping[int, int]] = FROZEN_PAYTABLE_UNITS,
) -> OracleLine | None:
    options = line_options(symbols, paytable)
    if not options:
        return None
    # A tie policy is presentation-only; score/cells must describe one option.
    return max(options, key=lambda item: (item.amount_units, item.count, item.symbol))


def score_grid(
    grid: Sequence[Sequence[str]],
    paylines: Iterable[Sequence[int]],
    paytable: Mapping[str, Mapping[int, int]] = FROZEN_PAYTABLE_UNITS,
) -> tuple[int, dict[int, tuple[OracleLine, tuple[tuple[int, int], ...]]]]:
    events = {}
    for line_id, rows in enumerate(paylines, start=1):
        symbols = tuple(grid[row][reel] for reel, row in enumerate(rows))
        outcome = best_line(symbols, paytable)
        if outcome is not None:
            positions = tuple((rows[reel], reel) for reel in range(outcome.count))
            events[line_id] = (outcome, positions)
    return sum(item[0].amount_units for item in events.values()), events


def exhaustive_line_cases():
    for symbols in product(ALL_SYMBOLS, repeat=5):
        winner = best_line(symbols)
        yield symbols, 0 if winner is None else winner.amount_units


def check_original(root: str) -> dict:
    """Read-only audit against the old implementation; run in a fresh process."""
    import sys
    sys.dont_write_bytecode = True
    sys.path.insert(0, root)
    from polska_gurom.game import _line_best_win
    checked = 0
    mismatches = []
    for symbols, expected in exhaustive_line_cases():
        actual = units(_line_best_win(list(symbols)))
        checked += 1
        if actual != expected:
            mismatches.append((symbols, actual, expected))
            if len(mismatches) > 20:
                break
    return {"checked": checked, "mismatches": mismatches}


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument("--original-root", required=True)
    args = parser.parse_args()
    print(json.dumps(check_original(args.original_root), indent=2))
