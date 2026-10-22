"""Reproducible finite-book math compiler. No payouts are edited after evaluation."""
from collections import Counter
from dataclasses import asdict
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE / "dependencies"), str(ROOT / "test-interface" / "engine")]
import zstandard
from polska_gurom import config
from polska_gurom.selection import replay_spec, source_fingerprint

OUT = ROOT / "test-interface" / "stake_math"
TOTAL_WEIGHT = 10**12
NATURAL_BOOKS = 100000


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(result):
    return json.dumps([{"index": 0, "type": "roundResult", "data": asdict(result)}],
                      ensure_ascii=False, separators=(",", ":")).encode()


def build():
    start = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    specs, payouts, bonuses, expansions = [], [], [], []
    seen = set()
    writer = zstandard.ZstdCompressor(level=12).stream_writer((OUT / "books_base.jsonl.zst").open("wb"))

    def add(spec, result, events):
        book_id = len(specs)
        assert not any(s.cascade_limit_reached for s in (result.base, *result.free_spins))
        assert result.payout_units % 10 == 0
        assert 0 <= result.payout_units <= config.MAX_WIN_UNITS
        seen.add(digest(events))
        specs.append(spec)
        payouts.append(result.payout_units)
        bonuses.append(bool(result.base.bonus_triggered))
        expansions.append(result.expansions)
        writer.write(b'{"id":' + str(book_id).encode() + b',"payoutMultiplier":' +
                     str(result.payout_units).encode() + b',"events":' + events + b'}\n')
        return book_id

    seed = 0
    while len(specs) < NATURAL_BOOKS:
        spec = {"seed": seed}
        result = replay_spec(spec)
        events = encode(result)
        if digest(events) not in seen:
            add(spec, result, events)
        seed += 1
        if len(specs) and len(specs) % 10000 == 0:
            print(f"Generated {len(specs)} unique complete natural books", flush=True)

    # Rare outcomes are reachable draw sequences. Optimization assigns them a
    # frequency explicitly; their astronomically low natural RNG odds are not
    # misrepresented as the final weighted model's odds.
    candidates = []
    rare_seen = set()
    for last_shifts in itertools.product((-2, -1, 0), repeat=2):
        stops = [4, 33, 27, (21 + last_shifts[0]) % 36, (13 + last_shifts[1]) % 36]
        for limit in range(5, 102):
            recipe = {"name": "wild_refill", "stops": stops,
                      "wild_refill_limit": limit, "fallback_seed": 20261019}
            spec = {"recipe": recipe}
            result = replay_spec(spec)
            events = encode(result)
            key = digest(events)
            if key not in seen and key not in rare_seen:
                rare_seen.add(key)
                candidates.append((spec, result, events))
    weights = [0] * len(specs)
    rare_groups = []
    selected = set()
    for target, mass in ((50000, 20000000), (100000, 4000000), (200000, 1000000),
                         (300000, 500000), (400000, 250000), (500000, 125000)):
        pool = [x for x in candidates if digest(x[2]) not in selected and
                ((x[1].payout_units == 500000) if target == 500000 else
                 (x[1].payout_units < 500000))]
        chosen = sorted(pool, key=lambda x: abs(x[1].payout_units-target))[:4]
        assert len(chosen) == 4
        entries = []
        for i, (spec, result, events) in enumerate(chosen):
            selected.add(digest(events))
            book_id = add(spec, result, events)
            weight = mass // 4 + (i < mass % 4)
            weights.append(weight)
            entries.append({"id": book_id, "payout_units": result.payout_units, "weight": weight})
        rare_groups.append({"target_units": target, "group_weight": mass, "books": entries})
    writer.close()

    positive = [i for i in range(NATURAL_BOOKS) if payouts[i]]
    zero = [i for i in range(NATURAL_BOOKS) if not payouts[i]]
    desired = 96 * TOTAL_WEIGHT
    reserved_sum = sum(w*p for w, p in zip(weights, payouts))
    positive_sum = sum(payouts[i] for i in positive)
    ordinary_weight, remainder = divmod(desired-reserved_sum, positive_sum)
    assert ordinary_weight > 0 and remainder % 10 == 0
    for i in positive:
        weights[i] = ordinary_weight
    # Real 0.2x/0.3x books span the payout lattice (gcd 0.1x).
    # Move one ordinary weight to the remainder if it is the sole 0.1x gap.
    if remainder == 10:
        ordinary_weight -= 1
        remainder += positive_sum
        for i in positive:
            weights[i] -= 1
    correction_books = [next(i for i in positive if payouts[i] == p) for p in (20, 30)]
    thirties = int(remainder % 20 != 0)
    twenties = (remainder - thirties*30) // 20
    assert twenties >= 0 and 20*twenties + 30*thirties == remainder
    weights[correction_books[0]] += twenties
    weights[correction_books[1]] += thirties
    zero_mass = TOTAL_WEIGHT - sum(weights)
    zero_weight, zero_remainder = divmod(zero_mass, len(zero))
    assert zero_weight > 0
    for offset, i in enumerate(zero):
        weights[i] = zero_weight + (offset < zero_remainder)
    assert len(weights) == len(payouts) == len(specs)
    assert sum(weights) == TOTAL_WEIGHT and min(weights) > 0
    assert sum(w*p for w,p in zip(weights,payouts)) == desired
    lut = OUT / "lookUpTable_base_0.csv"
    lut.write_text("".join(f"{i},{w},{p}\n" for i,(w,p) in enumerate(zip(weights,payouts))), encoding="utf-8")
    manifest = {"schema": 1, "math_version": config.MATH_VERSION,
                "total_weight": TOTAL_WEIGHT, "payout_scale": 100,
                "source_fingerprint": source_fingerprint(), "lut_sha256": digest(lut.read_bytes()),
                "books": specs}
    (OUT / "selection.json").write_text(json.dumps(manifest, separators=(",", ":")), encoding="utf-8")
    (OUT / "index.json").write_text(json.dumps({"modes": [{"name": "base", "cost": 1.0,
        "events": "books_base.jsonl.zst", "weights": lut.name}]}, indent=2), encoding="utf-8")
    second = Fraction(sum(w*p*p for w,p in zip(weights,payouts)), TOTAL_WEIGHT*10000)
    variance = second - Fraction(96,100)**2
    cap_mass = sum(w for w,p in zip(weights,payouts) if p == 500000)
    summary = {"math_version": config.MATH_VERSION, "mode": "base", "cost": 1,
        "selection": "unbiased integer ticket in published complete-round lookup table",
        "book_count": len(specs), "unique_event_sequences": len(seen),
        "natural_candidate_books": NATURAL_BOOKS, "last_natural_seed": seed-1,
        "candidate_sample_rtp": sum(payouts[:NATURAL_BOOKS]) / NATURAL_BOOKS / 100,
        "total_weight": TOTAL_WEIGHT, "weighted_payout_units_sum": desired,
        "rtp_exact_fraction": "24/25", "rtp": .96, "payout_scale": 100, "payout_step_units": 10,
        "max_win": 5000, "max_win_weight": cap_mass, "max_win_one_in": TOTAL_WEIGHT//cap_mass,
        "hit_frequency": sum(w for w,p in zip(weights,payouts) if p>0)/TOTAL_WEIGHT,
        "net_profit_frequency": sum(w for w,p in zip(weights,payouts) if p>100)/TOTAL_WEIGHT,
        "bonus_frequency": sum(w for w,b in zip(weights,bonuses) if b)/TOTAL_WEIGHT,
        "expansions_per_paid_round": sum(w*e for w,e in zip(weights,expansions))/TOTAL_WEIGHT,
        "standard_deviation": math.sqrt(float(variance)), "variance_fraction": str(variance),
        "largest_single_book_probability": max(weights)/TOTAL_WEIGHT,
        "distinct_payouts": len(set(payouts)), "rare_groups": rare_groups,
        "ordinary_positive_book_weight": ordinary_weight, "correction_book_ids": correction_books,
        "correction_additional_weights": [twenties, thirties],
        "source_fingerprint": source_fingerprint(), "elapsed_seconds": time.perf_counter()-start,
        "platform_approval": "Not performed; export and public SDK validation are local"}
    summary["files"] = {name: {"sha256": digest((OUT/name).read_bytes()), "bytes": (OUT/name).stat().st_size}
                        for name in ("index.json", "books_base.jsonl.zst", lut.name, "selection.json")}
    (OUT / "mathematics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k:summary[k] for k in ("book_count","rtp","hit_frequency","max_win_one_in","elapsed_seconds")}), flush=True)


if __name__ == "__main__":
    build()
