"""Monte Carlo validation through the actual game and its integer settlement."""
from __future__ import annotations
from collections import Counter
import math
import random
from .config import PAYOUT_SCALE, MAX_WIN_UNITS, WILD, SCATTER
from .game import play_round


def _bucket(units: int) -> str:
    x = units / PAYOUT_SCALE
    if x == 0: return "0x"
    if x < 1: return ">0x-1x"
    if x < 5: return "1x-5x"
    if x < 20: return "5x-20x"
    if x < 100: return "20x-100x"
    if x < 500: return "100x-500x"
    if x < 1000: return "500x-1000x"
    if units < MAX_WIN_UNITS: return "1000x+"
    return "5000x Max Win"


def simulate(n: int, seed: int = 20261018,
             expansion_probability: float | None = None) -> dict:
    if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
        raise ValueError("Number of paid rounds must be a positive integer")
    rng = random.Random(seed)
    total = squares = base_sum = bonus_sum = 0
    hit = profit = partial = break_even = bonus_count = free_count = expansions = 0
    cap_hits = max_units = wild_cells = scatter_cells = 0
    scatter_dist, buckets = Counter(), Counter()
    for _ in range(n):
        result = play_round(rng, expansion_probability)
        units = result.payout_units
        assert units == result.base.payout_units + sum(result.free_spin_credits)
        assert 0 <= units <= MAX_WIN_UNITS
        total += units
        squares += units * units
        base_sum += result.base.payout_units
        bonus_sum += result.bonus_payout_units
        hit += units > 0
        profit += units > PAYOUT_SCALE
        partial += 0 < units < PAYOUT_SCALE
        break_even += units == PAYOUT_SCALE
        bonus_count += result.base.bonus_triggered
        free_count += len(result.free_spins)
        expansions += result.expansions
        cap_hits += result.cap_reduction_units > 0
        max_units = max(max_units, units)
        wild_cells += sum(s == WILD for row in result.base.grid for s in row)
        scatter_cells += result.base.scatter_count
        scatter_dist[result.base.scatter_count] += 1
        buckets[_bucket(units)] += 1
    mean = total / (n * PAYOUT_SCALE)
    variance = (squares * n - total * total) / (n * n * PAYOUT_SCALE**2)
    sd = math.sqrt(variance)
    half_width = 1.96 * sd / math.sqrt(n)
    return {
        "method": "actual game.play_round, rational expansion draw, integer settlement",
        "seed": seed, "spins": n, "rtp": mean,
        "rtp_95_percent_normal_interval": [mean - half_width, mean + half_width],
        "base_rtp": base_sum / (n * PAYOUT_SCALE),
        "bonus_rtp": bonus_sum / (n * PAYOUT_SCALE),
        "hit_frequency": hit / n, "net_profit_frequency": profit / n,
        "positive_below_bet_frequency": partial / n,
        "break_even_frequency": break_even / n,
        "bonus_frequency": bonus_count / n,
        "average_bonus_payout": bonus_sum / (bonus_count * PAYOUT_SCALE) if bonus_count else 0.0,
        "variance": variance, "std_dev": sd,
        "max_observed_win": max_units / PAYOUT_SCALE,
        "rounds_reduced_by_cap": cap_hits,
        "free_spins_played": free_count, "expanding_wild_events": expansions,
        "wild_cell_frequency": wild_cells / (15 * n),
        "scatter_cell_frequency": scatter_cells / (15 * n),
        "scatter_distribution": dict(sorted(scatter_dist.items())),
        "win_buckets": dict(buckets),
        "confidence_interval_note": "Empirical normal Monte Carlo interval; exact mathematics and tail bounds are verified separately.",
    }
