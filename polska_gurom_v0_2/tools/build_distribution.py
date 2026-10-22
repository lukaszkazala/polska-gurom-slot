"""Enumerate exact correlated (line award, original Scatter count) histograms.

Run from any directory: python tools/build_distribution.py [--output FILE.npz]
Requires NumPy. Uses config values; never calls the runtime game evaluator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from fractions import Fraction
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from polska_gurom import config as c
from tools.math_config import compute_config_fingerprint, math_config_payload

SCALE = c.PAYOUT_SCALE
SYMBOL_IDS = {s: i for i, s in enumerate(c.SYMBOLS)}
WILD = SYMBOL_IDS[c.WILD]
SCATTER = SYMBOL_IDS[c.SCATTER]
LINES = np.asarray(c.PAYLINES, dtype=np.uint8)
SYMBOL_BASE = len(c.SYMBOLS)
MAX_LINE_UNITS = len(LINES) * max(v for row in c.PAYTABLE_UNITS.values() for v in row.values())


def make_windows():
    return [np.array([[SYMBOL_IDS[strip[(st + row) % len(strip)]] for row in range(c.ROWS)] for st in range(len(strip))], dtype=np.uint8) for strip in c.REEL_STRIPS]


def scalar_line_units(symbols):
    """Independent scalar scoring oracle, with no runtime-game imports."""
    awards = []
    for target in c.REGULAR_SYMBOLS:
        n = 0
        for symbol in symbols:
            if symbol not in (target, c.WILD):
                break
            n += 1
        awards.append(c.PAYTABLE_UNITS[target].get(n, 0))
    return max(awards, default=0)


def scalar_grid_units(grid, forced=None):
    scatter_count = sum(s == c.SCATTER for row in grid for s in row)
    line_units = sum(scalar_line_units([c.WILD if reel == forced else grid[line[reel]][reel] for reel in range(c.REELS)]) for line in c.PAYLINES)
    scatter_units = c.SCATTER_PAYTABLE_UNITS.get(min(scatter_count, c.REELS), 0)
    return line_units, scatter_units, scatter_count


def make_lut():
    codes = np.arange(SYMBOL_BASE ** c.REELS, dtype=np.int32)
    digits = np.stack([(codes // (SYMBOL_BASE ** p)) % SYMBOL_BASE for p in range(c.REELS - 1, -1, -1)], axis=1)
    lut = np.zeros(len(codes), dtype=np.int32)
    for target, wins in c.PAYTABLE_UNITS.items():
        compatible = (digits == SYMBOL_IDS[target]) | (digits == WILD)
        lengths = np.cumprod(compatible, axis=1).sum(axis=1)
        for n, award in wins.items():
            idx = lengths == n
            lut[idx] = np.maximum(lut[idx], award)
    for code in np.random.default_rng(71932).choice(len(codes), min(1000, len(codes)), replace=False):
        assert lut[code] == scalar_line_units([c.SYMBOLS[i] for i in digits[code]])
    return lut


def all_stops(reels):
    shape = tuple(len(c.REEL_STRIPS[r]) for r in reels)
    compact = np.indices(shape, dtype=np.int32).reshape(len(reels), -1).T
    stops = np.zeros((len(compact), c.REELS), dtype=np.int32)
    stops[:, reels] = compact
    return stops


def evaluate_stops(stops, windows, lut, forced=None):
    max_scatter_count = sum(int((w == SCATTER).sum(axis=1).max()) for w in windows)
    scatter_bins = max_scatter_count + 1
    n = len(stops)
    lp = np.zeros(n, dtype=np.int32)
    sc = np.zeros(n, dtype=np.int32)
    for reel in range(c.REELS):
        if reel != forced:
            sc += (windows[reel][stops[:, reel]] == SCATTER).sum(axis=1).astype(np.int32)
    for line in LINES:
        code = np.zeros(n, dtype=np.int32)
        for reel in range(c.REELS):
            code *= SYMBOL_BASE
            code += WILD if reel == forced else windows[reel][stops[:, reel], line[reel]]
        lp += lut[code]
    hist = np.bincount(lp * scatter_bins + sc, minlength=(MAX_LINE_UNITS + 1) * scatter_bins).reshape(MAX_LINE_UNITS + 1, scatter_bins)
    if forced is not None:
        omitted_sc_counts = np.bincount((windows[forced] == SCATTER).sum(axis=1))
        expanded = np.zeros_like(hist)
        for extra_sc, weight in enumerate(omitted_sc_counts):
            if weight:
                expanded[:, extra_sc:] += hist[:, :scatter_bins - extra_sc] * weight
        hist = expanded
    return hist


def stats(hist, denominator):
    lu, sc = np.nonzero(hist)
    weights = hist[lu, sc]
    su = np.array([c.SCATTER_PAYTABLE_UNITS.get(min(int(n), c.REELS), 0) for n in sc], dtype=np.int64)
    pay = lu + su
    assert int(hist.sum()) == denominator
    n1 = sum(int(w) * int(v) for w, v in zip(weights, pay))
    n2 = sum(int(w) * int(v) ** 2 for w, v in zip(weights, pay))
    line_n1 = sum(int(w) * int(v) for w, v in zip(weights, lu))
    mean = Fraction(n1, denominator * SCALE)
    e2 = Fraction(n2, denominator * SCALE ** 2)
    variance = e2 - mean * mean
    positive = int(weights[pay > 0].sum())
    net = int(weights[pay > SCALE].sum())
    even = int(weights[pay == SCALE].sum())
    return {
        "denominator": denominator, "payout_unit": f"1/{SCALE} total bet",
        "mean": float(mean), "mean_fraction": str(mean),
        "second_raw_moment": float(e2), "variance": float(variance),
        "std_dev": float(variance) ** 0.5,
        "positive_frequency": positive / denominator,
        "positive_frequency_fraction": str(Fraction(positive, denominator)),
        "net_profit_frequency": net / denominator,
        "break_even_frequency": even / denominator,
        "loss_disguised_as_win_frequency": (positive - net - even) / denominator,
        "maximum": int(pay.max()) / SCALE,
        "maximum_by_scatter_count": {str(k): int(pay[sc == k].max()) / SCALE if np.any(sc == k) else None for k in range(hist.shape[1])},
        "line_maximum_by_scatter_count": {str(k): int(lu[sc == k].max()) / SCALE if np.any(sc == k) else None for k in range(hist.shape[1])},
        "scatter_counts": hist.sum(axis=0).tolist(),
        "line_mean": float(Fraction(line_n1, denominator * SCALE)),
        "payout_mass": len(weights),
    }


def save_artifacts(histograms, output, elapsed_seconds=None, provenance="complete_reel_window_enumeration"):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    denominator = math.prod(map(len, c.REEL_STRIPS))
    fingerprint = compute_config_fingerprint(c)
    np.savez_compressed(output, **histograms, __math_config_sha256__=np.array(fingerprint), __format_version__=np.array(1))
    summary = {key: stats(hist, denominator * (12 if key == "fs_mixture_25pct" else 1)) for key, hist in histograms.items()}
    summary["metadata"] = {
        "math_config_sha256": fingerprint,
        "counts_npz_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "math_configuration": math_config_payload(c),
        "histogram_axes": f"[line payout in units of 1/{SCALE} total bet, original scatter count]",
        "free_spin_line_multiplier_applied_to_counts": False,
        "free_spin_line_multiplier": c.FS_LINE_MULTIPLIER,
        "histogram_keys": list(histograms),
        "provenance": provenance,
        "elapsed_seconds": elapsed_seconds,
    }
    summary_path = output.parent / "distribution_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", "--outfile", type=Path, default=PROJECT_ROOT / "verification" / "joint_counts.npz")
    args = parser.parse_args(argv)
    start = time.monotonic()
    windows, lut = make_windows(), make_lut()
    suffixes = all_stops(list(range(1, c.REELS)))
    hist = None
    for stop in range(len(c.REEL_STRIPS[0])):
        suffixes[:, 0] = stop
        batch = evaluate_stops(suffixes, windows, lut)
        hist = batch if hist is None else hist + batch
        print(f"base {stop + 1}/{len(c.REEL_STRIPS[0])}: {time.monotonic() - start:.1f}s", flush=True)
    histograms = {"base": hist}
    for reel in c.EXPANDING_REELS:
        stops = all_stops([r for r in range(c.REELS) if r != reel])
        histograms[f"forced_{reel}"] = evaluate_stops(stops, windows, lut, forced=reel)
        print(f"forced reel {reel}: {time.monotonic() - start:.1f}s", flush=True)
    save_artifacts(histograms, args.output, time.monotonic() - start)
    print(f"Saved {args.output}", flush=True)


if __name__ == "__main__":
    main()
