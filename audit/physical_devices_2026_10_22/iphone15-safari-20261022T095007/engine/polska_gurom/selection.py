"""Local replay of exactly the complete-round distribution published to RGS.

The production platform selects an exported book. This local demo selects its
integer ticket and regenerates the identical book without needing a Zstd runtime.
"""
from __future__ import annotations
from bisect import bisect_right
import csv
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from . import config, game


def source_fingerprint():
    here = Path(__file__).resolve().parent
    return {name: hashlib.sha256((here / name).read_bytes()).hexdigest()
            for name in ("config.py", "game.py", "selection.py")}


class RecipeRandom(random.Random):
    """A finite, reachable draw sequence used to construct rare exported books.

    Every forced stop and refill occurs on its actual reel strip. Their final
    probability comes from the published book weights, not natural reel odds.
    """
    def __init__(self, recipe):
        super().__init__(recipe["fallback_seed"])
        self.stops = iter(recipe["stops"])
        self.initial = 5
        self.wilds = recipe["wild_refill_limit"]

    def randrange(self, stop, *args):
        if self.initial:
            value = next(self.stops)
            if args or not 0 <= value < stop:
                raise ValueError("Invalid witness stop")
            self.initial -= 1
            return value
        return super().randrange(stop, *args)

    def choice(self, population):
        if config.WILD in population and (self.wilds is None or self.wilds > 0):
            if self.wilds is not None:
                self.wilds -= 1
            return config.WILD
        return super().choice(population)


def replay_spec(spec):
    rng = random.Random(spec["seed"]) if "seed" in spec else RecipeRandom(spec["recipe"])
    return game.play_round(rng)


def _validate_bonus_coverage(manifest, weights):
    """Reject a finite bank that makes any declared feature unreachable."""
    declared = {str(fs): scatters for scatters, fs in config.FREE_SPINS.items()}
    coverage = manifest.get("bonus_coverage")
    if not isinstance(coverage, dict) or set(coverage) != set(declared):
        raise ValueError("Declared bonus coverage is missing or incomplete; rebuild math")
    seen = set()
    for fs, scatters in declared.items():
        group = coverage[fs]
        ids = group.get("book_ids")
        if (group.get("scatters") != scatters or not isinstance(ids, list) or not ids or
                any(type(i) is not int or not 0 <= i < len(weights) for i in ids) or
                len(set(ids)) != len(ids) or seen.intersection(ids)):
            raise ValueError("Invalid declared bonus coverage IDs")
        seen.update(ids)
        mass = sum(weights[i] for i in ids)
        if mass <= 0 or type(group.get("total_weight")) is not int or mass != group["total_weight"]:
            raise ValueError("Declared bonus has no valid positive weight")
        for book_id in ids:
            result = replay_spec(manifest["books"][book_id])
            if (weights[book_id] <= 0 or result.base.scatter_count != scatters or
                    result.base.free_spins_awarded != int(fs) or not result.base.bonus_triggered or
                    len(result.free_spins) > int(fs) or
                    len(result.free_spins) < int(fs) and result.payout_units != config.MAX_WIN_UNITS):
                raise ValueError("Declared bonus coverage does not match the actual replay")


@lru_cache(maxsize=1)
def load_distribution():
    directory = Path(__file__).resolve().parents[2] / "stake_math"
    manifest = json.loads((directory / "selection.json").read_text(encoding="utf-8"))
    if manifest["math_version"] != config.MATH_VERSION or manifest["source_fingerprint"] != source_fingerprint():
        raise RuntimeError("Math books are stale; rebuild and validate the published distribution")
    cumulative, payouts, total = [], [], 0
    with (directory / "lookUpTable_base_0.csv").open(encoding="utf-8", newline="") as stream:
        for index, row in enumerate(csv.reader(stream)):
            book_id, weight, payout = map(int, row)
            if book_id != index or weight <= 0 or payout % 10 or not 0 <= payout <= config.MAX_WIN_UNITS:
                raise ValueError("Invalid weighted book")
            total += weight
            cumulative.append(total)
            payouts.append(payout)
    if total != manifest["total_weight"] or total >= 2**64 or len(payouts) != len(manifest["books"]):
        raise ValueError("Distribution totals do not match")
    lut = directory / "lookUpTable_base_0.csv"
    if hashlib.sha256(lut.read_bytes()).hexdigest() != manifest["lut_sha256"]:
        raise ValueError("Distribution checksum mismatch")
    weights = [b-a for a, b in zip([0]+cumulative[:-1], cumulative)]
    _validate_bonus_coverage(manifest, weights)
    return manifest, cumulative, payouts


def select_round(rng):
    manifest, cumulative, payouts = load_distribution()
    index = bisect_right(cumulative, rng.randrange(manifest["total_weight"]))
    result = replay_spec(manifest["books"][index])
    if result.payout_units != payouts[index]:
        raise RuntimeError("Replayed payout differs from published book")
    return index, result
