"""Legacy initial-window helpers; no RTP model for the cascade prototype."""
from __future__ import annotations
from collections import Counter
from fractions import Fraction
from itertools import product
from . import config as c


def _independent_award_units(sequence) -> int:
    awards = [0]
    for start in range(len(sequence) - 2):
        possible = set(c.REGULAR_SYMBOLS)
        for length, symbol in enumerate(sequence[start:], start=1):
            if symbol != c.WILD:
                possible.intersection_update((symbol,))
            if not possible:
                break
            if length >= 3:
                awards.extend(c.PAYTABLE_UNITS[s][length] for s in possible)
    return max(awards)


def symbol_probabilities():
    return [{s: strip.count(s) / len(strip) for s in c.SYMBOLS} for strip in c.REEL_STRIPS]


def expected_line_payout_fraction(forced_wild_reel: int | None = None) -> Fraction:
    if forced_wild_reel is not None and forced_wild_reel not in c.EXPANDING_REELS:
        raise ValueError("Only configured expanding reels are supported")
    counts = [Counter(strip) for strip in c.REEL_STRIPS]
    pools = [[c.WILD] if i == forced_wild_reel else c.SYMBOLS for i in range(c.REELS)]
    numerator = 0
    denominator = c.PAYOUT_SCALE
    for i, strip in enumerate(c.REEL_STRIPS):
        if i != forced_wild_reel:
            denominator *= len(strip)
    for sequence in product(*pools):
        ways = 1
        for reel, symbol in enumerate(sequence):
            if reel != forced_wild_reel:
                ways *= counts[reel][symbol]
        numerator += ways * _independent_award_units(sequence)
    return Fraction(numerator, denominator)


def expected_line_payout(forced_wild_reel: int | None = None) -> float:
    return float(expected_line_payout_fraction(forced_wild_reel))


def scatter_distribution_fraction() -> dict[int, Fraction]:
    dist = {0: Fraction(1)}
    for strip in c.REEL_STRIPS:
        counts = Counter(sum(strip[(stop + row) % len(strip)] == c.SCATTER for row in range(c.ROWS))
                         for stop in range(len(strip)))
        nxt = Counter()
        for a, pa in dist.items():
            for b, ways in counts.items():
                nxt[a+b] += pa * Fraction(ways, len(strip))
        dist = dict(nxt)
    return dist


def scatter_distribution() -> dict[int, float]:
    return {k: float(v) for k, v in scatter_distribution_fraction().items()}


def exact_first_moments() -> dict[str, Fraction]:
    if c.MATH_ASSUMPTIONS.get("falling_cascades_enabled"):
        raise ValueError("The v0.2 first-moment model does not include falling cascades")
    if not all(c.MATH_ASSUMPTIONS[k] for k in (
        "uniform_independent_reel_stops", "expansion_independent_of_grid",
        "uniform_expanding_reel_choice", "free_spins_independent",
        "scatter_evaluated_before_expansion")) or c.MATH_ASSUMPTIONS["retriggers_enabled"]:
        raise ValueError("Configuration does not satisfy the supported first-moment model")
    p = Fraction(c.EXPANDING_WILD_NUMERATOR, c.EXPANDING_WILD_DENOMINATOR)
    sd = scatter_distribution_fraction()
    lines = len(c.PAYLINES) * expected_line_payout_fraction()
    expanded = sum((len(c.PAYLINES) * expected_line_payout_fraction(r)
                    for r in c.EXPANDING_REELS), Fraction()) / len(c.EXPANDING_REELS)
    scatter = sum((prob * Fraction(c.SCATTER_PAYTABLE_UNITS.get(min(k, 5), 0), c.PAYOUT_SCALE)
                   for k, prob in sd.items() if k >= 3), Fraction())
    q = sum((prob for k, prob in sd.items() if c.FREE_SPINS.get(min(k, 5), 0)), Fraction())
    n_fs = sum((prob * c.FREE_SPINS.get(min(k, 5), 0) for k, prob in sd.items()), Fraction())
    fs = c.FS_LINE_MULTIPLIER * ((1-p)*lines + p*expanded) + scatter
    base, bonus = lines + scatter, n_fs * fs
    return {"base_line_rtp": lines, "scatter_rtp": scatter, "base_rtp": base,
            "expanded_line_rtp_before_multiplier": expanded, "free_spin_ev": fs,
            "bonus_rtp_uncapped": bonus, "total_rtp_uncapped": base + bonus,
            "bonus_frequency": q, "average_free_spins_per_trigger": n_fs/q,
            "average_bonus_payout": bonus/q, "expansion_probability": p}


def theoretical_metrics() -> dict:
    if c.MATH_ASSUMPTIONS.get("selection") == "integer_weighted_complete_round_books":
        from fractions import Fraction
        from .selection import load_distribution
        manifest, cdf, payouts = load_distribution()
        weights = [right-left for left,right in zip([0]+cdf[:-1], cdf)]
        total = manifest["total_weight"]
        mean = Fraction(sum(w*p for w,p in zip(weights,payouts)), total*c.PAYOUT_SCALE)
        return {"status": "exact", "model_version": c.MATH_VERSION, "rtp": float(mean),
                "rtp_fraction": str(mean), "book_count": len(weights), "total_weight": total,
                "max_win_one_in": total/sum(w for w,p in zip(weights,payouts) if p==c.MAX_WIN_UNITS),
                "scope": "Published finite complete-round weighted distribution, including cascades and bonuses"}
    if c.MATH_ASSUMPTIONS.get("falling_cascades_enabled"):
        return {
            "status": "unavailable",
            "model_version": "0.3.0-prototype",
            "scope": "Falling cascades change payout probabilities. The previous v0.2 RTP model does not apply; the new model requires separate validation.",
        }
    fractions = exact_first_moments()
    return {**{key: float(value) for key, value in fractions.items()},
            "exact_fractions": {key: str(value) for key, value in fractions.items()},
            "scatter_distribution": scatter_distribution(),
            "scope": "Exact uncapped first moments. The capped RTP interval, full variance and frequencies are in verification/math_validation.json; regenerate it after every configuration change."}
