"""Independent falling-cascade invariants and a small diagnostic sample.

This script does not call the production line evaluator to calculate expected
awards. It does not establish a theoretical RTP or certify gambling software.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "engine"))
from polska_gurom import config, game

REPORT = ROOT / "qa" / "cascade_math_checks.json"
COUNTS = Counter()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def independent_wins(grid, multiplier):
    """Enumerate every payable contiguous interval, independently of the engine."""
    result = []
    for number, rows in enumerate(config.PAYLINES, 1):
        line = [grid[row][reel] for reel, row in enumerate(rows)]
        candidates = []
        for start in range(3):
            for count in range(3, 6-start):
                regular = set(line[start:start+count]) - {config.WILD}
                for order, (symbol, pays) in enumerate(config.PAYTABLE_UNITS.items()):
                    if regular <= {symbol}:
                        candidates.append((pays[count], -start, -order, count, symbol))
        if not candidates:
            continue
        units, negative_start, _, count, symbol = max(candidates)
        result.append((number, tuple(rows), symbol, count, units * multiplier,
                       multiplier, -negative_start))
    return result


def validate_grid(grid):
    require(len(grid) == 3 and all(len(row) == 5 for row in grid), "3 by 5 grid")
    require(all(symbol in config.SYMBOLS for row in grid for symbol in row), "known symbols")


def validate_transition(step, next_step, expected_removed):
    require(tuple(step.removed_positions) == tuple(sorted(expected_removed)), "removed union")
    require(len(set(step.removed_positions)) == len(step.removed_positions), "unique removals")
    before, after = step.evaluation_grid, next_step.evaluation_grid
    moves = {}
    for move in step.movements:
        require((move.to_row, move.reel) not in moves, "unique movement destination")
        require(0 <= move.to_row < 3 and 0 <= move.reel < 5, "movement in grid")
        require(move.from_row < move.to_row, "movement points down")
        moves[move.to_row, move.reel] = move
    expected_destinations = set()
    for reel in range(5):
        survivors = [(row, before[row][reel]) for row in range(3)
                     if (row, reel) not in expected_removed]
        holes = 3 - len(survivors)
        for row in range(holes):
            expected_destinations.add((row, reel))
            require((row, reel) in moves, "new symbol has movement")
            move = moves[row, reel]
            require(move.from_row == row - holes, "new symbol starts above reel")
            require(move.symbol != config.SCATTER, "refills exclude Scatter")
            require(move.symbol in config.REFILL_STRIPS[reel], "refill belongs to reel")
            require(after[row][reel] == move.symbol, "new symbol matches next grid")
            COUNTS["new_symbols_checked"] += 1
        for index, (from_row, symbol) in enumerate(survivors):
            to_row = holes + index
            require(after[to_row][reel] == symbol, "survivor relative order and symbol")
            if from_row != to_row:
                expected_destinations.add((to_row, reel))
                require((to_row, reel) in moves, "falling survivor has movement")
                move = moves[to_row, reel]
                require((move.from_row, move.symbol) == (from_row, symbol), "survivor movement source")
                COUNTS["falling_survivors_checked"] += 1
        require([after[row][reel] for row in range(holes, 3)] ==
                [symbol for _, symbol in survivors], "survivor order")
    require(set(moves) == expected_destinations, "no extra movements")
    require(sum(symbol == config.SCATTER for row in before for symbol in row) ==
            sum(symbol == config.SCATTER for row in after for symbol in row), "Scatter count persists")
    COUNTS["transitions_checked"] += 1


def validate_spin(spin, is_free=False, limit=config.MAX_WIN_UNITS):
    validate_grid(spin.grid)
    validate_grid(spin.evaluation_grid)
    multiplier = config.FS_LINE_MULTIPLIER if is_free else 1
    require(spin.line_multiplier == multiplier, "base/free line multiplier")
    scatters = sum(symbol == config.SCATTER for row in spin.grid for symbol in row)
    scatter_units = config.SCATTER_PAYTABLE_UNITS.get(min(scatters, 5), 0)
    require(spin.scatter_count == scatters, "Scatter evaluated before expansion")
    require(spin.scatter_payout_units == scatter_units, "Scatter not multiplied")
    awarded = 0 if is_free else config.FREE_SPINS.get(min(scatters, 5), 0)
    require(spin.free_spins_awarded == awarded, "free spin trigger award/no retrigger")
    require(spin.bonus_triggered == bool(awarded), "bonus flag")
    expected_initial = [list(row) for row in spin.grid]
    if spin.expanding_reel is not None:
        require(is_free and spin.expanding_reel in config.EXPANDING_REELS, "expansion only in free spins")
        for row in range(3):
            expected_initial[row][spin.expanding_reel] = config.WILD
        COUNTS["expansions_checked"] += 1
    require(tuple(map(tuple, expected_initial)) == spin.evaluation_grid, "initial expansion grid")
    require(bool(spin.cascades), "spin contains evaluation stage")
    require(spin.cascades[0].evaluation_grid == spin.evaluation_grid, "first cascade grid")
    require(spin.line_wins == spin.cascades[0].line_wins, "first wins compatibility")
    credited = min(scatter_units, limit)
    raw_lines = 0
    for index, step in enumerate(spin.cascades):
        validate_grid(step.evaluation_grid)
        expected = independent_wins(step.evaluation_grid, multiplier)
        actual = [(win.line_id, tuple(win.rows), win.symbol, win.count,
                   win.payout_units, win.line_multiplier, win.start_reel) for win in step.line_wins]
        require(actual == expected, "independent intervals equal every cascade line")
        raw = sum(win[4] for win in expected)
        require(step.line_payout_units == raw, "cascade raw sum")
        require(step.payout_units == min(raw, limit - credited), "cascade credit respects remaining cap")
        credited += step.payout_units
        raw_lines += raw
        union = {(rows[reel], reel) for _, rows, _, count, _, _, start in expected
                 for reel in range(start, start + count)}
        if index + 1 < len(spin.cascades):
            require(bool(expected) and credited < limit, "continue only after uncapped win")
            validate_transition(step, spin.cascades[index + 1], union)
        else:
            require(not step.removed_positions and not step.movements, "terminal stage has no unplayed transition")
            if expected and credited < limit:
                require(spin.cascade_limit_reached and len(spin.cascades) == config.MAX_CASCADES,
                        "winning terminal stage requires safeguard")
        COUNTS["stages_checked"] += 1
        COUNTS["line_awards_checked"] += len(expected)
    require(spin.line_payout_units == raw_lines, "spin aggregates all cascade lines")
    require(spin.raw_payout_units == raw_lines + scatter_units, "spin raw lines plus Scatter")
    require(spin.payout_units == credited == min(spin.raw_payout_units, limit), "spin settlement")
    require(spin.cap_reduction_units == spin.raw_payout_units - spin.payout_units, "spin cap reduction")
    COUNTS["free_spins_checked" if is_free else "base_spins_checked"] += 1


def validate_round(result):
    validate_spin(result.base)
    remaining = config.MAX_WIN_UNITS - result.base.payout_units
    require(len(result.free_spins) == len(result.free_spin_credits), "one credit per free spin")
    require(len(result.free_spins) <= result.base.free_spins_awarded, "no extra free spins")
    for spin, credit in zip(result.free_spins, result.free_spin_credits):
        validate_spin(spin, True, remaining)
        require(credit == spin.payout_units == min(spin.raw_payout_units, remaining), "free spin settlement")
        remaining -= credit
    require(len(result.free_spins) == result.base.free_spins_awarded or remaining == 0,
            "all awarded free spins played unless cap reached")
    raw = result.base.raw_payout_units + sum(spin.raw_payout_units for spin in result.free_spins)
    total = result.base.payout_units + sum(result.free_spin_credits)
    require(result.raw_payout_units == raw, "round raw settlement")
    require(result.payout_units == total == min(raw, config.MAX_WIN_UNITS), "whole round cap")
    require(result.bonus_payout_units == sum(result.free_spin_credits), "bonus aggregate")
    require(result.cap_reduction_units == raw - total, "round cap reduction")
    require(total <= 5000 * config.PAYOUT_SCALE, "5000 times total bet limit")


class ConstantRefills(random.Random):
    def choice(self, sequence):
        return "P4" if "P4" in sequence else sequence[0]


def check_forced_cases():
    dense = tuple(("P4",) * 5 for _ in range(3))
    for limit in (0, 1, 37, 1150, config.MAX_WIN_UNITS):
        spin = game.evaluate_paid_spin(dense, ConstantRefills(19), payout_limit_units=limit)
        validate_spin(spin, limit=limit)
        require(spin.payout_units == limit, "forced base limit exactly reached")
    for limit in (1, 1500, config.MAX_WIN_UNITS):
        spin = game.evaluate_free_spin(dense, ConstantRefills(19), expansion_probability=0,
                                       payout_limit_units=limit)
        validate_spin(spin, True, limit)
        require(spin.payout_units == limit, "forced free spin limit exactly reached")
    before_expansion = tuple(tuple("SCATTER" if reel == 1 else "L1" for reel in range(5))
                             for _ in range(3))
    spin = game.evaluate_free_spin(before_expansion, ConstantRefills(19), expansion_probability=1)
    validate_spin(spin, True)
    require(spin.scatter_count == 3 and spin.scatter_payout_units == 100, "Scatter award survives overwritten reel")
    require(all(row[1] == "WILD" for row in spin.evaluation_grid), "forced expanding reel")
    with patch.object(game, "generate_grid", return_value=dense):
        capped_base = game.play_round(ConstantRefills(19), expansion_probability=0)
    validate_round(capped_base)
    require(capped_base.payout_units == config.MAX_WIN_UNITS and not capped_base.free_spins,
            "full round can finish at base cap")
    trigger = (("SCATTER", "L1", "L2", "L3", "L4"),
               ("SCATTER", "P1", "P2", "P3", "P4"),
               ("SCATTER", "L4", "L3", "L2", "L1"))
    # Inject explicit grids only inside this process to isolate round-credit
    # boundaries; the production generator and its files remain untouched.
    with patch.object(game, "generate_grid", side_effect=[trigger, dense]):
        capped_bonus = game.play_round(ConstantRefills(19), expansion_probability=0)
    validate_round(capped_bonus)
    require(capped_bonus.base.payout_units == 100 and len(capped_bonus.free_spins) == 1,
            "bonus cap stops remaining free spins")
    require(capped_bonus.free_spin_credits == (config.MAX_WIN_UNITS - 100,),
            "bonus cap credits remaining whole-round amount")
    return {"forced_base_limits": 5, "forced_free_limits": 3,
            "scatter_before_expansion": True, "partial_final_award": True,
            "full_round_base_cap": True, "full_round_bonus_cap": True}


def original_manifest():
    original = ROOT.parent / "polska_gurom_v0_2"
    manifest = json.loads((original / "verification" / "file_manifest.json").read_text(encoding="utf-8"))
    changed = [name for name, digest in manifest.items()
               if hashlib.sha256((original / name).read_bytes()).hexdigest() != digest]
    require(not changed, "original v0.2 manifest unchanged: " + repr(changed))
    return {"files_checked": len(manifest), "unchanged": True}


def main():
    started = time.monotonic()
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000
    report = {"success": False, "rounds": rounds,
              "scope": "Independent line, movement and settlement invariants; diagnostic random sample only.",
              "rtp_notice": "Empirical result from this small sample is not theoretical RTP, a 96% claim, or certification."}
    try:
        report["original_v0_2"] = original_manifest()
        report["forced_cases"] = check_forced_cases()
        total_units = base_units = bonus_units = bonus_rounds = cascaded_bases = 0
        maximum = 0
        for seed in range(rounds):
            result = game.play_round(random.Random(seed))
            validate_round(result)
            total_units += result.payout_units
            base_units += result.base.payout_units
            bonus_units += result.bonus_payout_units
            bonus_rounds += bool(result.free_spins)
            cascaded_bases += len(result.base.cascades) > 1
            maximum = max(maximum, result.payout_units)
        report.update(success=True, deterministic_seeds={"first": 0, "last": rounds - 1},
                      bonus_rounds=bonus_rounds, base_rounds_with_cascades=cascaded_bases,
                      empirical_rtp_percent=total_units / rounds / config.PAYOUT_SCALE * 100,
                      empirical_base_return_percent=base_units / rounds / config.PAYOUT_SCALE * 100,
                      empirical_bonus_return_percent=bonus_units / rounds / config.PAYOUT_SCALE * 100,
                      maximum_observed_bet_multiple=maximum / config.PAYOUT_SCALE)
    except Exception as error:
        report["failure"] = repr(error)
        raise
    finally:
        report["counts"] = dict(COUNTS)
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
