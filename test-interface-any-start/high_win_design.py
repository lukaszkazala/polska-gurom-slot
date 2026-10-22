"""Declared high-payout targets and exact integer weighting for math 0.6.0.

Targets are computed before candidate generation or weight assignment. Reel
rules are unchanged; the compiler only selects legal complete-round witnesses.
"""
from fractions import Fraction
from math import gcd

TOTAL_WEIGHT = 10**12
HIGH_RETURN_UNITS = 2_443_555_420_320
BONUS_MASSES = {8: 4_679_041_094, 10: 286_875_670, 12: 4_018_776}
CAP_MASSES = {0: 62_500, 8: 31_250, 10: 18_750, 12: 12_500}
FAMILY_SHARES = {0: 40, 8: 30, 10: 20, 12: 10}


def targets():
    budget = HIGH_RETURN_UNITS - 500_000 * sum(CAP_MASSES.values())
    profile = [Fraction(4, 5)**i for i in range(18)]
    total = sum(profile)
    bands = []
    for i, share in enumerate(profile):
        low, high = 50_000 + 25_000*i, 75_000 + 25_000*i
        moment = budget * share / total
        mass = round(moment / ((low + high)//2))
        bands.append({"lower_units": low, "upper_units_exclusive": high,
                      "target_weight": mass,
                      "target_probability_fraction": str(Fraction(mass, TOTAL_WEIGHT)),
                      "target_return_units_fraction": str(moment),
                      "target_rtp_percentage_points": float(moment / TOTAL_WEIGHT),
                      "rtp_relative_tolerance": 0.01})
    return {"schema": 1, "math_version": "0.6.0-high-wins",
            "baseline_math_version": "0.5.0-any-start", "total_weight": TOTAL_WEIGHT,
            "high_return_units": HIGH_RETURN_UNITS,
            "high_rtp_percentage_points": HIGH_RETURN_UNITS / TOTAL_WEIGHT,
            "ordinary_to_high_return_transfer_units": 0,
            "design": "18 bands of 250x; non-cap RTP shares decline by factor 4/5 per band; frequency targets use band midpoints",
            "family_percentages_per_band": FAMILY_SHARES,
            "cap_weights_by_awarded_fs": CAP_MASSES,
            "bonus_weights": BONUS_MASSES,
            "bands": bands}


def candidate_specs():
    """Finite legal draw sequences, independent of assigned weights."""
    import itertools
    trigger_stops = {8: [35, 28, 17, 16, 31],
                     10: [35, 28, 17, 16, 8],
                     12: [35, 27, 22, 15, 8]}
    for fs, stops in trigger_stops.items():
        for seed, expansion, shifts, limit in itertools.product(
                (20261022, 20261023), (None, 1, 2, 3),
                itertools.product((-2, -1, 0), repeat=2), range(51)):
            yield {"recipe": {"name": "bonus_wild_refill", "stops": stops,
                "free_spin_stops": [4, 33, 27, 21+shifts[0], 13+shifts[1]],
                "wild_refill_limit": limit, "expanding_reel": expansion,
                "fallback_seed": seed}}


def choose_candidates(candidates, replay, encode, digest, already_seen):
    """Retain four representatives across each band and two capped per FS."""
    best = {}
    count = 0
    for spec, result, events in candidates:
        count += 1
        payout = result.payout_units
        if payout < 50_000:
            continue
        key = digest(events)
        if key in already_seen:
            continue
        family = result.base.free_spins_awarded
        if payout == 500_000:
            # Distinct limit/refill recipes that stop at the same grid are one
            # event sequence; retain distinct events, never duplicate books.
            bucket = best.setdefault((family, 18), {})
            if key not in bucket and len(bucket) < 2:
                bucket[key] = (spec, result, events)
            continue
        band = (payout - 50_000)//25_000
        for slot, offset in enumerate((5_000, 10_000, 15_000, 20_000)):
            target = 50_000 + band*25_000 + offset
            index = (family, band, slot)
            rank = (abs(payout-target), payout, key)
            if index not in best or rank < best[index][0]:
                best[index] = (rank, (spec, result, events))
    selected = {}
    for key, value in sorted(best.items()):
        values = value.values() if len(key) == 2 else (value[1],)
        for item in values:
            selected.setdefault(digest(item[2]), item)
    return list(selected.values()), count


def _egcd(a, b):
    if not b:
        return a, 1, 0
    g, x, y = _egcd(b, a % b)
    return g, y, x-(a//b)*y


def _ceildiv(a, b):
    return -((-a)//b)


def exact_correction(weights, payouts, floors, pairs, delta):
    """Two bounded ticket transfers preserve each family/band probability.

    All arithmetic is integer. No solver tolerances or post-evaluation payout
    edits enter the exported model.
    """
    if not delta:
        return []
    assert delta % 10 == 0
    needed = delta//10
    transfers = []
    for low, high in pairs:
        step = (payouts[high]-payouts[low])//10
        if step > 0:
            transfers.append((low, high, step,
                -(weights[high]-floors[high]), weights[low]-floors[low]))
    for n, one in enumerate(transfers):
        for two in transfers[n+1:]:
            lo1, hi1, a, xmin, xmax = one
            lo2, hi2, b, ymin, ymax = two
            if {lo1, hi1}.intersection((lo2, hi2)):
                continue
            g, x, y = _egcd(a, b)
            if needed % g:
                continue
            x *= needed//g
            y *= needed//g
            dx, dy = b//g, a//g
            lower = max(_ceildiv(xmin-x, dx), _ceildiv(y-ymax, dy))
            upper = min((xmax-x)//dx, (y-ymin)//dy)
            if lower > upper:
                continue
            near = min(upper, max(lower, round(Fraction(-x, dx))))
            options = {lower, upper, near}
            k = min(options, key=lambda k: abs(x+dx*k)+abs(y-dy*k))
            x, y = x+dx*k, y-dy*k
            weights[lo1] -= x
            weights[hi1] += x
            weights[lo2] -= y
            weights[hi2] += y
            assert a*x+b*y == needed
            return [{"from": lo1, "to": hi1, "tickets": x},
                    {"from": lo2, "to": hi2, "tickets": y}]
    raise AssertionError("No bounded exact high-return correction; expand legal candidates")


def weight_high(payouts, awards, weights, plan):
    groups, floors, pairs = {}, {}, []
    high_ids = [i for i, p in enumerate(payouts) if p >= 50_000]
    for i in high_ids:
        weights[i] = 0
        band = 18 if payouts[i] == 500_000 else (payouts[i]-50_000)//25_000
        groups.setdefault((band, awards[i]), []).append(i)
    for family, mass in CAP_MASSES.items():
        ids = groups.get((18, family), [])
        assert ids, f"No real cap witness for family {family}"
        for offset, i in enumerate(ids):
            weights[i] = mass//len(ids) + (offset < mass % len(ids))
            floors[i] = 1
    for band, target in enumerate(plan["bands"]):
        mass = target["target_weight"]
        remaining_mass = mass
        for family, share in FAMILY_SHARES.items():
            ids = groups.get((band, family), [])
            assert ids, f"Missing family {family} in high band {band}"
            family_mass = remaining_mass if family == 12 else mass*share//100
            remaining_mass -= family_mass
            floor = max(1, family_mass//(20*len(ids)))
            assert floor*len(ids) < family_mass
            for i in ids:
                weights[i] = floors[i] = floor
            low, high = min(ids, key=payouts.__getitem__), max(ids, key=payouts.__getitem__)
            available = family_mass - floor*len(ids)
            target_moment = Fraction(target["target_return_units_fraction"])*family_mass/mass
            fixed = sum(weights[i]*payouts[i] for i in ids)
            spread = payouts[high]-payouts[low]
            upper = (min(available, max(0, round((target_moment-fixed-available*payouts[low])/spread)))
                     if spread else 0)
            weights[low] += available-upper
            weights[high] += upper
            if spread:
                pairs.extend((i, j) for i in ids for j in ids if payouts[j] > payouts[i])
    current = sum(weights[i]*payouts[i] for i in high_ids)
    correction = exact_correction(weights, payouts, floors, pairs, HIGH_RETURN_UNITS-current)
    assert sum(weights[i]*payouts[i] for i in high_ids) == HIGH_RETURN_UNITS
    assert all(weights[i] >= floors[i] > 0 for i in high_ids)
    actual = []
    for band, target in enumerate(plan["bands"]):
        ids = [i for (b, _), rows in groups.items() if b == band for i in rows]
        moment = sum(weights[i]*payouts[i] for i in ids)
        expected = Fraction(target["target_return_units_fraction"])
        assert sum(weights[i] for i in ids) == target["target_weight"]
        assert abs(moment-expected)*100 <= expected, f"Band {band} exceeds declared 1% RTP tolerance"
        actual.append({**target, "actual_weight": sum(weights[i] for i in ids),
                       "actual_return_units": moment,
                       "actual_rtp_percentage_points": moment/TOTAL_WEIGHT,
                       "book_ids": ids,
                       "family_weights": {str(fs): sum(weights[i] for i in groups[band, fs])
                                          for fs in FAMILY_SHARES}})
    return {**plan, "bands": actual, "exact_moment_correction": correction,
            "high_weight": sum(weights[i] for i in high_ids),
            "cap_book_ids_by_awarded_fs": {str(fs): groups[18, fs] for fs in CAP_MASSES}}
