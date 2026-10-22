"""Deterministic legal bonus draw candidates; this does not assign weights."""
from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import asdict
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "test-interface-any-start/engine"))
from polska_gurom import config
from polska_gurom.selection import BonusRecipeRandom, replay_spec

BASE_STOPS = {
    8: [35, 28, 17, 16, 31],
    10: [35, 28, 17, 16, 8],
    12: [35, 27, 22, 15, 8],
}


def candidates():
    for fs, base_stops in BASE_STOPS.items():
        for seed, expansion, shifts, limit in itertools.product(
                (20261022, 20261023), (None, 1, 2, 3),
                itertools.product((-2, -1, 0), repeat=2), range(51)):
            recipe = {
                "name": "bonus_wild_refill", "stops": base_stops,
                "free_spin_stops": [4, 33, 27, 21 + shifts[0], 13 + shifts[1]],
                "wild_refill_limit": limit, "expanding_reel": expansion,
                "fallback_seed": seed,
            }
            yield fs, {"recipe": recipe}


class LegalDrawAudit(BonusRecipeRandom):
    """Check the overridden RNG values at their actual consumption point."""
    def __init__(self, recipe):
        super().__init__(recipe)
        self.draw_count = 0

    def randrange(self, stop, *args):
        value = super().randrange(stop, *args)
        assert not args and type(value) is int and 0 <= value < stop
        self.draw_count += 1
        return value

    def choice(self, population):
        value = super().choice(population)
        assert value in population
        self.draw_count += 1
        return value


def compact_catalog(report):
    """Keep two meaningful neighboring payouts per band/FS, plus cap witnesses."""
    rows = report["candidates"]
    chosen = {}
    bands = []
    compact_gaps = {}

    def add(row):
        chosen[row["event_sha256"]] = row

    for fs in BASE_STOPS:
        pool = [row for row in rows if row["fs"] == fs]
        for lower in range(50000, 500000, 25000):
            upper = lower + 25000
            midpoint = (lower + upper) // 2
            available = [row for row in pool if lower <= row["payout_units"] < upper]
            assert available, (fs, lower)
            below = [row for row in available if row["payout_units"] < midpoint]
            above = [row for row in available if row["payout_units"] > midpoint]
            picks = []
            if below:
                picks.append(max(below, key=lambda row: row["payout_units"]))
            if above:
                picks.append(min(above, key=lambda row: row["payout_units"]))
            for row in picks:
                add(row)
            bands.append({"fs": fs, "lower_units": lower, "upper_units_exclusive": upper,
                          "candidate_count": len(available),
                          "min_units": min(row["payout_units"] for row in available),
                          "max_units": max(row["payout_units"] for row in available),
                          "selected_payout_units": [row["payout_units"] for row in picks]})
        caps = [row for row in pool if row["payout_units"] == config.MAX_WIN_UNITS and
                row["free_spins_played"] < fs and row["cap_reduction_units"] > 0]
        # Two different legal expansion reels for each declared FS award.
        for expansion in (1, 3):
            add(next(row for row in caps if row["spec"]["recipe"]["expanding_reel"] == expansion))
        while True:
            values = sorted({50000, 500000, *(row["payout_units"] for row in chosen.values()
                                             if row["fs"] == fs)})
            largest = max((b-a, a, b) for a,b in zip(values, values[1:]))
            if largest[0] <= 25000:
                break
            _, lower, upper = largest
            inside = [row for row in pool if lower < row["payout_units"] < upper]
            assert inside
            add(min(inside, key=lambda row: abs(2*row["payout_units"]-lower-upper)))
        compact_gaps[str(fs)] = largest[0]
    return {**report, "candidates": list(chosen.values()), "catalog_count": len(chosen),
            "band_summaries": bands, "catalog_largest_gaps_units": compact_gaps,
            "catalog_method": "Nearest payout below and above each 250x band midpoint, "
                              "two FS cap witnesses with different expansion reels, "
                              "then fill any remaining gap larger than 250x"}


def main():
    from polska_gurom import game
    started = time.perf_counter()
    seen, rows = set(), []
    pools = {fs: set() for fs in BASE_STOPS}
    caps = {fs: [] for fs in BASE_STOPS}
    draw_count = 0
    count = 0
    for fs, spec in candidates():
        count += 1
        rng = LegalDrawAudit(spec["recipe"])
        result = game.play_round(rng)
        draw_count += rng.draw_count
        assert result.base.free_spins_awarded == fs
        assert result.base.scatter_count == {8: 3, 10: 4, 12: 5}[fs]
        assert result.base.line_payout_units == 0
        assert result.base.payout_units < config.MAX_WIN_UNITS
        assert len(result.free_spins) == fs or result.payout_units == config.MAX_WIN_UNITS
        assert all(not s.cascade_limit_reached for s in (result.base, *result.free_spins))
        assert result.payout_units % 10 == 0
        assert replay_spec(spec) == result
        events = json.dumps(asdict(result), separators=(",", ":"))
        digest = hashlib.sha256(events.encode()).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        if result.payout_units >= 50000:
            pools[fs].add(result.payout_units)
            row = {"spec": spec, "fs": fs, "payout_units": result.payout_units,
                   "event_sha256": digest, "free_spins_played": len(result.free_spins),
                   "cap_reduction_units": result.cap_reduction_units}
            rows.append(row)
            if result.payout_units == config.MAX_WIN_UNITS:
                assert len(result.free_spins) > 0
                assert sum(result.free_spin_credits) > 0
                if len(result.free_spins) < fs and result.cap_reduction_units > 0:
                    caps[fs].append(row)
    summaries = {}
    for fs, values in pools.items():
        boundaries = sorted({50000, 500000, *values})
        gaps = sorted(((b-a, a, b) for a,b in zip(boundaries, boundaries[1:])), reverse=True)
        summaries[str(fs)] = {"distinct_high_payouts": len(values),
                              "largest_gap_units": gaps[0][0],
                              "largest_gaps_units": gaps[:5],
                              "cap_sequences": len(caps[fs]),
                              "example_cap": caps[fs][0]}
    report = {"candidate_count": count, "unique_rounds": len(seen),
              "unique_high_rounds": len(rows), "legal_rng_draws_checked": draw_count,
              "variants": summaries, "elapsed_seconds": time.perf_counter()-started,
              "candidates": rows}
    report = compact_catalog(report)
    directory = Path(__file__).resolve().parent
    (directory / "bonus_candidates.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k,v in report.items() if k != "candidates"}, indent=2))


if __name__ == "__main__":
    main()
