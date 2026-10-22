"""Fresh exhaustive v0.5 audit. Does not edit game, bank, or synced sources."""
from __future__ import annotations

from bisect import bisect_right
from collections import Counter, defaultdict
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
import random
import sys
import time
from types import SimpleNamespace

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
GAME = ROOT / "test-interface-any-start"
sys.path[:0] = [str(ROOT / "audit/stake_cascades_v04/dependencies"), str(GAME / "engine")]
import zstandard
from polska_gurom import config, game, selection

# Independent declared contract, not values read from production evaluators.
REGULAR = ("L1", "L2", "L3", "L4", "P1", "P2", "P3", "P4")
SYMBOLS = REGULAR + ("WILD", "SCATTER")
TABLE = dict(zip(REGULAR, [
    {3:10,4:60,5:200}, {3:20,4:80,5:280}, {3:20,4:100,5:360},
    {3:30,4:130,5:480}, {3:50,4:200,5:800}, {3:60,4:280,5:1200},
    {3:100,4:440,5:2000}, {3:160,4:800,5:4000},
]))
LINES = (
    (1,1,1,1,1), (1,1,1,0,0), (1,1,1,2,2),
    (0,0,0,0,0), (2,2,2,2,2),
    (0,0,0,1,1), (2,2,2,1,1),
    (0,1,1,1,0), (2,1,1,1,2),
    (0,1,1,2,2), (2,1,1,0,0),
    (1,1,0,0,1), (1,1,2,2,1),
    (1,1,0,1,2), (1,1,2,1,0),
    (0,0,0,1,2),
    (0,1,2,1,0), (2,1,0,1,2),
    (0,1,2,2,1), (2,1,0,0,1),
)
SCATTER_PAY = {3:100,4:500,5:2000}
FS = {3:8,4:10,5:12}
CAP = 500000
COUNTS = Counter()
CONTEXT = {}


def ensure(condition, message):
    COUNTS["assertions"] += 1
    if not condition:
        raise AssertionError(f"{message}: {CONTEXT}")


def digest(data):
    return hashlib.sha256(data).hexdigest()


@lru_cache(maxsize=100000)
def oracle(seq):
    """Enumerate every interval then rank by award, start, symbol order.

    Unlike production prefix loops, explicitly enumerate all 3/4/5-cell
    intervals. Monotonic paytable means a valid longer interval outranks
    its shorter intervals. Returned tie list includes all equal winners.
    """
    candidates = []
    for start, end in ((0,3),(0,4),(0,5),(1,4),(1,5),(2,5)):
        present = set(seq[start:end]) - {"WILD"}
        possible = REGULAR if not present else tuple(present) if len(present) == 1 else ()
        for symbol in possible:
            if symbol in TABLE:
                candidates.append((TABLE[symbol][end-start], start, REGULAR.index(symbol), end-start, symbol))
    if not candidates:
        return (None,0,0,0), ()
    candidates.sort(key=lambda x: (-x[0],x[1],x[2]))
    units,start,_,count,symbol = candidates[0]
    ties = tuple((u,s,c,t) for u,s,_,c,t in candidates if u == units)
    return (symbol,count,units,start), ties


def exhaustive_lines():
    examples = []
    ties = any_start_only = win_sequences = 0
    for seq in product(SYMBOLS, repeat=5):
        expected, choices = oracle(seq)
        actual = game._line_award_with_start(seq)
        ensure(expected == actual, f"line mismatch {seq}: {expected} != {actual}")
        win_sequences += expected[2] > 0
        any_start_only += expected[2] > 0 and expected[3] > 0
        if len({(s,c) for _,s,c,_ in choices}) > 1:
            ties += 1
            if len(examples) < 12:
                examples.append({"symbols":seq,"selected":expected,"equal_best_intervals":choices})
    return {"sequences_checked":100000,"mismatches":0,"winning_sequences":win_sequences,
            "winning_selected_start_after_reel_one":any_start_only,
            "sequences_with_equal_best_distinct_intervals":ties,"tie_examples":examples,
            "tie_rule":"Maximum award, then leftmost start, then declared regular-symbol order."}


def expected_wins(grid, mult):
    result = []
    for line_id,rows in enumerate(LINES,1):
        (symbol,count,units,start),_ = oracle(tuple(grid[rows[r]][r] for r in range(5)))
        if units:
            result.append({"line_id":line_id,"rows":list(rows),"symbol":symbol,"count":count,
                           "payout_units":units*mult,"line_multiplier":mult,"start_reel":start})
    return result


def validate_grid(grid):
    ensure(len(grid)==3 and all(len(r)==5 for r in grid),"grid dimensions")
    ensure(all(s in SYMBOLS for r in grid for s in r),"known symbols")


def validate_transition(current, following, removed):
    ensure(current["removed_positions"] == [list(p) for p in sorted(removed)],"removal union")
    before,after = current["evaluation_grid"], following["evaluation_grid"]
    moves = []
    for col in range(5):
        survivors = [(r,before[r][col]) for r in range(3) if (r,col) not in removed]
        holes = 3-len(survivors)
        for dest in range(holes):
            symbol = after[dest][col]
            ensure(symbol != "SCATTER" and symbol in config.REFILL_STRIPS[col],"refill support")
            moves.append({"symbol":symbol,"from_row":dest-holes,"to_row":dest,"reel":col})
        for n,(source,symbol) in enumerate(survivors):
            dest = holes+n
            ensure(after[dest][col] == symbol,"survivor order and gravity")
            if dest != source:
                moves.append({"symbol":symbol,"from_row":source,"to_row":dest,"reel":col})
    ensure(current["movements"] == moves,"complete movement records")
    COUNTS["transitions"] += 1


INITIAL_WINDOWS = [{tuple(strip[(i+r)%len(strip)] for r in range(3)) for i in range(len(strip))}
                   for strip in config.REEL_STRIPS]


def validate_spin(spin, is_free, limit):
    mult = 4 if is_free else 1
    initial = spin["grid"]
    validate_grid(initial)
    ensure(all(tuple(initial[r][c] for r in range(3)) in INITIAL_WINDOWS[c]
               for c in range(5)),"initial grid reachable from real reel windows")
    count = sum(s=="SCATTER" for row in initial for s in row)
    scatter = SCATTER_PAY.get(min(count,5),0)
    fs = 0 if is_free else FS.get(min(count,5),0)
    ensure(spin["scatter_count"]==count,"scatter count before expansion")
    ensure(spin["scatter_payout_units"]==scatter,"scatter pays once and without multiplier")
    ensure(spin["free_spins_awarded"]==fs and spin["bonus_triggered"]==(fs>0),"bonus trigger")
    ensure(spin["line_multiplier"]==mult,"line-only multiplier")
    expansion = spin["expanding_reel"]
    expected = [r[:] for r in initial]
    if expansion is not None:
        ensure(is_free and type(expansion) is int and expansion in (1,2,3),"expanding reel")
        for row in range(3):
            expected[row][expansion] = "WILD"
        COUNTS["expansions"] += 1
    ensure(spin["evaluation_grid"] == expected,"expansion transformation")
    stages = spin["cascades"]
    ensure(stages and len(stages)<=1000,"stage count")
    ensure(stages[0]["evaluation_grid"] == expected,"first stage")
    ensure(spin["line_wins"] == stages[0]["line_wins"],"legacy first-stage wins")
    ensure(not spin["cascade_limit_reached"],"no bank result hits safety cutoff")
    credited,raw_lines = min(scatter,limit),0
    for i,stage in enumerate(stages):
        CONTEXT["stage"]=i
        validate_grid(stage["evaluation_grid"])
        wins = expected_wins(stage["evaluation_grid"],mult)
        ensure(stage["line_wins"]==wins,"independent interval line calculation")
        raw = sum(w["payout_units"] for w in wins)
        ensure(stage["line_payout_units"]==raw,"stage raw sum")
        credit = min(raw,limit-credited)
        ensure(stage["payout_units"]==credit,"credited stage cap")
        credited += credit
        raw_lines += raw
        removed = {(w["rows"][col],col) for w in wins
                   for col in range(w["start_reel"],w["start_reel"]+w["count"])}
        if i+1<len(stages):
            ensure(bool(wins) and credited<limit,"only continue after noncapped winning stage")
            validate_transition(stage,stages[i+1],removed)
        else:
            ensure(not stage["removed_positions"] and not stage["movements"],"no phantom terminal movements")
            ensure(not wins or credited==limit,"terminal stage loses or reaches cap")
        COUNTS["stages"] += 1
        COUNTS["line_awards"] += len(wins)
        COUNTS["line_awards_start_2"] += sum(w["start_reel"]==1 for w in wins)
        COUNTS["line_awards_start_3"] += sum(w["start_reel"]==2 for w in wins)
    ensure(spin["line_payout_units"]==raw_lines,"spin raw line sum")
    ensure(spin["raw_payout_units"]==raw_lines+scatter,"spin raw sum")
    ensure(spin["payout_units"]==credited==min(raw_lines+scatter,limit),"spin settlement")
    COUNTS["free_spins" if is_free else "base_spins"] += 1


def validate_round(result):
    CONTEXT["spin"]="base"
    validate_spin(result["base"],False,CAP)
    remaining = CAP-result["base"]["payout_units"]
    ensure(len(result["free_spins"])==len(result["free_spin_credits"]),"one credit per FS")
    for n,(spin,credit) in enumerate(zip(result["free_spins"],result["free_spin_credits"]),1):
        CONTEXT["spin"]=n
        ensure(remaining>0,"bonus stops at cap")
        validate_spin(spin,True,remaining)
        ensure(credit==spin["payout_units"],"free-spin credit")
        remaining -= credit
    ensure(len(result["free_spins"])==result["base"]["free_spins_awarded"] or remaining==0,
           "all granted spins executed unless max")
    raw = result["base"]["raw_payout_units"]+sum(s["raw_payout_units"] for s in result["free_spins"])
    total = result["base"]["payout_units"]+sum(result["free_spin_credits"])
    ensure(result["raw_payout_units"]==raw,"round raw sum")
    ensure(result["payout_units"]==total==min(raw,CAP),"round credited sum")
    ensure(result["bonus_payout_units"]==sum(result["free_spin_credits"]),"bonus sum")
    ensure(result["cap_reduction_units"]==raw-total,"cap reduction")


def ratio(num,den):
    f = Fraction(num,den)
    return {"fraction":str(f),"value":float(f)}


def main():
    start = time.monotonic()
    OUT.mkdir(parents=True,exist_ok=True)
    report = {"math_version":config.MATH_VERSION,"success":False,
              "runtime":{"python":sys.version,"zstandard":zstandard.__version__},
              "scope":"Exhaustive line inputs; every exported weighted book, every grid and cascade; exact rational distribution metrics."}
    try:
        report["source_sha256"] = {str(p.relative_to(ROOT)):digest(p.read_bytes())
            for p in [GAME/"engine/polska_gurom/config.py",GAME/"engine/polska_gurom/game.py",
                      GAME/"engine/polska_gurom/selection.py",*(GAME/"stake_math").glob("*")]}
        ensure(config.PAYTABLE_UNITS==TABLE and config.PAYLINES==LINES,"independent spec matches configuration")
        ensure(len(LINES)==len(set(LINES))==20,"20 distinct active paylines")
        report["exhaustive_lines"]=exhaustive_lines()
        print("Exhaustive 100000 line sequences passed.",flush=True)
        bank = GAME/"stake_math"
        manifest = json.loads((bank/"selection.json").read_text(encoding="utf-8"))
        summary = json.loads((bank/"mathematics.json").read_text(encoding="utf-8"))
        rows = [tuple(map(int,row)) for row in csv.reader((bank/"lookUpTable_base_0.csv").open())]
        ensure([r[0] for r in rows]==list(range(len(rows))),"contiguous unique CSV IDs")
        ensure(all(w>0 and p>=0 and p<=CAP and p%10==0 for _,w,p in rows),"positive integral weights and payout lattice")
        total = sum(w for _,w,_ in rows)
        ensure(total==manifest["total_weight"]==10**12 and total<2**64,"weight total")
        ensure(manifest["source_fingerprint"]==selection.source_fingerprint(),"manifest source fingerprint")
        ensure(manifest["lut_sha256"]==digest((bank/"lookUpTable_base_0.csv").read_bytes()),"LUT checksum")
        for name,data in summary["files"].items():
            ensure(data["sha256"]==digest((bank/name).read_bytes()) and data["bytes"]==(bank/name).stat().st_size,
                   "math summary file hash and size")
        cumulative = []
        for _,w,_ in rows:
            cumulative.append(w+(cumulative[-1] if cumulative else 0))
        seen = set()
        payout_mass = Counter()
        buckets = defaultdict(lambda: {"books":0,"weight":0,"weighted_payout_units":0})
        metrics = Counter()
        coverage = defaultdict(list)
        base_stages,free_stages = Counter(),Counter()
        expansion_reels = Counter()
        base_scatter_counts = Counter()
        top_records = []
        categories_examples = {}
        largest_stages = {"base":(0,None),"free":(0,None)}
        with zstandard.ZstdDecompressor().stream_reader((bank/"books_base.jsonl.zst").open("rb")) as dec:
            stream = io.TextIOWrapper(dec,encoding="utf-8")
            for index,line in enumerate(stream):
                CONTEXT.update(book=index,spin="base",stage=0)
                book = json.loads(line)
                ensure(book["id"]==index,"JSONL ID equals CSV")
                ensure(set(book)=={"id","payoutMultiplier","events"},"book fields")
                _,weight,payout = rows[index]
                ensure(book["payoutMultiplier"]==payout,"CSV-book payout equality")
                events = book["events"]
                ensure(len(events)==1 and events[0]["index"]==0 and events[0]["type"]=="roundResult","event envelope")
                result = events[0]["data"]
                ensure(result["payout_units"]==payout,"event-book payout equality")
                validate_round(result)
                replay = json.loads(json.dumps(asdict(selection.replay_spec(manifest["books"][index]))))
                ensure(replay==result,"complete exported book equals current local replay")
                key = digest(json.dumps(events,sort_keys=True,separators=(",",":")).encode())
                ensure(key not in seen,"complete event sequence unique")
                seen.add(key)
                base = result["base"]
                fs = base["free_spins_awarded"]
                if fs:
                    coverage[fs].append(index)
                    metrics[f"bonus_{fs}_weight"] += weight
                    categories_examples.setdefault(f"bonus_{fs}",index)
                if payout==CAP:
                    categories_examples.setdefault("maximum",index)
                    metrics["max_in_base_weight" if base["payout_units"]==CAP else "max_in_bonus_weight"] += weight
                metrics["weighted_payout_units"] += weight*payout
                metrics["weighted_squared_payout_units"] += weight*payout*payout
                metrics["weighted_base_units"] += weight*base["payout_units"]
                metrics["weighted_bonus_units"] += weight*result["bonus_payout_units"]
                metrics["weighted_base_scatter_units"] += weight*min(base["scatter_payout_units"],base["payout_units"])
                metrics["weighted_bonus_scatter_units"] += weight*sum(min(s["scatter_payout_units"],s["payout_units"])
                                                                         for s in result["free_spins"])
                metrics["weighted_free_spins"] += weight*len(result["free_spins"])
                metrics["weighted_expansions"] += weight*sum(s["expanding_reel"] is not None for s in result["free_spins"])
                metrics["weighted_cap_reduction_units"] += weight*result["cap_reduction_units"]
                metrics["weighted_base_stages"] += weight*len(base["cascades"])
                metrics["weighted_free_stages"] += weight*sum(len(s["cascades"]) for s in result["free_spins"])
                metrics["base_cascade_weight"] += weight*(len(base["cascades"])>1)
                metrics["any_cascade_weight"] += weight*any(len(s["cascades"])>1 for s in [base,*result["free_spins"]])
                metrics["bonus_weight"] += weight*(fs>0)
                metrics["hit_weight"] += weight*(payout>0)
                metrics["partial_weight"] += weight*(0<payout<100)
                metrics["breakeven_weight"] += weight*(payout==100)
                metrics["profit_weight"] += weight*(payout>100)
                metrics["zero_weight"] += weight*(payout==0)
                metrics["max_weight"] += weight*(payout==CAP)
                metrics["capped_weight"] += weight*(result["cap_reduction_units"]>0)
                base_stages[len(base["cascades"])] += weight
                base_scatter_counts[base["scatter_count"]] += weight
                if len(base["cascades"])>largest_stages["base"][0]:
                    largest_stages["base"]=(len(base["cascades"]),index)
                for s in result["free_spins"]:
                    free_stages[len(s["cascades"])] += weight
                    if s["expanding_reel"] is not None:
                        expansion_reels[s["expanding_reel"]+1] += weight
                    if len(s["cascades"])>largest_stages["free"][0]:
                        largest_stages["free"]=(len(s["cascades"]),index)
                payout_mass[payout] += weight
                bucket = ("0" if payout==0 else "(0,1)" if payout<100 else "1" if payout==100 else
                          "(1,5)" if payout<500 else "[5,20)" if payout<2000 else "[20,100)" if payout<10000 else
                          "[100,500)" if payout<50000 else "[500,1000)" if payout<100000 else
                          "[1000,2000)" if payout<200000 else "[2000,3000)" if payout<300000 else
                          "[3000,4000)" if payout<400000 else "[4000,5000)" if payout<CAP else "5000")
                buckets[bucket]["books"] += 1
                buckets[bucket]["weight"] += weight
                buckets[bucket]["weighted_payout_units"] += weight*payout
                top_records.append((weight*payout,index,weight,payout))
                COUNTS["books"] += 1
                if (index+1)%10000==0:
                    print(f"Validated and replayed {index+1} complete books; {time.monotonic()-start:.1f}s.",flush=True)
        ensure(COUNTS["books"]==len(rows)==len(manifest["books"])==summary["book_count"],"book total")
        for n,ids in coverage.items():
            cov = manifest["bonus_coverage"][str(n)]
            ensure(ids==cov["book_ids"] and metrics[f"bonus_{n}_weight"]==cov["total_weight"],"complete exact bonus coverage")
        exact_mean = Fraction(metrics["weighted_payout_units"],total*100)
        second = Fraction(metrics["weighted_squared_payout_units"],total*10000)
        variance = second-exact_mean**2
        ensure(exact_mean==Fraction(24,25),"exact RTP target")
        ensure(str(variance)==summary["variance_fraction"],"summary variance")
        for name,key in (("hit_frequency","hit_weight"),("net_profit_frequency","profit_weight"),
                         ("bonus_frequency","bonus_weight"),("expansions_per_paid_round","weighted_expansions")):
            ensure(metrics[key]/total==summary[name],f"summary {name}")
        ensure(total/metrics["max_weight"]==summary["max_win_one_in"],"summary maximum odds")
        sorted_payouts = sorted(payout_mass)
        gaps = sorted([(b-a,a,b) for a,b in zip(sorted_payouts,sorted_payouts[1:])],reverse=True)[:15]
        top_records.sort(reverse=True)
        concentrations = {}
        for n in (1,10,100,1000):
            concentrations[str(n)] = {
                "rtp_share":ratio(sum(a for a,_,_,_ in top_records[:n]),metrics["weighted_payout_units"]),
                "probability":ratio(sum(w for _,_,w,_ in top_records[:n]),total)}
        tail = {}
        for threshold in (5,20,100,500,1000,2000,3000,4000,5000):
            w=sum(w for _,w,p in rows if p>=threshold*100)
            wp=sum(w*p for _,w,p in rows if p>=threshold*100)
            tail[str(threshold)]={"probability":ratio(w,total),"rtp_contribution":ratio(wp,total*100),
                                  "rtp_share":ratio(wp,metrics["weighted_payout_units"])}
        max_book_weight=max(w for _,w,_ in rows)
        metrics_out = {
            "total_weight":total,"positive_weight_records":len(rows),"distinct_payouts":len(payout_mass),
            "exact_rtp":str(exact_mean),"rtp":float(exact_mean),"second_moment":str(second),
            "variance_fraction":str(variance),"variance":float(variance),"standard_deviation":math.sqrt(float(variance)),
            "house_edge":float(1-exact_mean),
            "largest_single_book_probability":max_book_weight/total,
            "largest_single_book_ids":[i for i,w,p in rows if w==max_book_weight],
            "positive_payout_records":sum(p>0 for _,_,p in rows),
            "positive_payout_record_share":sum(p>0 for _,_,p in rows)/len(rows),
            "hit":ratio(metrics["hit_weight"],total),"zero":ratio(metrics["zero_weight"],total),
            "partial_return":ratio(metrics["partial_weight"],total),"break_even":ratio(metrics["breakeven_weight"],total),
            "net_profit":ratio(metrics["profit_weight"],total),"bonus":ratio(metrics["bonus_weight"],total),
            "bonus_one_in":total/metrics["bonus_weight"],"maximum":ratio(metrics["max_weight"],total),
            "maximum_one_in":total/metrics["max_weight"],
            "maximum_in_base":ratio(metrics["max_in_base_weight"],total),
            "maximum_in_bonus":ratio(metrics["max_in_bonus_weight"],total),
            "round_cap_reductions":ratio(metrics["capped_weight"],total),
            "base_rtp":ratio(metrics["weighted_base_units"],total*100),
            "bonus_rtp":ratio(metrics["weighted_bonus_units"],total*100),
            "base_scatter_rtp":ratio(metrics["weighted_base_scatter_units"],total*100),
            "bonus_scatter_rtp":ratio(metrics["weighted_bonus_scatter_units"],total*100),
            "base_line_rtp":ratio(metrics["weighted_base_units"]-metrics["weighted_base_scatter_units"],total*100),
            "bonus_line_rtp":ratio(metrics["weighted_bonus_units"]-metrics["weighted_bonus_scatter_units"],total*100),
            "expected_bonus_payout_given_trigger":ratio(metrics["weighted_bonus_units"],metrics["bonus_weight"]*100),
            "expected_fs_given_trigger":ratio(metrics["weighted_free_spins"],metrics["bonus_weight"]),
            "expansions_per_paid_round":ratio(metrics["weighted_expansions"],total),
            "expansion_fraction_of_played_fs":ratio(metrics["weighted_expansions"],metrics["weighted_free_spins"]),
            "expanding_reels_conditional":{str(k):ratio(v,metrics["weighted_expansions"]) for k,v in expansion_reels.items()},
            "base_cascade_probability":ratio(metrics["base_cascade_weight"],total),
            "any_cascade_probability":ratio(metrics["any_cascade_weight"],total),
            "average_base_evaluation_stages":ratio(metrics["weighted_base_stages"],total),
            "average_free_evaluation_stages":ratio(metrics["weighted_free_stages"],metrics["weighted_free_spins"]),
            "max_evaluation_stages":largest_stages,
            "bonus_variants":{str(n):{"books":len(ids),"probability":ratio(metrics[f"bonus_{n}_weight"],total),
                                     "one_in":total/metrics[f"bonus_{n}_weight"]} for n,ids in sorted(coverage.items())},
            "base_scatter_distribution":{str(k):ratio(v,total) for k,v in sorted(base_scatter_counts.items())},
            "base_stage_distribution":{str(k):ratio(v,total) for k,v in sorted(base_stages.items())},
            "free_stage_distribution_given_free_spin":{str(k):ratio(v,metrics["weighted_free_spins"]) for k,v in sorted(free_stages.items())},
            "buckets":{k:{**v,"probability":v["weight"]/total,
                           "rtp_contribution":v["weighted_payout_units"]/(total*100)}
                       for k,v in buckets.items()},
            "largest_payout_gaps":[{"gap":d/100,"lower":a/100,"upper":b/100} for d,a,b in gaps],
            "top_contribution_records": [{"id":i,"weight":w,"payout":p/100,"rtp_contribution":a/(total*100)}
                                          for a,i,w,p in top_records[:20]],
            "rtp_concentration_by_record_count":concentrations,
            "tail_concentration":tail,"replay_examples":categories_examples,
        }
        # Invoke production selector at both edges of EVERY ticket interval.
        # Replays already independently verified above; substitute only their
        # expensive reconstruction so this isolates the selection boundary.
        loaded,loaded_cdf,loaded_payouts=selection.load_distribution()
        ensure(loaded_cdf==cumulative and loaded_payouts==[p for _,_,p in rows],"loaded selector distribution")
        by_identity={id(spec):p for spec,(_,_,p) in zip(loaded["books"],rows)}
        original_replay=selection.replay_spec
        selection.replay_spec=lambda spec:SimpleNamespace(payout_units=by_identity[id(spec)])
        class Ticket:
            def __init__(self,value): self.value=value
            def randrange(self,bound):
                ensure(bound==total,"selector uses total final weight")
                return self.value
        try:
            for i,(left,right) in enumerate(zip([0]+cumulative[:-1],cumulative)):
                ensure(selection.select_round(Ticket(left))[0]==i,"first ticket of interval")
                ensure(selection.select_round(Ticket(right-1))[0]==i,"last ticket of interval")
        finally:
            selection.replay_spec=original_replay
        report["selector_boundary_tests"]={"intervals":len(rows),"boundary_tickets":len(rows)*2,"mismatches":0}
        # Monte Carlo check of published weights only; expensive game replay
        # has already been checked exhaustively for all selected possibilities.
        rng=random.Random(20261020)
        n=1_000_000
        mc=Counter()
        for _ in range(n):
            _,_,p=rows[bisect_right(cumulative,rng.randrange(total))]
            mc["sum"]+=p
            mc["sum_squares"]+=p*p
            mc["hit"]+=p>0
            mc["profit"]+=p>100
            mc["maximum"]+=p==CAP
        sample_mean=mc["sum"]/(n*100)
        sample_var=(mc["sum_squares"]/n-(mc["sum"]/n)**2)/10000
        hw=1.96*math.sqrt(sample_var/n)
        report["weighted_ticket_simulation"]={"rounds":n,"seed":20261020,"rtp":sample_mean,
            "normal_95_percent_interval":[sample_mean-hw,sample_mean+hw],
            "standard_error_using_exact_variance":math.sqrt(float(variance)/n),
            "z_score_using_exact_variance":(sample_mean-float(exact_mean))/math.sqrt(float(variance)/n),
            "hit_frequency":mc["hit"]/n,"net_profit_frequency":mc["profit"]/n,"maximum_hits":mc["maximum"],
            "note":"Normal interval is approximate for rare-tail distribution; exact RTP comes from weights."}
        report.update(success=True,metrics=metrics_out,unique_event_sequences=len(seen))
        with (OUT/"payout_distribution.csv").open("w",newline="",encoding="utf-8") as fp:
            writer=csv.writer(fp)
            writer.writerow(["payout_units","total_weight","probability","rtp_contribution"])
            writer.writerows((p,w,w/total,w*p/(total*100)) for p,w in sorted(payout_mass.items()))
    except Exception as exc:
        report["error"]=repr(exc)
        raise
    finally:
        report["counts"]=dict(COUNTS)
        report["elapsed_seconds"]=time.monotonic()-start
        (OUT/"independent_full_bank_results.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        print(json.dumps({"success":report["success"],"elapsed_seconds":report["elapsed_seconds"],
                          "counts":dict(COUNTS),"error":report.get("error")}),flush=True)


if __name__=="__main__":
    main()
