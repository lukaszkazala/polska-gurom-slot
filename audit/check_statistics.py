"""Check bucket boundaries against exact integer multiplier units."""
from __future__ import annotations
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import random
import sys

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Kazaluka_slots\polska_gurom_phase2_v0.1")
sys.path.insert(0, str(ROOT))
from polska_gurom.config import PAYLINES, PAYTABLE, SCATTER_PAYTABLE, REGULAR_SYMBOLS, MAX_WIN
from polska_gurom.game import generate_grid, evaluate_paid_spin, evaluate_free_spin
from polska_gurom.sim import _bucket, simulate
from polska_gurom.theory import theoretical_metrics

TABLE = {s: {n: int(Decimal(str(x))*100) for n, x in prizes.items()}
         for s, prizes in PAYTABLE.items()}
SCATTER_TABLE = {n: int(Decimal(str(x))*100) for n, x in SCATTER_PAYTABLE.items()}


def integer_grid_payout(grid, expansion=None):
    scatter_count = sum(s == "SCATTER" for row in grid for s in row)
    result = SCATTER_TABLE.get(min(scatter_count, 5), 0)
    for line in PAYLINES:
        seq = ["WILD" if r == expansion else grid[line[r]][r] for r in range(5)]
        candidates = []
        for target in REGULAR_SYMBOLS:
            n = 0
            for s in seq:
                if s not in (target, "WILD"):
                    break
                n += 1
            candidates.append(TABLE[target].get(n, 0))
        result += max(candidates)
    return result


def integer_bucket(x):
    if x == 0:
        return "0x"
    for upper, label in [(100, ">0x-1x"), (500, "1x-5x"), (2000, "5x-20x"),
                         (10000, "20x-100x"), (50000, "100x-500x"),
                         (100000, "500x-1000x"), (500000, "1000x+")]:
        if x < upper:
            return label
    return "5000x Max Win"


rng = random.Random(20261015)
float_counts, exact_counts = Counter(), Counter()
examples = []
payout_mismatches = 0
n = 100_000
for i in range(n):
    grid = generate_grid(rng)
    base = evaluate_paid_spin(grid)
    integer_total = integer_grid_payout(grid)
    float_bonus = 0.0
    for _ in range(base.free_spins_awarded):
        free_grid = generate_grid(rng)
        fs = evaluate_free_spin(free_grid, rng)
        integer_total += integer_grid_payout(free_grid, fs.expanding_reel)
        float_bonus += fs.payout
    float_total = min(base.payout + float_bonus, MAX_WIN)
    integer_total = min(integer_total, int(MAX_WIN*100))
    if round(float_total*100) != integer_total:
        payout_mismatches += 1
    float_label, exact_label = _bucket(float_total), integer_bucket(integer_total)
    float_counts[float_label] += 1
    exact_counts[exact_label] += 1
    if float_label != exact_label and len(examples) < 5:
        examples.append({"round_index_1_based": i+1, "grid": grid,
                         "free_spins_awarded": base.free_spins_awarded,
                         "float_payout": float_total, "exact_payout": integer_total/100,
                         "actual_bucket": float_label, "correct_bucket": exact_label})

result = {"spins": n, "seed": 20261015, "float_buckets": dict(float_counts),
          "exact_buckets": dict(exact_counts), "examples": examples,
          "payout_mismatches_at_cent_precision": payout_mismatches,
          "wrong_bucket_count": sum(max(0, float_counts[k]-exact_counts[k]) for k in float_counts)}
Path(__file__).with_name("statistics_audit.json").write_text(
    json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result), flush=True)

invalid = {}
for p in [-0.5, 1.5]:
    theoretical = theoretical_metrics(p)["total_rtp"]
    empirical = simulate(10_000, seed=20261015, expansion_probability=p)["rtp"]
    invalid[str(p)] = {"theory": theoretical, "simulation_10k": empirical}
Path(__file__).with_name("invalid_probability_audit.json").write_text(
    json.dumps(invalid, indent=2), encoding="utf-8")
print("Invalid probabilities accepted:", json.dumps(invalid), flush=True)
