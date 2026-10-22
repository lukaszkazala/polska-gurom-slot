"""Independent Monte Carlo model using exhaustive histograms, not game code."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from polska_gurom import config as c
from tools.verify_math import load_histograms, validate_config


def wilson(successes, n):
    p, z = successes / n, 1.96
    center = (p + z*z/(2*n))/(1+z*z/n)
    width = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return [center-width, center+width]


def simulate(n, seed, input_path, batch_size=250000):
    validate_config()
    if n <= 0 or batch_size <= 0:
        raise ValueError("Round count and batch size must be positive")
    histograms, denominator, fingerprint = load_histograms(input_path)
    rng = np.random.default_rng(seed)
    sparse = {}
    for key, histogram in histograms.items():
        line, sc = np.nonzero(histogram)
        sparse[key] = (line.astype(np.int64), sc, np.cumsum(histogram[line, sc], dtype=np.int64))

    def draw(key, size, multiplier):
        line, scatter, cumulative = sparse[key]
        ix = np.searchsorted(cumulative, rng.integers(denominator, size=size, dtype=np.int64), side="right")
        sc = scatter[ix]
        scatter_pay = np.array([c.SCATTER_PAYTABLE_UNITS.get(min(int(k), 5), 0) for k in sc], dtype=np.int64)
        return multiplier * line[ix] + scatter_pay, sc

    sums = dict(total=0, square=0, base=0, bonus=0, hit=0, profit=0, partial=0,
                even=0, triggers=0, free_spins=0, expansions=0, cap_hits=0)
    max_payout = max_raw = 0
    scale = c.PAYOUT_SCALE
    for start in range(0, n, batch_size):
        size = min(batch_size, n-start)
        base, sc = draw("base", size, 1)
        fs_count = np.array([c.FREE_SPINS.get(min(int(k), 5), 0) for k in sc], dtype=np.int64)
        triggered_indices = np.flatnonzero(fs_count)
        owner = np.repeat(triggered_indices, fs_count[triggered_indices])
        bonus = np.zeros(size, dtype=np.int64)
        if len(owner):
            expanded = rng.integers(c.EXPANDING_WILD_DENOMINATOR, size=len(owner)) < c.EXPANDING_WILD_NUMERATOR
            picks = rng.integers(len(c.EXPANDING_REELS), size=len(owner))
            fs = np.zeros(len(owner), dtype=np.int64)
            ordinary = np.flatnonzero(~expanded)
            fs[ordinary], _ = draw("base", len(ordinary), c.FS_LINE_MULTIPLIER)
            for i, reel in enumerate(c.EXPANDING_REELS):
                indices = np.flatnonzero(expanded & (picks == i))
                fs[indices], _ = draw(f"forced_{reel}", len(indices), c.FS_LINE_MULTIPLIER)
            np.add.at(bonus, owner, fs)
            sums["expansions"] += int(expanded.sum())
        raw = base + bonus
        paid = np.minimum(raw, c.MAX_WIN_UNITS)
        sums["total"] += int(paid.sum(dtype=np.int64))
        sums["square"] += int(np.sum(paid*paid, dtype=np.int64))
        sums["base"] += int(base.sum(dtype=np.int64))
        sums["bonus"] += int((paid-base).sum(dtype=np.int64))
        sums["hit"] += int(np.count_nonzero(paid > 0))
        sums["profit"] += int(np.count_nonzero(paid > scale))
        sums["partial"] += int(np.count_nonzero((paid > 0) & (paid < scale)))
        sums["even"] += int(np.count_nonzero(paid == scale))
        sums["triggers"] += len(triggered_indices)
        sums["free_spins"] += len(owner)
        sums["cap_hits"] += int(np.count_nonzero(raw > c.MAX_WIN_UNITS))
        max_payout = max(max_payout, int(paid.max()))
        max_raw = max(max_raw, int(raw.max()))
    mean = sums["total"]/(n*scale)
    variance = (sums["square"]*n-sums["total"]**2)/(n*n*scale**2)
    sd = math.sqrt(variance)
    width = 1.96*sd/math.sqrt(n)
    return {
        "method": "Independent histogram Monte Carlo; integer inverse-CDF samples of exhaustive windows. Not the game engine implementation.",
        "math_config_sha256": fingerprint, "rounds": n, "seed": seed,
        "rtp": mean, "rtp_95_percent_normal_interval": [mean-width, mean+width],
        "base_rtp": sums["base"]/(n*scale), "bonus_rtp": sums["bonus"]/(n*scale),
        "variance": variance, "std_dev": sd,
        "hit_frequency": sums["hit"]/n, "hit_frequency_95_wilson_interval": wilson(sums["hit"],n),
        "net_profit_frequency": sums["profit"]/n, "net_profit_95_wilson_interval": wilson(sums["profit"],n),
        "positive_below_bet_frequency": sums["partial"]/n, "break_even_frequency": sums["even"]/n,
        "bonus_frequency": sums["triggers"]/n, "bonus_frequency_95_wilson_interval": wilson(sums["triggers"],n),
        "mean_bonus_given_trigger": sums["bonus"]/(sums["triggers"]*scale) if sums["triggers"] else 0,
        "free_spins": sums["free_spins"], "expansions": sums["expansions"],
        "cap_hits": sums["cap_hits"], "max_observed_payout": max_payout/scale,
        "max_observed_before_cap": max_raw/scale,
        "confidence_interval_note": "Normal RTP interval from empirical variance; Wilson intervals for binary events. Exact moments and cap bounds are checked separately.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=10000000)
    parser.add_argument("--seed", type=int, default=20261018)
    parser.add_argument("--input", type=Path, default=ROOT/"verification"/"joint_counts.npz")
    parser.add_argument("--output", type=Path, default=ROOT/"verification"/"simulation_distribution_10m.json")
    args = parser.parse_args()
    report = simulate(args.rounds, args.seed, args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
