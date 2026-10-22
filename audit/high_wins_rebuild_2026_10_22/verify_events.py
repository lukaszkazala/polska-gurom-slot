"""Independent integer event and distribution audit of a complete exported bank.

The payout contract is frozen below. Interval enumeration is independent of the
production prefix scorer. Production replay is checked in addition to, never in
place of, the independent event calculations. No input bank is modified.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import asdict
from fractions import Fraction
from functools import lru_cache
from itertools import product
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "audit/stake_cascades_v04/dependencies"))
import zstandard

REGULAR = ("L1", "L2", "L3", "L4", "P1", "P2", "P3", "P4")
SYMBOLS = REGULAR + ("WILD", "SCATTER")
TABLE = dict(zip(REGULAR, [
    {3: 10, 4: 60, 5: 200}, {3: 20, 4: 80, 5: 280},
    {3: 20, 4: 100, 5: 360}, {3: 30, 4: 130, 5: 480},
    {3: 50, 4: 200, 5: 800}, {3: 60, 4: 280, 5: 1200},
    {3: 100, 4: 440, 5: 2000}, {3: 160, 4: 800, 5: 4000},
]))
LINES = (
    (1,1,1,1,1), (1,1,1,0,0), (1,1,1,2,2),
    (0,0,0,0,0), (2,2,2,2,2), (0,0,0,1,1), (2,2,2,1,1),
    (0,1,1,1,0), (2,1,1,1,2), (0,1,1,2,2), (2,1,1,0,0),
    (1,1,0,0,1), (1,1,2,2,1), (1,1,0,1,2), (1,1,2,1,0),
    (0,0,0,1,2), (0,1,2,1,0), (2,1,0,1,2), (0,1,2,2,1), (2,1,0,0,1),
)
SCATTER_PAY = {3: 100, 4: 500, 5: 2000}
FS = {3: 8, 4: 10, 5: 12}
BONUS_MASSES = {8: 4_679_041_094, 10: 286_875_670, 12: 4_018_776}
BASE_STRIP = (
    "L1","P1","L2","L3","WILD","L1","P2","L4","L2","P3","L1","P1",
    "L3","P4","L2","L1","P2","L4","L3","P1","L1","P3","L2","WILD",
    "L4","L1","P4","L3","P1","L2","P2","L4","L3","P3","L1","SCATTER",
)
STRIPS = tuple(BASE_STRIP[n:] + BASE_STRIP[:n] for n in (0, 7, 13, 19, 27))
REFILL_SUPPORT = tuple(set(strip) - {"SCATTER"} for strip in STRIPS)
WINDOWS = tuple({tuple(strip[(stop + row) % 36] for row in range(3))
                 for stop in range(36)} for strip in STRIPS)
CAP = 500000
TOTAL = 10**12
COUNTS = Counter()
CONTEXT = {}


def ensure(condition, message):
    COUNTS["assertions"] += 1
    if not condition:
        raise AssertionError(f"{message}: {CONTEXT}")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@lru_cache(maxsize=100000)
def oracle(seq):
    """Enumerate all valid intervals, rank award then leftmost then symbol.

    The contract's strictly increasing symbol paytables ensure a shorter prefix
    never outranks its longer valid interval. This enumeration deliberately
    differs from the production target-by-target maximal-prefix implementation.
    """
    options = []
    for start, end in ((0,3), (0,4), (0,5), (1,4), (1,5), (2,5)):
        fixed = set(seq[start:end]) - {"WILD"}
        possible = REGULAR if not fixed else tuple(fixed) if len(fixed) == 1 else ()
        for symbol in possible:
            if symbol in TABLE:
                options.append((TABLE[symbol][end-start], -start,
                                -REGULAR.index(symbol), end-start, symbol))
    if not options:
        return None, 0, 0, 0
    units, negative_start, _, count, symbol = max(options)
    return symbol, count, units, -negative_start


def expected_wins(grid, multiplier):
    wins = []
    for line_id, rows in enumerate(LINES, 1):
        symbol, count, units, start = oracle(tuple(grid[rows[c]][c] for c in range(5)))
        if units:
            wins.append({"line_id": line_id, "rows": list(rows), "symbol": symbol,
                         "count": count, "payout_units": units * multiplier,
                         "line_multiplier": multiplier, "start_reel": start})
    return wins


def validate_grid(grid):
    ensure(isinstance(grid, list) and len(grid) == 3 and
           all(isinstance(row, list) and len(row) == 5 for row in grid), "grid dimensions")
    ensure(all(symbol in SYMBOLS for row in grid for symbol in row), "known grid symbols")


def validate_numeric_types(value, field=""):
    if isinstance(value, dict):
        for key, item in value.items():
            validate_numeric_types(item, key)
    elif isinstance(value, list):
        for item in value:
            validate_numeric_types(item, field)
    elif isinstance(value, (int, float, bool)):
        if field in ("bonus_triggered", "cascade_limit_reached"):
            ensure(type(value) is bool, "boolean event field type")
        else:
            ensure(type(value) is int, "integer event field type")


def validate_transition(stage, next_stage, removed):
    ensure(stage["removed_positions"] == [list(cell) for cell in sorted(removed)], "removal union")
    before, after = stage["evaluation_grid"], next_stage["evaluation_grid"]
    moves = []
    for reel in range(5):
        survivors = [(row, before[row][reel]) for row in range(3) if (row, reel) not in removed]
        holes = 3 - len(survivors)
        for dest in range(holes):
            symbol = after[dest][reel]
            ensure(symbol in REFILL_SUPPORT[reel], "refill symbol reachable and not Scatter")
            moves.append({"symbol": symbol, "from_row": dest-holes, "to_row": dest, "reel": reel})
            COUNTS["refill_symbols"] += 1
        for offset, (source, symbol) in enumerate(survivors):
            dest = holes + offset
            ensure(after[dest][reel] == symbol, "survivor order and gravity")
            if dest != source:
                moves.append({"symbol": symbol, "from_row": source, "to_row": dest, "reel": reel})
            COUNTS["surviving_symbols"] += 1
    ensure(stage["movements"] == moves, "complete ordered movement records")
    COUNTS["transitions"] += 1


def validate_spin(spin, is_free, limit):
    ensure(type(limit) is int and 0 < limit <= CAP, "positive remaining spin cap")
    multiplier = 4 if is_free else 1
    initial = spin["grid"]
    validate_grid(initial)
    ensure(all(tuple(initial[row][reel] for row in range(3)) in WINDOWS[reel]
               for reel in range(5)), "initial grid reachable from actual reel windows")
    scatters = sum(symbol == "SCATTER" for row in initial for symbol in row)
    scatter_units = SCATTER_PAY.get(min(scatters, 5), 0)
    awarded = 0 if is_free else FS.get(min(scatters, 5), 0)
    ensure(spin["scatter_count"] == scatters, "Scatter counted before expansion")
    ensure(spin["scatter_payout_units"] == scatter_units, "Scatter pays once without line multiplier")
    ensure(spin["free_spins_awarded"] == awarded and
           spin["bonus_triggered"] == (awarded > 0), "bonus award and no FS retriggers")
    ensure(spin["line_multiplier"] == multiplier, "line multiplier")
    expansion = spin["expanding_reel"]
    expected = [row[:] for row in initial]
    if expansion is not None:
        ensure(is_free and type(expansion) is int and expansion in (1, 2, 3), "legal expanding reel")
        for row in range(3):
            expected[row][expansion] = "WILD"
        COUNTS["expansions"] += 1
    ensure(spin["evaluation_grid"] == expected, "exact expansion transformation")
    stages = spin["cascades"]
    ensure(isinstance(stages, list) and 0 < len(stages) <= 1000, "cascade count")
    ensure(not spin["cascade_limit_reached"], "no exported emergency cascade cutoff")
    ensure(stages[0]["evaluation_grid"] == expected, "first cascade grid")
    ensure(spin["line_wins"] == stages[0]["line_wins"], "first-stage compatibility wins")
    credited, raw_lines = min(scatter_units, limit), 0
    for index, stage in enumerate(stages):
        CONTEXT["stage"] = index
        validate_grid(stage["evaluation_grid"])
        wins = expected_wins(stage["evaluation_grid"], multiplier)
        ensure(stage["line_wins"] == wins, "independently enumerated highest line awards")
        raw = sum(win["payout_units"] for win in wins)
        credit = min(raw, limit-credited)
        ensure(stage["line_payout_units"] == raw, "cascade raw line sum")
        ensure(stage["payout_units"] == credit, "cascade credit including partial cap payout")
        if 0 < credit < raw:
            COUNTS["partially_credited_cascades"] += 1
        credited += credit
        raw_lines += raw
        removed = {(win["rows"][reel], reel) for win in wins
                   for reel in range(win["start_reel"], win["start_reel"]+win["count"])}
        if index + 1 < len(stages):
            ensure(bool(wins) and credited < limit, "cascade continues only after an uncapped win")
            validate_transition(stage, stages[index+1], removed)
        else:
            ensure(not stage["removed_positions"] and not stage["movements"], "no terminal phantom movement")
            ensure(not wins or credited == limit, "cascade terminates on loss or cap")
        COUNTS["stages"] += 1
        COUNTS["line_awards"] += len(wins)
    ensure(spin["line_payout_units"] == raw_lines, "spin raw line sum")
    ensure(spin["raw_payout_units"] == raw_lines+scatter_units, "spin total raw sum")
    ensure(spin["payout_units"] == credited == min(raw_lines+scatter_units, limit), "spin settlement")
    COUNTS["free_spins" if is_free else "base_spins"] += 1


def validate_round(result):
    validate_numeric_types(result)
    CONTEXT["spin"] = "base"
    validate_spin(result["base"], False, CAP)
    free = result["free_spins"]
    credits = result["free_spin_credits"]
    awarded = result["base"]["free_spins_awarded"]
    ensure(len(free) == len(credits) <= awarded, "at most the awarded FS, one credit per FS")
    remaining = CAP-result["base"]["payout_units"]
    for number, (spin, credit) in enumerate(zip(free, credits), 1):
        CONTEXT["spin"] = number
        ensure(remaining > 0, "no FS after round cap")
        validate_spin(spin, True, remaining)
        ensure(credit == spin["payout_units"], "FS credit equals spin settlement")
        remaining -= credit
    ensure(len(free) == awarded or remaining == 0, "unplayed FS terminate only at cap")
    raw = result["base"]["raw_payout_units"] + sum(spin["raw_payout_units"] for spin in free)
    total = result["base"]["payout_units"] + sum(credits)
    ensure(result["raw_payout_units"] == raw, "whole-round raw sum")
    ensure(result["payout_units"] == total == min(raw, CAP), "whole-round credited sum")
    ensure(result["bonus_payout_units"] == sum(credits), "whole-round bonus sum")
    ensure(result["cap_reduction_units"] == raw-total, "whole-round cap reduction")


def ratio(numerator, denominator):
    value = Fraction(numerator, denominator)
    return {"fraction": str(value), "value": float(value)}


def mutation_checks(examples):
    """Check rejection sensitivity using real exported witnesses."""
    tests = []
    ordinary = examples["first"]
    def reject(name, mutate, original):
        changed = deepcopy(original)
        mutate(changed)
        before = COUNTS.copy()
        try:
            validate_round(changed)
        except (AssertionError, KeyError, ValueError, IndexError, TypeError):
            tests.append({"mutation": name, "rejected": True})
        else:
            raise AssertionError(f"Verifier did not reject {name}")
        finally:
            COUNTS.clear()
            COUNTS.update(before)
    reject("incorrect round credited total", lambda r: r.__setitem__("payout_units", r["payout_units"]+10), ordinary)
    reject("incorrect scatter count", lambda r: r["base"].__setitem__("scatter_count", 99), ordinary)
    reject("fractional payout event field", lambda r: r.__setitem__("payout_units", float(r["payout_units"])), ordinary)
    reject("unreachable initial reel window", lambda r: r["base"]["grid"][0].__setitem__(0, "SCATTER"), examples["no_scatter"])
    if "cascade" in examples:
        def corrupt_motion(r):
            spin = next(s for s in (r["base"], *r["free_spins"]) if len(s["cascades"]) > 1)
            spin["cascades"][0]["movements"][0]["to_row"] = 99
        reject("incorrect gravity movement", corrupt_motion, examples["cascade"])
    if "bonus" in examples:
        reject("missing awarded uncapped FS", lambda r: (r["free_spins"].pop(), r["free_spin_credits"].pop()), examples["bonus"])
    if "bonus_cap" in examples:
        def after_cap(r):
            r["free_spins"].append(deepcopy(r["free_spins"][-1]))
            r["free_spin_credits"].append(0)
        reject("executed FS after reaching round cap", after_cap, examples["bonus_cap"])
        reject("incorrect partially capped FS credit", lambda r: r["free_spin_credits"].__setitem__(-1, r["free_spin_credits"][-1]+10), examples["bonus_cap"])
    return tests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", type=Path, default=ROOT / "test-interface-any-start")
    parser.add_argument("--bank", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("event_verification.json"))
    parser.add_argument("--acceptance", action="store_true", help="Require the new high-win project acceptance contract")
    parser.add_argument("--plan", type=Path, default=Path(__file__).with_name("tuning_targets.json"))
    parser.add_argument("--skip-selector", action="store_true", help="Use for a bank snapshot not installed beside its engine")
    args = parser.parse_args()
    args.game = args.game.resolve()
    args.bank = (args.bank or args.game / "stake_math").resolve()
    args.output = args.output.resolve()
    sys.path.insert(0, str(args.game / "engine"))
    from polska_gurom import config, game, selection
    started = time.monotonic()
    report = {"success": False, "scope": "Every exported event; independent frozen-contract interval scorer, reel reachability, cascades, settlement and exact weighted metrics; full local replay in addition.",
              "game": str(args.game), "bank": str(args.bank), "acceptance_required": args.acceptance,
              "runtime": {"python": sys.version, "zstandard": zstandard.__version__}}
    try:
        ensure(config.PAYTABLE_UNITS == TABLE and config.PAYLINES == LINES, "frozen line and payout contract unchanged")
        ensure(config.REEL_STRIPS == STRIPS and
               config.REFILL_STRIPS == tuple(tuple(s for s in strip if s != "SCATTER") for strip in STRIPS), "frozen reel and refill strips unchanged")
        ensure(config.MAX_WIN_UNITS == CAP and config.PAYOUT_SCALE == 100 and
               config.FS_LINE_MULTIPLIER == 4 and config.FREE_SPINS == FS and
               config.SCATTER_PAYTABLE_UNITS == SCATTER_PAY and config.MAX_CASCADES == 1000 and
               config.EXPANDING_REELS == (1,2,3) and config.EXPANDING_WILD_NUMERATOR == 250000000 and
               config.EXPANDING_WILD_DENOMINATOR == 1000000000, "frozen mechanics contract unchanged")
        for seq in product(SYMBOLS, repeat=5):
            ensure(oracle(seq) == game._line_award_with_start(seq), f"exhaustive line mismatch {seq}")
        report["exhaustive_line_sequences"] = 100000
        print("Independent scoring matched all 100000 line sequences.", flush=True)
        manifest = json.loads((args.bank / "selection.json").read_text(encoding="utf-8"))
        summary = json.loads((args.bank / "mathematics.json").read_text(encoding="utf-8"))
        index_document = json.loads((args.bank / "index.json").read_text(encoding="utf-8"))
        ensure(index_document == {"modes":[{"name":"base", "cost":1.0,
               "events":"books_base.jsonl.zst", "weights":"lookUpTable_base_0.csv"}]},
               "one base mode with round cost1 and exact exported file references")
        ensure(summary["mode"] == "base" and summary["cost"] == 1, "summary round mode and cost1")
        with (args.bank / "lookUpTable_base_0.csv").open(newline="", encoding="utf-8") as source:
            rows = [tuple(map(int, row)) for row in csv.reader(source)]
        ensure([r[0] for r in rows] == list(range(len(rows))), "unique contiguous LUT IDs")
        ensure(all(w > 0 and 0 <= p <= CAP and p % 10 == 0 for _, w, p in rows), "positive weights and exact payout lattice")
        ensure(sum(w for _, w, _ in rows) == manifest["total_weight"] == TOTAL, "total ticket mass")
        ensure(len(manifest["books"]) == len(rows), "manifest and LUT count")
        ensure(manifest["source_fingerprint"] == selection.source_fingerprint(), "full source fingerprint")
        ensure(manifest["math_version"] == config.MATH_VERSION == summary["math_version"], "math versions agree")
        ensure(manifest["lut_sha256"] == digest(args.bank / "lookUpTable_base_0.csv"), "LUT checksum")
        for name, data in summary["files"].items():
            ensure(data["sha256"] == digest(args.bank / name) and
                   data["bytes"] == (args.bank / name).stat().st_size, f"summary file hash and size {name}")
        report["source_fingerprint"] = selection.source_fingerprint()
        report["export_sha256"] = {p.name: digest(p) for p in args.bank.iterdir() if p.is_file()}
        report["verification_script_sha256"] = digest(Path(__file__))
        plan = None
        if args.acceptance:
            plan = json.loads(args.plan.read_text(encoding="utf-8"))
            report["predeclared_plan_sha256"] = digest(args.plan)
            ensure(plan["math_version"] == config.MATH_VERSION and plan["total_weight"] == TOTAL and
                   plan["high_return_units"] == 2443555420320 and
                   plan["ordinary_to_high_return_transfer_units"] == 0, "predeclared plan fixed invariants")
            ensure(len(plan["bands"]) == 18 and [(b["lower_units"],b["upper_units_exclusive"])
                for b in plan["bands"]] == [(low,low+25000) for low in range(50000,CAP,25000)],
                "predeclared exhaustive disjoint high payout bands")
        metrics, payout_mass, variant_mass, base_scatter_mass = Counter(), Counter(), Counter(), Counter()
        band_families = defaultdict(Counter)
        coverage, cap_ids, bonus_cap_ids, high_ids = defaultdict(list), [], defaultdict(list), []
        seen, examples, contribution_records = set(), {}, []
        cap_witnesses = []
        buckets = defaultdict(lambda: Counter())
        with (args.bank / "books_base.jsonl.zst").open("rb") as source:
            with zstandard.ZstdDecompressor().stream_reader(source) as decompressed:
                for index, line in enumerate(io.TextIOWrapper(decompressed, encoding="utf-8")):
                    CONTEXT.update(book=index, spin="base", stage=0)
                    ensure(index < len(rows), "export does not exceed LUT")
                    book = json.loads(line)
                    _, weight, payout = rows[index]
                    ensure(set(book) == {"id", "payoutMultiplier", "events"} and
                           book["id"] == index and book["payoutMultiplier"] == payout, "book envelope equals LUT")
                    events = book["events"]
                    ensure(len(events) == 1 and events[0]["index"] == 0 and
                           events[0]["type"] == "roundResult", "single complete-round event envelope")
                    result = events[0]["data"]
                    ensure(result["payout_units"] == payout, "event payout equals LUT")
                    validate_round(result)
                    replay = json.loads(json.dumps(asdict(selection.replay_spec(manifest["books"][index]))))
                    ensure(replay == result, "full deterministic replay equals exported events")
                    canonical = json.dumps(events, sort_keys=True, separators=(",", ":")).encode()
                    key = hashlib.sha256(canonical).digest()
                    ensure(key not in seen, "unique complete event sequence")
                    seen.add(key)
                    base, free = result["base"], result["free_spins"]
                    award = base["free_spins_awarded"]
                    payout_mass[payout] += weight
                    base_scatter_mass[base["scatter_count"]] += weight
                    if award:
                        coverage[award].append(index)
                        variant_mass[award] += weight
                        metrics[f"bonus_{award}_payout_sum"] += weight*result["bonus_payout_units"]
                    metrics["payout_sum"] += weight*payout
                    metrics["squared_payout_sum"] += weight*payout*payout
                    metrics["base_payout_sum"] += weight*base["payout_units"]
                    metrics["bonus_payout_sum"] += weight*result["bonus_payout_units"]
                    metrics["base_scatter_payout_sum"] += weight*min(base["scatter_payout_units"], base["payout_units"])
                    metrics["bonus_scatter_payout_sum"] += weight*sum(min(s["scatter_payout_units"], s["payout_units"]) for s in free)
                    metrics["hit_weight"] += weight*(payout > 0)
                    metrics["profit_weight"] += weight*(payout > 100)
                    metrics["bonus_weight"] += weight*(award > 0)
                    metrics["max_weight"] += weight*(payout == CAP)
                    metrics["weighted_free_spins"] += weight*len(free)
                    metrics["weighted_expansions"] += weight*sum(s["expanding_reel"] is not None for s in free)
                    metrics["capped_weight"] += weight*(result["cap_reduction_units"] > 0)
                    if payout >= 50000:
                        high_ids.append(index)
                        if payout < CAP:
                            band_families[(payout-50000)//25000][award] += weight
                    if payout == CAP:
                        cap_ids.append(index)
                        reached_in_fs = base["payout_units"] < CAP and bool(free)
                        metrics["max_in_bonus_weight" if reached_in_fs else "max_in_base_weight"] += weight
                        if reached_in_fs:
                            bonus_cap_ids[award].append(index)
                            metrics[f"max_in_bonus_{award}_weight"] += weight
                        cap_witnesses.append({"id": index, "weight": weight, "awarded_fs": award,
                            "executed_fs": len(free), "unplayed_fs": award-len(free),
                            "base_payout_units": base["payout_units"], "bonus_payout_units": result["bonus_payout_units"],
                            "raw_payout_units": result["raw_payout_units"],
                            "cap_reduction_units": result["cap_reduction_units"], "cap_reached_during_fs": reached_in_fs,
                            "final_credit_units": result["free_spin_credits"][-1] if free else base["payout_units"]})
                    bucket = "5000" if payout == CAP else f"[{payout//25000*250},{payout//25000*250+250})" if payout >= 50000 else "[0,500)"
                    buckets[bucket]["books"] += 1
                    buckets[bucket]["weight"] += weight
                    buckets[bucket]["payout_sum"] += weight*payout
                    contribution_records.append((weight*payout, index, weight, payout))
                    examples.setdefault("first", result)
                    if base["scatter_count"] == 0:
                        examples.setdefault("no_scatter", result)
                    if any(len(s["cascades"]) > 1 for s in (base, *free)):
                        examples.setdefault("cascade", result)
                    if award and payout < CAP:
                        examples.setdefault("bonus", result)
                    if payout == CAP and base["payout_units"] < CAP:
                        examples.setdefault("bonus_cap", result)
                    COUNTS["books"] += 1
                    if (index+1) % 20000 == 0:
                        print(f"Verified {index+1} complete exported rounds ({time.monotonic()-started:.1f}s).", flush=True)
        ensure(COUNTS["books"] == len(rows) == summary["book_count"], "all bank records checked")
        ensure(set(coverage) == {8,10,12}, "all bonus variants have legal positive-weight records")
        for award, ids in coverage.items():
            entry = manifest["bonus_coverage"][str(award)]
            ensure(ids == entry["book_ids"] and variant_mass[award] == entry["total_weight"], "exact complete manifest bonus coverage")
        mean = Fraction(metrics["payout_sum"], TOTAL*100)
        variance = Fraction(metrics["squared_payout_sum"], TOTAL*10000)-mean**2
        ensure(mean == Fraction(24,25), "exact RTP 24/25")
        ensure(metrics["max_weight"] == 125000, "fixed total maximum mass")
        ensure(dict(variant_mass) == BONUS_MASSES, "all three fixed bonus entry masses")
        ensure(summary["rtp_exact_fraction"] == str(mean) and
               summary["variance_fraction"] == str(variance), "summary exact RTP and variance")
        for summary_key, metric_key in (("hit_frequency", "hit_weight"), ("net_profit_frequency", "profit_weight"),
                ("bonus_frequency", "bonus_weight"), ("expansions_per_paid_round", "weighted_expansions")):
            ensure(summary[summary_key] == metrics[metric_key]/TOTAL, f"summary {summary_key}")
        high_payouts = sorted(p for p in payout_mass if p >= 50000)
        bounded = sorted({50000, CAP, *high_payouts})
        gaps = sorted(((b-a, a, b) for a,b in zip(bounded, bounded[1:])), reverse=True)
        all_sorted = sorted(payout_mass)
        all_gaps = sorted(((b-a,a,b) for a,b in zip(all_sorted, all_sorted[1:])), reverse=True)
        contribution_records.sort(reverse=True)
        high_sum = sum(w*p for p,w in payout_mass.items() if p >= 50000)
        high_weight = sum(w for p,w in payout_mass.items() if p >= 50000)
        tail = {}
        for threshold in (500,750,1000,1500,2000,2500,3000,3500,4000,4500,5000):
            weight = sum(w for p,w in payout_mass.items() if p >= threshold*100)
            value = sum(w*p for p,w in payout_mass.items() if p >= threshold*100)
            tail[str(threshold)] = {"weight": weight, "probability": ratio(weight,TOTAL),
                                   "rtp": ratio(value,TOTAL*100), "share_of_total_rtp": ratio(value,metrics["payout_sum"])}
        report["metrics"] = {
            "math_version": config.MATH_VERSION, "book_count": len(rows), "total_weight": TOTAL,
            "rtp": ratio(metrics["payout_sum"], TOTAL*100), "variance": ratio(variance.numerator,variance.denominator),
            "standard_deviation": math.sqrt(float(variance)),
            "hit_frequency": ratio(metrics["hit_weight"],TOTAL), "net_profit_frequency": ratio(metrics["profit_weight"],TOTAL),
            "base_rtp": ratio(metrics["base_payout_sum"],TOTAL*100),
            "bonus_rtp": ratio(metrics["bonus_payout_sum"],TOTAL*100),
            "ordinary_rtp": ratio(metrics["payout_sum"]-high_sum,TOTAL*100),
            "high_rtp": ratio(high_sum,TOTAL*100), "high_rtp_percentage_points": high_sum/TOTAL,
            "high_probability": ratio(high_weight,TOTAL), "high_weight": high_weight,
            "high_records": len(high_ids), "high_distinct_payouts": len(high_payouts),
            "high_largest_gap_x": gaps[0][0]/100,
            "high_gaps_including_range_edges": [{"lower_x":a/100,"upper_x":b/100,"gap_x":d/100} for d,a,b in gaps],
            "largest_gaps_all_payouts": [{"lower_x":a/100,"upper_x":b/100,"gap_x":d/100} for d,a,b in all_gaps[:20]],
            "maximum_probability": ratio(metrics["max_weight"],TOTAL), "maximum_one_in": TOTAL//metrics["max_weight"],
            "maximum_base_weight": metrics["max_in_base_weight"], "maximum_bonus_weight": metrics["max_in_bonus_weight"],
            "maximum_bonus_variant_weights": {str(fs):metrics[f"max_in_bonus_{fs}_weight"] for fs in (8,10,12)},
            "bonus_entry_weights": {str(fs):variant_mass[fs] for fs in (8,10,12)},
            "bonus_variant_book_counts": {str(fs):len(coverage[fs]) for fs in (8,10,12)},
            "bonus_variant_rtp": {str(fs):ratio(metrics[f"bonus_{fs}_payout_sum"],TOTAL*100) for fs in (8,10,12)},
            "distinct_payouts": len(payout_mass), "cap_witnesses": cap_witnesses,
            "high_band_statistics": {key:{**dict(value),"probability":ratio(value["weight"],TOTAL),
                                             "rtp":ratio(value["payout_sum"],TOTAL*100)} for key,value in buckets.items()},
            "tail_concentration": tail,
            "high_top_record_rtp_shares": {str(n):ratio(sum(item[0] for item in sorted(
                (item for item in contribution_records if item[3]>=50000),reverse=True)[:n]),high_sum)
                for n in (1,5,10,20)},
            "raw_weighted_sums": dict(metrics),
        }
        report["rejection_sensitivity_checks"] = mutation_checks(examples)
        if not args.skip_selector:
            ensure(args.bank == (args.game / "stake_math").resolve(), "selector checks require installed bank")
            loaded, cumulative, payouts = selection.load_distribution()
            ensure(payouts == [p for _,_,p in rows], "selector loaded final payouts")
            expected_cdf, total = [], 0
            for _,weight,_ in rows:
                total += weight
                expected_cdf.append(total)
            ensure(cumulative == expected_cdf, "selector loaded final cumulative weights")
            identities = {id(spec):p for spec,(_,_,p) in zip(loaded["books"],rows)}
            original = selection.replay_spec
            selection.replay_spec = lambda spec: SimpleNamespace(payout_units=identities[id(spec)])
            class Ticket:
                def __init__(self, value): self.value = value
                def randrange(self, bound):
                    ensure(bound == TOTAL, "selector ticket bound")
                    return self.value
            try:
                for index,(left,right) in enumerate(zip([0]+cumulative[:-1],cumulative)):
                    ensure(selection.select_round(Ticket(left))[0] == index, "first ticket per interval")
                    ensure(selection.select_round(Ticket(right-1))[0] == index, "last ticket per interval")
            finally:
                selection.replay_spec = original
            report["selector_boundaries"] = {"intervals": len(rows), "tickets_checked": 2*len(rows), "success": True,
                "method": "Production interval selector at both boundaries; event reconstruction independently verified for every spec above."}
        else:
            report["selector_boundaries"] = {"skipped": True, "reason": "Bank snapshot not installed beside engine"}
        if args.acceptance:
            ensure(gaps[0][0] <= 25000, "high payout gap including edges <=250x")
            ensure(metrics["max_in_base_weight"] > 0 and metrics["max_in_bonus_weight"] > 0, "maximum in base and FS")
            ensure(any(w["cap_reached_during_fs"] and w["unplayed_fs"] > 0 for w in cap_witnesses), "real cap during FS stops unplayed FS")
            ensure(COUNTS["partially_credited_cascades"] > 0, "partial cap credit covered by actual exported record")
            ensure(high_sum == 2443555420320, "original >=500x RTP budget preserved exactly")
            plan_checks = []
            for band_index, band in enumerate(plan["bands"]):
                low, high = band["lower_units"], band["upper_units_exclusive"]
                mass = sum(weight for payout,weight in payout_mass.items() if low <= payout < high)
                moment = sum(weight*payout for payout,weight in payout_mass.items() if low <= payout < high)
                target = Fraction(band["target_return_units_fraction"])
                tolerance = Fraction(str(band["rtp_relative_tolerance"]))
                ensure(mass == band["target_weight"], "exact predeclared band frequency")
                ensure(abs(moment-target) <= target*tolerance, "predeclared band RTP contribution tolerance")
                remaining = mass
                family_checks = {}
                for family in (0,8,10,12):
                    target_family_mass = remaining if family == 12 else mass*plan["family_percentages_per_band"][str(family)]//100
                    remaining -= target_family_mass
                    ensure(band_families[band_index][family] == target_family_mass > 0,
                           "predeclared positive per-family band frequency")
                    family_checks[str(family)] = target_family_mass
                declared = summary["high_win_design"]["bands"][band_index]
                ensure(declared["actual_weight"] == mass and declared["actual_return_units"] == moment and
                       declared["family_weights"] == family_checks, "export summary band achievements independently reproduced")
                plan_checks.append({"lower_x":low/100,"upper_x_exclusive":high/100,
                    "target_weight":band["target_weight"],"actual_weight":mass,
                    "target_return_units_fraction":str(target),"actual_return_units":moment,
                    "relative_rtp_deviation": {"fraction":str(abs(Fraction(moment)-target)/target),
                                               "value":float(abs(Fraction(moment)-target)/target)},
                    "family_weights":family_checks})
            for family, expected_weight in plan["cap_weights_by_awarded_fs"].items():
                ensure(sum(w["weight"] for w in cap_witnesses if w["awarded_fs"] == int(family)) == expected_weight,
                       "exact predeclared maximum split")
            report["predeclared_band_acceptance"] = plan_checks
            ensure(digest(args.plan) == report["predeclared_plan_sha256"], "plan stable throughout verification")
        ensure(selection.source_fingerprint() == report["source_fingerprint"], "game sources stable throughout verification")
        ensure({p.name:digest(p) for p in args.bank.iterdir() if p.is_file()} == report["export_sha256"],
               "input export stable throughout verification")
        report.update(success=True, math_version=config.MATH_VERSION,
                      unique_event_sequences=len(seen), exported_books_checked=len(rows))
    except Exception as exc:
        report["error"] = repr(exc)
        raise
    finally:
        report["counts"] = dict(COUNTS)
        report["elapsed_seconds"] = time.monotonic()-started
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        print(json.dumps({"success":report["success"],"output":str(args.output),
                          "counts":report["counts"],"elapsed_seconds":report["elapsed_seconds"],
                          "error":report.get("error")}),flush=True)


if __name__ == "__main__":
    main()
