"""Additional current-source checks against freshly enumerated distributions."""
from collections import Counter
from decimal import Decimal, localcontext, ROUND_CEILING
from fractions import Fraction
import json
from pathlib import Path
import random
import sys

sys.dont_write_bytecode = True
PROJECT = Path(__file__).resolve().parents[3] / "polska_gurom_v0_2"
OUTPUT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))
import numpy as np
from polska_gurom import config as c, game
from tools.build_distribution import make_lut, make_windows, evaluate_stops, scalar_grid_units
from tools.verify_math import load_histograms, payout_counts, scatter_units

hist, denominator, fingerprint = load_histograms(OUTPUT / "joint_counts.npz")
with np.load(PROJECT / "verification" / "joint_counts.npz", allow_pickle=False) as archive:
    old_equal = {key: bool(np.array_equal(value, archive[key])) for key, value in hist.items()}

class Expansion:
    def __init__(self, reel): self.reel = reel
    def random(self): return 0.0
    def choice(self, choices):
        assert self.reel in choices
        return self.reel

rng = random.Random(20261019)
natural_grids = 1000
for _ in range(natural_grids):
    grid = game.generate_grid(rng)
    for forced in (None, *c.EXPANDING_REELS):
        line, scatter, sc = scalar_grid_units(grid, forced)
        spin = game.evaluate_paid_spin(grid) if forced is None else game.evaluate_free_spin(grid, Expansion(forced), 1)
        assert spin.line_payout_units == line * (1 if forced is None else 4)
        assert spin.scatter_payout_units == scatter
        assert spin.scatter_count == sc
        assert spin.line_payout_units == sum(w.payout_units for w in spin.line_wins)

untriggered_mass = sum(int(hist["base"][units, sc]) for units, sc in zip(*np.nonzero(hist["base"]))
                       if sc < 3 and units % 10)
untriggered_payout_counts = Counter()
for units, sc in zip(*np.nonzero(hist["base"])):
    if sc < 3 and units % 10:
        untriggered_payout_counts[int(units)] += int(hist["base"][units, sc])

p = Fraction(c.EXPANDING_WILD_NUMERATOR, c.EXPANDING_WILD_DENOMINATOR)
fs_denominator = denominator * p.denominator * len(c.EXPANDING_REELS)
fs_counts = Counter()
for payout, n in payout_counts(hist["base"], 4).items():
    fs_counts[payout] += n * (p.denominator - p.numerator) * len(c.EXPANDING_REELS)
for reel in c.EXPANDING_REELS:
    for payout, n in payout_counts(hist[f"forced_{reel}"], 4).items():
        fs_counts[payout] += n * p.numerator

# Independent Decimal Chernoff probability bounds at >= thresholds.
# Untriggered maximum is <1000x; only triggered rounds enter this MGF.
bounds = {}
with localcontext() as ctx:
    ctx.prec = 60
    ctx.rounding = ROUND_CEILING
    def exp_upper(value): return value.exp().next_plus()
    for t_string in ("0.004", "0.008", "0.012", "0.016", "0.020", "0.024", "0.028", "0.032"):
        t = Decimal(t_string)
        z_mgf = sum((Decimal(n) * exp_upper(t * Decimal(u) / 100) / Decimal(fs_denominator)
                     for u, n in fs_counts.items()), Decimal(0))
        triggered_mgf = Decimal(0)
        for sc, spins in c.FREE_SPINS.items():
            x_mgf = sum((Decimal(int(hist["base"][u, sc])) * exp_upper(t * Decimal(int(u) + scatter_units(sc)) / 100) / Decimal(denominator)
                         for u in np.flatnonzero(hist["base"][:, sc])), Decimal(0))
            power = Decimal(1)
            for _ in range(spins): power *= z_mgf
            triggered_mgf += x_mgf * power
        for threshold in (1000, 5000):
            bound = exp_upper(-t * Decimal(threshold)) * triggered_mgf
            if threshold not in bounds or bound < Decimal(bounds[threshold]["probability_upper_bound"]):
                bounds[threshold] = {"t": str(t), "probability_upper_bound": str(bound),
                                     "one_million_round_union_bound": str(bound * Decimal(1_000_000))}

report = {"passed": True, "math_config_sha256": fingerprint,
          "histogram_total_natural_grids": denominator,
          "fresh_histogram_arrays_equal_previous": old_equal,
          "independent_natural_base_checks": natural_grids,
          "independent_natural_forced_free_spin_checks": natural_grids * 3,
          "untriggered_rounds_payout_hundredths_not_divisible_by_ten": {
              "count": untriggered_mass, "denominator": denominator,
              "probability_fraction": str(Fraction(untriggered_mass, denominator)),
              "probability": untriggered_mass / denominator,
              "first_examples_units_and_counts": sorted(untriggered_payout_counts.items())[:20],
              "note": "Exact lower bound for all paid rounds. Triggered final bonus distributions are not needed to prove the format conflict."},
          "independent_decimal_chernoff_probability_upper_bounds": bounds,
          "probability_bounds_precision": 60,
          "probability_bounds_rounding": "ROUND_CEILING, exp.next_plus"}
(OUTPUT / "extra_checks.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
