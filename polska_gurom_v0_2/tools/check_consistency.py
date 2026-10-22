"""Cross-check all scorers, natural reel grids and stale-data rejection."""
from __future__ import annotations
import argparse
import ast
import json
from pathlib import Path
import random
import runpy
import sys
import tempfile
from unittest.mock import patch
import numpy as np

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from polska_gurom import config as c, game
from tools.build_distribution import make_lut, scalar_grid_units
from tools.math_config import compute_config_fingerprint
from tools.verify_math import load_histograms, validate_config


def require(condition, message):
    if not condition:
        raise AssertionError(message)


class FixedExpansion:
    def __init__(self, reel):
        self.reel = reel
    def random(self):
        return 0.0
    def choice(self, choices):
        require(self.reel in choices, "Expansion outside permitted reels")
        return self.reel


def check(baseline=None):
    validate_config()
    syntax_files = list(ROOT.rglob("*.py"))
    for file in syntax_files:
        ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
    frozen_oracle = runpy.run_path(str(ROOT/"tests"/"test_game.py"))["_oracle_amount"]
    lut = make_lut()
    for code, value in enumerate(lut):
        sequence = [c.SYMBOLS[(code//10**p)%10] for p in range(4,-1,-1)]
        expected = frozen_oracle(sequence)
        require(int(value) == expected, f"Histogram LUT differs for {sequence}")
        require(game._line_award(sequence)[2] == expected, f"Runtime scorer differs for {sequence}")
    rng = random.Random(77183)
    for _ in range(1000):
        stops = [rng.randrange(len(strip)) for strip in c.REEL_STRIPS]
        grid = [[c.REEL_STRIPS[reel][(stops[reel]+row)%len(c.REEL_STRIPS[reel])]
                 for reel in range(c.REELS)] for row in range(c.ROWS)]
        line, scatter, sc = scalar_grid_units(grid)
        paid = game.evaluate_paid_spin(grid)
        require(paid.line_payout_units == line and paid.scatter_payout_units == scatter,
                "Runtime paid spin differs from independent natural-window oracle")
        require(paid.scatter_count == sc, "Original Scatter count differs")
        require(sum(x.payout_units for x in paid.line_wins) == line, "Line event ledger differs")
        for reel in c.EXPANDING_REELS:
            line, scatter, sc = scalar_grid_units(grid, reel)
            free = game.evaluate_free_spin(grid, FixedExpansion(reel), 1)
            require(free.line_payout_units == c.FS_LINE_MULTIPLIER*line
                    and free.scatter_payout_units == scatter and free.scatter_count == sc,
                    "Runtime expanded FS differs from independent grid oracle")
            require(sum(x.payout_units for x in free.line_wins) == free.line_payout_units,
                    "Free-spin line events do not reconcile")
    current, denominator, fingerprint = load_histograms(ROOT/"verification"/"joint_counts.npz")
    baseline_compared = False
    if baseline is not None:
        with np.load(baseline, allow_pickle=False) as old:
            for key, value in current.items():
                require(np.array_equal(value, old[key]), f"Repeated enumeration differs for {key}")
        baseline_compared = True
    with tempfile.TemporaryDirectory(prefix="stale-check-", dir=ROOT/"verification") as folder:
        bad = Path(folder)/"bad.npz"
        np.savez_compressed(bad, __math_config_sha256__=np.array("stale"), __format_version__=np.array(1))
        try:
            load_histograms(bad)
        except ValueError as error:
            require("Stale histogram" in str(error), "Unexpected stale-data error")
        else:
            raise AssertionError("Stale histogram was accepted")
    changed = {**c.MATH_ASSUMPTIONS, "retriggers_enabled": True}
    with patch.object(c, "MATH_ASSUMPTIONS", changed):
        require(compute_config_fingerprint(c) != fingerprint, "Rule assumptions missing from fingerprint")
        try:
            validate_config()
        except ValueError:
            pass
        else:
            raise AssertionError("Unsupported retriggers were accepted")
    return {"passed": True, "math_config_sha256": fingerprint,
            "syntax_files_checked": len(syntax_files), "all_symbol_sequences_checked": len(lut),
            "independent_natural_base_grids_checked": 1000,
            "independent_expanded_free_spin_grids_checked": 3000,
            "histograms_repeated_enumeration_equal": baseline_compared,
            "exact_reel_combinations": denominator,
            "stale_histograms_rejected": True, "changed_assumptions_rejected": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    report = check(args.baseline)
    path = ROOT/"verification"/"consistency_checks.json"
    path.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
