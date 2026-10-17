"""Exact pre-cap expectations for the natural cyclic-reel generator.

Linearity is used only for expectations. No independence between paylines is
assumed for hit frequency, variance or cap calculations.
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction
from itertools import product
from math import comb, prod

from .config import load_config
from .evaluator import evaluate_line

SYMBOL_ORDER = ("L1", "L2", "L3", "L4", "P1", "P2", "P3", "P4", "WILD", "SCATTER")


def exact_value(value: Fraction, unit: str = "TOTAL_BET") -> dict:
    value = Fraction(value)
    return {"fraction": str(value), "numerator": value.numerator,
            "denominator": value.denominator, "value": float(value), "unit": unit}


def scatter_distribution(cfg) -> tuple[Fraction, ...]:
    """Convolve empirical cyclic-window scatter counts, valid for multi-SC windows."""
    distribution = [Fraction(1)]
    for reel in cfg.reels:
        counts = Counter(sum(reel[(stop + row) % len(reel)] == "SCATTER"
                             for row in range(3)) for stop in range(len(reel)))
        out = [Fraction(0)] * (len(distribution) + max(counts))
        for before, probability in enumerate(distribution):
            for count, occurrences in counts.items():
                out[before + count] += probability * Fraction(occurrences, len(reel))
        distribution = out
    return tuple(distribution)


def exact_line_expectation_units(cfg, charge_reel: int | None = None) -> Fraction:
    """Enumerate every nonzero-probability symbol tuple, with integer weights."""
    counts = [Counter(reel) for reel in cfg.reels]
    if charge_reel is not None:
        counts[charge_reel] = Counter({"WILD": len(cfg.reels[charge_reel])})
    numerator = 0
    for entries in product(*(tuple(count.items()) for count in counts)):
        symbols = tuple(entry[0] for entry in entries)
        win = evaluate_line(symbols, cfg)
        if win is not None:
            numerator += win.payout_units * prod(entry[1] for entry in entries)
    return Fraction(numerator, prod(len(reel) for reel in cfg.reels))


def no_wild_substitution_line_expectation_units(cfg) -> Fraction:
    """Diagnostic only: natural WILD is a blocker, not a rules change."""
    counts = [Counter(reel) for reel in cfg.reels]
    total = Fraction(0)
    for symbol, pays in cfg.paytable.items():
        p = [Fraction(count[symbol],len(reel)) for count,reel in zip(counts,cfg.reels)]
        for length in (3,4,5):
            probability = prod(p[:length])
            if length < 5:
                probability *= 1-p[length]
            total += probability*pays[length]
    return total


def _convex_cap_loss_upper(cfg, scatter_probs, fs_mean: Fraction,
                          spin_upper: int) -> Fraction:
    """Rigorous stop-loss bound in units using bounded independent FS.

    For 0<=Y<=M with mean m, convexity gives Y <=cx M*Bernoulli(m/M).
    The positive-part payoff is convex in each independent FS. Replacing each
    FS in turn bounds expected cap loss; base payout is bounded by M.
    """
    p = fs_mean / spin_upper
    result = Fraction(0)
    for count, probability in enumerate(scatter_probs):
        spins = cfg.fs_awards.get(count, 0)
        if not spins:
            result += probability * max(spin_upper - cfg.cap_units, 0)
            continue
        conditional = sum((Fraction(comb(spins, successes)) * p ** successes
                           * (1-p) ** (spins-successes)
                           * max(spin_upper * (1+successes) - cfg.cap_units, 0)
                           for successes in range(spins+1)), Fraction(0))
        result += probability * conditional
    return result


def analyze(cfg=None) -> dict:
    cfg = cfg or load_config()
    scale = cfg.scale
    scatter_probs = scatter_distribution(cfg)
    scatter_mean = sum((p * cfg.scatter_pays.get(k, 0)
                        for k, p in enumerate(scatter_probs)), Fraction(0))
    no_charge_line = exact_line_expectation_units(cfg)
    charge_line = {index: exact_line_expectation_units(cfg, index) for index in (1, 2, 3)}
    weight_sum = sum(cfg.charge_weights)
    expanded_line = sum((charge_line[index] * Fraction(weight, weight_sum)
                         for index, weight in zip((1, 2, 3), cfg.charge_weights)), Fraction(0))
    line_count = len(cfg.paylines)
    base = no_charge_line * line_count + scatter_mean
    fs_without = base
    fs_with = expanded_line * line_count + scatter_mean
    fs_mean = fs_without + cfg.charge_probability * (fs_with-fs_without)
    bonus_probability = sum((p for count, p in enumerate(scatter_probs)
                             if cfg.fs_awards.get(count, 0)), Fraction(0))
    fs_per_round = sum((p * cfg.fs_awards.get(count, 0)
                       for count, p in enumerate(scatter_probs)), Fraction(0))
    fs_conditional = fs_per_round / bonus_probability if bonus_probability else Fraction(0)
    bonus = fs_per_round * fs_mean
    total = base + bonus
    spin_upper = line_count * max(max(row.values()) for row in cfg.paytable.values()) + max(cfg.scatter_pays.values(), default=0)
    round_upper = spin_upper * (1 + max(cfg.fs_awards.values(), default=0))
    cap_loss_upper = _convex_cap_loss_upper(cfg, scatter_probs, fs_mean, spin_upper)
    charge_slope = fs_per_round * (fs_with-fs_without)
    no_wild_base = no_wild_substitution_line_expectation_units(cfg)*line_count+scatter_mean
    required_charge = ((Fraction(96, 100)*scale - base - fs_per_round*fs_without)
                       / charge_slope if charge_slope else None)
    reels = []
    for index, reel in enumerate(cfg.reels):
        counts = Counter(reel)
        window_sc = Counter(sum(reel[(stop+row) % len(reel)] == "SCATTER" for row in range(3))
                            for stop in range(len(reel)))
        wild_windows = sum(any(reel[(stop+row) % len(reel)] == "WILD" for row in range(3))
                           for stop in range(len(reel)))
        reels.append({"reel_1_based": index+1, "length": len(reel), "ordered_strip": list(reel),
                      "counts": dict(counts),
                      "single_row_symbol_probabilities": {s: exact_value(Fraction(counts[s], len(reel)), "probability") for s in SYMBOL_ORDER},
                      "scatter_window_distribution": {str(k): exact_value(Fraction(v, len(reel)), "probability") for k,v in sorted(window_sc.items())},
                      "natural_wild_cell_probability": exact_value(Fraction(counts["WILD"], len(reel)), "probability"),
                      "natural_wild_window_probability": exact_value(Fraction(wild_windows, len(reel)), "probability")})
    sweep = []
    for probability in (Fraction(0), Fraction(1,4), Fraction(1,2), Fraction(3,4), Fraction(1)):
        fs = fs_without + probability*(fs_with-fs_without)
        sweep.append({"charge_probability": exact_value(probability, "probability"),
                      "rtp_pre_cap": exact_value((base+fs_per_round*fs)/scale),
                      "bonus_rtp_pre_cap": exact_value(fs_per_round*fs/scale)})
    return {
        "method": "EXACT", "scope": "Natural cyclic-reel generator; pre-cap expected values",
        "status": "PROTOTYPE / NOT MATH-FROZEN", "config_version": cfg.version,
        "config_hash": cfg.config_hash, "scale": scale,
        "reels": reels,
        "scatter_distribution": {str(k): exact_value(p, "probability") for k,p in enumerate(scatter_probs)},
        "trigger_distribution": {str(k): exact_value(scatter_probs[k] if k<len(scatter_probs) else Fraction(0), "probability") for k in (3,4,5)},
        "bonus_probability": exact_value(bonus_probability, "probability"),
        "bonus_mean_interval_paid_rounds": exact_value(1/bonus_probability, "paid_rounds") if bonus_probability else None,
        "mean_free_spins_given_bonus": exact_value(fs_conditional, "free_spins"),
        "mean_free_spins_per_paid_round": exact_value(fs_per_round, "free_spins/paid_round"),
        "required_mean_bonus_for_22_5pp": exact_value(Fraction(225,1000)/bonus_probability) if bonus_probability else None,
        "line_mean_no_charge": exact_value(no_charge_line/scale),
        "line_mean_charge_by_reel": {str(k+1): exact_value(value/scale) for k,value in charge_line.items()},
        "free_spin_mean_no_charge": exact_value(fs_without/scale),
        "free_spin_mean_conditional_charge": exact_value(fs_with/scale),
        "free_spin_mean": exact_value(fs_mean/scale),
        "charge_increment_per_free_spin": exact_value(cfg.charge_probability*(fs_with-fs_without)/scale),
        "mean_bonus_given_trigger_pre_cap": exact_value(fs_conditional*fs_mean/scale),
        "base_rtp_pre_cap": exact_value(base/scale),
        "bonus_rtp_pre_cap": exact_value(bonus/scale),
        "total_rtp_pre_cap": exact_value(total/scale),
        "scatter_rtp_pre_cap": exact_value(scatter_mean*(1+fs_per_round)/scale),
        "diagnostics_exact_pre_cap": {
            "note": "Counterfactual diagnostics only; no configuration changes and no inference about unavailable historical evaluator.",
            "base_rtp_natural_wilds_treated_as_blockers": exact_value(no_wild_base/scale),
            "base_rtp_increment_from_natural_wild_substitution": exact_value((base-no_wild_base)/scale),
            "bonus_rtp_without_scatter_payout_in_free_spins": exact_value(fs_per_round*(fs_mean-scatter_mean)/scale),
            "total_rtp_without_scatter_payout_in_free_spins": exact_value((total-fs_per_round*scatter_mean)/scale),
            "free_spin_scatter_rtp_contribution": exact_value(fs_per_round*scatter_mean/scale)},
        "charge_sweep_pre_cap": sweep,
        "charge_probability_required_for_96pct_pre_cap": exact_value(required_charge, "probability") if required_charge is not None else None,
        "cap": {"post_cap_exact_rtp_status": "EXACT" if cap_loss_upper==0 else "NOT CALCULATED",
                "method": "EXACT RIGOROUS BOUND: convex-order Bernoulli stop-loss domination; independent FS; same bounded payout and mean",
                "single_spin_payout_upper_bound": exact_value(Fraction(spin_upper,scale)),
                "round_payout_upper_bound": exact_value(Fraction(round_upper,scale)),
                "rtp_loss_upper_bound": exact_value(cap_loss_upper/scale),
                "post_cap_rtp_lower_bound": exact_value((total-cap_loss_upper)/scale),
                "post_cap_rtp_upper_bound": exact_value(total/scale),
                "base_rtp_post_cap": exact_value(base/scale) if spin_upper<=cfg.cap_units else None,
                "bonus_rtp_post_cap_lower_bound": exact_value((bonus-cap_loss_upper)/scale),
                "bonus_rtp_post_cap_upper_bound": exact_value(bonus/scale),
                "caveat": "Bounds are not exact post-cap RTP. The generic maximum is an upper bound, not an attainable maximum."},
        "not_calculated_exactly": ["hit frequency", "round variance", "round payout distribution", "post-cap exact RTP"],
        "historical_reported_unverified": {"total_rtp": .805417, "base_rtp": .744530, "bonus_rtp": .060887,
                                            "hit_frequency_1m": .496463, "bonus_interval": 196.55,
                                            "maximum_observed_1m": 130, "charge_probability": .25},
        "interpretation": "Agreement of pre-cap mean and bonus probability with historical rounded figures does not reconstruct historical reel order, evaluator implementation, hits, variance or tail."
    }
