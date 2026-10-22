"""Confirm important bugs are actually rejected; changes exist only in memory."""
from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import runpy
import sys
from unittest.mock import patch


def check(root: Path):
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(root))
    from polska_gurom import game
    tests = runpy.run_path(str(root / "tests" / "test_game.py"))
    original_score = game._line_best_win
    original_events = game.evaluate_line_wins
    original_fs = game.evaluate_free_spin
    original_round = game.play_round

    def doubled_events(grid, multiplier=1):
        return tuple(replace(event, payout_units=2 * event.payout_units)
                     for event in original_events(grid, multiplier))

    def dropped_event(grid, multiplier=1):
        return original_events(grid, multiplier)[1:]

    def scatter_after_expansion(grid, rng, expansion_probability=None):
        result = original_fs(grid, rng, expansion_probability)
        return replace(result, scatter_count=sum(cell == "SCATTER" for row in result.evaluation_grid for cell in row))

    def missing_credits(rng, expansion_probability=None):
        result = original_round(rng, expansion_probability)
        return replace(result, free_spin_credits=(0,) * len(result.free_spins))

    mutations = [
        ("double_single_line_payout", "_line_best_win", lambda symbols: 2 * original_score(symbols),
         "test_exhaustive_100000_line_sequences_against_independent_oracle"),
        ("double_event_payments", "evaluate_line_wins", doubled_events,
         "test_every_payline_event_matches_oracle_with_overlapping_prefixes"),
        ("drop_first_line_event", "evaluate_line_wins", dropped_event,
         "test_every_payline_event_matches_oracle_with_overlapping_prefixes"),
        ("ignore_scatter", "count_scatter", lambda grid: 0,
         "test_scatter_anywhere_pays_and_awards_only_in_paid_game"),
        ("zero_scatter_payment", "SCATTER_PAYTABLE_UNITS", {3: 0, 4: 0, 5: 0},
         "test_scatter_anywhere_pays_and_awards_only_in_paid_game"),
        ("expansion_does_nothing", "apply_expanding_wild", lambda grid, reel: grid,
         "test_expansion_uses_exactly_one_inner_reel_and_preserves_input"),
        ("scatter_count_after_expansion", "evaluate_free_spin", scatter_after_expansion,
         "test_expansion_uses_exactly_one_inner_reel_and_preserves_input"),
        ("ignore_round_cap", "cap_payout_units", lambda amount: amount,
         "test_round_cap_reconciles_base_bonus_and_every_credit"),
        ("missing_free_spin_credits", "play_round", missing_credits,
         "test_round_history_awards_8_10_12_without_retriggers"),
    ]
    results = {}
    for name, attr, changed, test_name in mutations:
        with patch.object(game, attr, changed):
            try:
                tests[test_name]()
            except AssertionError:
                results[name] = {"detected": True, "test": test_name}
            except Exception as exc:
                results[name] = {"detected": False, "test": test_name, "error": repr(exc)}
            else:
                results[name] = {"detected": False, "test": test_name}
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    result = check(args.root.resolve())
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if all(item["detected"] for item in result.values()) else 1)
