"""Exact correlated payout distributions for the 20-line v0.2 research layout.

Reads the v0.1 reference; never changes it. All counts enumerate real reel
windows, including their row correlations. Payout units are 1/100 total bet.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from fractions import Fraction
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REFERENCE = Path(r"D:\Kazaluka_slots\polska_gurom_phase2_v0.1")
sys.path.insert(0, str(REFERENCE))
from polska_gurom import config as c
from polska_gurom.game import _line_best_win

UNITS_PER_BET = 100
PAYTABLE = {s: dict(wins) for s, wins in c.PAYTABLE.items()}
PAYTABLE["L1"][3] = 0.16
SYMBOL_IDS = {s: i for i, s in enumerate(c.SYMBOLS)}
WILD = SYMBOL_IDS[c.WILD]
SCATTER = SYMBOL_IDS[c.SCATTER]
LINES = np.array(json.loads((HERE.parent / "paylines_variants" / "comparison_results.json").read_text())["nine_prefixes_with_v_twenty"]["lines"], dtype=np.uint8)
assert LINES.shape == (20, 5)
assert len(set(map(tuple, LINES.tolist()))) == 20
MAX_LINE_UNITS = 20 * max(round(v * UNITS_PER_BET) for wins in PAYTABLE.values() for v in wins.values())
HIST_SIZE = (MAX_LINE_UNITS + 1) * 6


def make_lut():
    codes = np.arange(100_000, dtype=np.int32)
    digits = np.stack([(codes // (10 ** p)) % 10 for p in range(4, -1, -1)], axis=1)
    lut = np.zeros(len(codes), dtype=np.int16)
    for target, wins in PAYTABLE.items():
        compatible = (digits == SYMBOL_IDS[target]) | (digits == WILD)
        lengths = np.cumprod(compatible, axis=1).sum(axis=1)
        for n, award in wins.items():
            idx = lengths == n
            lut[idx] = np.maximum(lut[idx], round(award * UNITS_PER_BET))
    # Independent reference evaluation, with fixed deterministic sampling.
    for code in np.random.default_rng(71932).choice(100_000, 1000, replace=False):
        syms = [c.SYMBOLS[i] for i in digits[code]]
        expected = 0.0
        for target, wins in PAYTABLE.items():
            n = 0
            for symbol in syms:
                if symbol not in (target, c.WILD):
                    break
                n += 1
            if n >= 3:
                expected = max(expected, wins[n])
        assert lut[code] == round(expected * UNITS_PER_BET)
    return lut


def make_windows():
    return [np.array([[SYMBOL_IDS[strip[(st + row) % len(strip)]] for row in range(3)] for st in range(len(strip))], dtype=np.uint8) for strip in c.REEL_STRIPS]


def evaluate_stops(stops, windows, lut, forced=None):
    n = len(stops)
    lp = np.zeros(n, dtype=np.int32)
    sc = np.zeros(n, dtype=np.uint8)
    for reel in range(5):
        if reel != forced:
            sc += (windows[reel][stops[:, reel]] == SCATTER).sum(axis=1).astype(np.uint8)
    for line in LINES:
        code = np.zeros(n, dtype=np.int32)
        for reel in range(5):
            code *= 10
            if reel == forced:
                code += WILD
            else:
                code += windows[reel][stops[:, reel], line[reel]]
        lp += lut[code]
    keys = lp * 6 + sc
    hist = np.bincount(keys, minlength=HIST_SIZE).reshape(MAX_LINE_UNITS + 1, 6)
    if forced is not None:
        # Omitted original reel remains relevant for Scatter. Three of its 36
        # windows contain the one Scatter, independent of all other reels.
        expanded = hist * 33
        expanded[:, 1:] += hist[:, :-1] * 3
        hist = expanded
    return hist


def all_stops(reels):
    shape = tuple(len(c.REEL_STRIPS[r]) for r in reels)
    compact = np.indices(shape, dtype=np.uint8).reshape(len(reels), -1).T
    stops = np.zeros((len(compact), 5), dtype=np.uint8)
    stops[:, reels] = compact
    return stops


def stats(hist, denominator):
    line_units = np.arange(len(hist), dtype=np.int64)[:, None]
    sc_units = np.array([0, 0, 0, 100, 500, 2000], dtype=np.int64)[None, :]
    payouts = line_units + sc_units
    total = int(hist.sum())
    assert total == denominator
    n1 = int(np.sum(hist * payouts, dtype=np.int64))
    # Largest possible first and second moment products fit int64 here.
    n2 = int(np.sum(hist * payouts * payouts, dtype=np.int64))
    mean = Fraction(n1, denominator * UNITS_PER_BET)
    e2 = Fraction(n2, denominator * UNITS_PER_BET ** 2)
    variance = e2 - mean * mean
    positive = int(hist[payouts > 0].sum())
    net = int(hist[payouts > UNITS_PER_BET].sum())
    even = int(hist[payouts == UNITS_PER_BET].sum())
    return {
        "denominator": denominator,
        "payout_unit": "1/100 total bet",
        "mean": float(mean), "mean_fraction": str(mean),
        "second_raw_moment": float(e2), "variance": float(variance),
        "std_dev": float(variance) ** 0.5,
        "positive_frequency": positive / denominator,
        "positive_frequency_fraction": str(Fraction(positive, denominator)),
        "net_profit_frequency": net / denominator,
        "break_even_frequency": even / denominator,
        "loss_disguised_as_win_frequency": (positive - net - even) / denominator,
        "maximum": float(payouts[hist > 0].max()) / UNITS_PER_BET,
        "maximum_by_scatter_count": {
            str(sc): float(payouts[:, sc][hist[:, sc] > 0].max()) / UNITS_PER_BET
            if np.any(hist[:, sc]) else None for sc in range(6)
        },
        "line_maximum_by_scatter_count": {
            str(sc): float(np.where(hist[:, sc] > 0)[0].max()) / UNITS_PER_BET
            if np.any(hist[:, sc]) else None for sc in range(6)
        },
        "scatter_counts": hist.sum(axis=0).tolist(),
        "line_mean": float(np.sum(hist * line_units)) / denominator / UNITS_PER_BET,
        "payout_mass": int(np.count_nonzero(hist)),
    }


def main():
    start = time.monotonic()
    lut = make_lut()
    windows = make_windows()
    histograms = {}
    denominator = 36 ** 5
    suffixes = all_stops([1, 2, 3, 4])
    hist = np.zeros((MAX_LINE_UNITS + 1, 6), dtype=np.int64)
    for stop in range(36):
        suffixes[:, 0] = stop
        hist += evaluate_stops(suffixes, windows, lut)
        print(f"base {stop + 1}/36: {time.monotonic() - start:.1f}s", flush=True)
    histograms["base"] = hist
    del suffixes
    for reel in (1, 2, 3):
        stops = all_stops([r for r in range(5) if r != reel])
        histograms[f"forced_{reel}"] = evaluate_stops(stops, windows, lut, forced=reel)
        print(f"forced reel {reel}: {time.monotonic() - start:.1f}s", flush=True)
    histograms["fs_mixture_25pct"] = histograms["base"] * 9 + sum(histograms[f"forced_{r}"] for r in (1, 2, 3))
    from math import comb
    expected_scatter_counts = np.array([comb(5, k) * 3 ** k * 33 ** (5 - k) for k in range(6)])
    for key, hist in histograms.items():
        assert np.array_equal(hist.sum(axis=0), expected_scatter_counts * (12 if key == "fs_mixture_25pct" else 1))
    np.savez_compressed(HERE / "joint_counts.npz", **histograms)
    summary = {key: stats(hist, denominator * (12 if key == "fs_mixture_25pct" else 1)) for key, hist in histograms.items()}
    assert abs(summary["base"]["line_mean"] - 0.7292096063756373) < 1e-12
    assert abs(summary["base"]["positive_frequency"] - 0.2970869532083524) < 1e-15
    summary["metadata"] = {
        "reference": str(REFERENCE),
        "reference_config_sha256": hashlib.sha256((REFERENCE / "polska_gurom" / "config.py").read_bytes()).hexdigest(),
        "lines": LINES.tolist(),
        "histogram_axes": "[line payout in units of 1/100 total bet, original scatter count]",
        "forced_histogram_counting": "Enumerated remaining 36^4 stops; omitted reel weights 33 no-scatter, 3 one-scatter.",
        "mixture_counting": "(9*base+forced_1+forced_2+forced_3)/(12*36^5)",
        "elapsed_seconds": time.monotonic() - start,
        "paytable": PAYTABLE,
    }
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
