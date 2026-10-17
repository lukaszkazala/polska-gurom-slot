"""Reproducible vectorized complete-round Monte Carlo, using the core line evaluator.

Generator algorithm: numpy-PCG64-splitstreams-v2. SeedSequence(seed).spawn(4)
creates independent base-stops, FS-stops, Charge occurrence and selection streams.
Charge is sampled with exact integer ratios and selection draws occur for every
FS, so numerical game results are invariant under processing batch size.
Base stops are sampled first in chunks;
FS are sampled in chronological bonus order. Every awarded FS is simulated,
including spins after the round cap. Charge is resolved on natural FS boards.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
from hashlib import sha256
from itertools import product
from pathlib import Path
import platform
import time

import numpy as np

from .analytics import SYMBOL_ORDER
from .config import load_config
from .evaluator import evaluate_line
from .engine import evaluate_spin

ALGORITHM_VERSION = "numpy-PCG64-splitstreams-v2"
POWERS = np.array([10000, 1000, 100, 10, 1], dtype=np.int64)


@lru_cache(maxsize=8)
def _line_lut(config_hash, paytable_key):
    # The LUT is populated by the actual scalar evaluator, not a second set of
    # Wild interpretation rules. A lightweight cfg carries the required table.
    from types import SimpleNamespace
    cfg = SimpleNamespace(paytable={symbol: dict(pays) for symbol,pays in paytable_key})
    result = np.zeros(100000, dtype=np.int64)
    for index, symbols in enumerate(product(SYMBOL_ORDER, repeat=5)):
        win = evaluate_line(symbols, cfg)
        if win is not None:
            result[index] = win.payout_units
    return result


class VectorEvaluator:
    def __init__(self, cfg):
        self.cfg = cfg
        self.symbol_indices = {s:i for i,s in enumerate(SYMBOL_ORDER)}
        self.reels = [np.array([self.symbol_indices[s] for s in reel], dtype=np.int8) for reel in cfg.reels]
        self.lengths = np.array([len(reel) for reel in cfg.reels], dtype=np.int64)
        self.lines = np.array(cfg.paylines, dtype=np.int64)
        self.lut = _line_lut(cfg.config_hash, tuple((s,tuple(sorted(pays.items()))) for s,pays in cfg.paytable.items()))

    def sample_stops(self, rng, n):
        return rng.integers(0, self.lengths, size=(n,5), dtype=np.int64)

    def evaluate(self, stops, charge_reels=None):
        stops = np.asarray(stops, dtype=np.int64)
        n = len(stops)
        natural = np.empty((n,5,3), dtype=np.int8)
        for reel in range(5):
            natural[:,reel,:] = self.reels[reel][(stops[:,reel,None]+np.arange(3)) % self.lengths[reel]]
        scatter_counts = np.sum(natural == self.symbol_indices["SCATTER"], axis=(1,2))
        scatter_units = np.array([self.cfg.scatter_pays.get(k,0) for k in range(16)], dtype=np.int64)[scatter_counts]
        board = natural.copy()
        if charge_reels is not None:
            selected = np.asarray(charge_reels) >= 0
            board[np.arange(n)[selected],np.asarray(charge_reels)[selected],:] = self.symbol_indices["WILD"]
        line_units = np.zeros(n, dtype=np.int64)
        for line in self.lines:
            codes = (board[:,np.arange(5),line] * POWERS).sum(axis=1)
            line_units += self.lut[codes]
        return {"natural": natural, "board": board, "scatter_counts": scatter_counts,
                "scatter_units": scatter_units, "line_units": line_units,
                "total_units": line_units+scatter_units}


def crosscheck(cfg=None, seed=91276, samples=2048):
    """Compare identical stops and every Charge choice against scalar core."""
    cfg = cfg or load_config()
    evaluator = VectorEvaluator(cfg)
    rng = np.random.Generator(np.random.PCG64(seed))
    stops = evaluator.sample_stops(rng,samples)
    charges = np.resize(np.array([-1,1,2,3],dtype=np.int64),samples)
    vector = evaluator.evaluate(stops,charges)
    for i in range(samples):
        scalar = evaluate_spin(cfg, tuple(int(x) for x in stops[i]),
                               is_free=charges[i]>=0,
                               charge_reel=int(charges[i]) if charges[i]>=0 else None)
        natural = tuple(tuple(SYMBOL_ORDER[int(x)] for x in column) for column in vector["natural"][i])
        board = tuple(tuple(SYMBOL_ORDER[int(x)] for x in column) for column in vector["board"][i])
        assert scalar.natural_board == natural, (i,"natural")
        assert scalar.board == board, (i,"board")
        assert scalar.scatter_count == int(vector["scatter_counts"][i]), (i,"scatter")
        assert scalar.scatter_units == int(vector["scatter_units"][i]), (i,"scatter units")
        assert scalar.line_units == int(vector["line_units"][i]), (i,"line units")
        assert scalar.total_units == int(vector["total_units"][i]), (i,"total")
    return {"status":"PASS","samples":samples,"seed":seed,
            "charge_choices_reel_indices":[None,1,2,3],
            "lut_entries_from_scalar_evaluator":100000}


def _code_hash():
    root = Path(__file__).resolve().parents[1]
    digest = sha256()
    for path in sorted((root/"polska_gurom").glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _natural_stats():
    return {"spins":0,"wild_cells":0,"wild_windows":0,"wild_boards":0,
            "wild_cells_by_reel":[0]*5,"wild_windows_by_reel":[0]*5,
            "scatter_histogram":[0]*16}


def _add_natural(stats, result):
    natural = result["natural"]
    wild = natural == 8
    stats["spins"] += len(natural)
    stats["wild_cells"] += int(wild.sum())
    windows = wild.any(axis=2)
    stats["wild_windows"] += int(windows.sum())
    stats["wild_boards"] += int(windows.any(axis=1).sum())
    for index in range(5):
        stats["wild_cells_by_reel"][index] += int(wild[:,index,:].sum())
        stats["wild_windows_by_reel"][index] += int(windows[:,index].sum())
    histogram = np.bincount(result["scatter_counts"],minlength=16)
    for index,count in enumerate(histogram):
        stats["scatter_histogram"][index] += int(count)


def _finish_natural(stats):
    n = stats["spins"]
    return {**stats,
            "natural_wild_cell_frequency": stats["wild_cells"]/(15*n) if n else None,
            "natural_wild_reel_window_frequency": stats["wild_windows"]/(5*n) if n else None,
            "natural_wild_board_frequency": stats["wild_boards"]/n if n else None,
            "scatter_distribution": {str(k):count/n if n else None for k,count in enumerate(stats["scatter_histogram"])}}


def _bins(units, scale, cap):
    masks = [("0",units==0), ("(0;1)",(units>0)&(units<scale)),
             ("[1;5)",(units>=scale)&(units<5*scale)),
             ("[5;20)",(units>=5*scale)&(units<20*scale)),
             ("[20;100)",(units>=20*scale)&(units<100*scale)),
             ("[100;500)",(units>=100*scale)&(units<500*scale)),
             ("[500;1000)",(units>=500*scale)&(units<1000*scale)),
             ("[1000;5000)",(units>=1000*scale)&(units<cap)),
             ("exactly 5000",units==cap)]
    return [{"interval":label,"count":int(mask.sum()),"probability":float(mask.mean()),
             "rtp_contribution":int(units[mask].sum())/(scale*len(units))} for label,mask in masks]


def simulate(n_rounds: int, seed: int, cfg=None, batch_size: int=100000) -> dict:
    if n_rounds < 2 or batch_size<1:
        raise ValueError("n_rounds>=2 and batch_size>=1 required")
    started = time.perf_counter()
    cfg = cfg or load_config()
    evaluator = VectorEvaluator(cfg)
    base_seed, free_seed, charge_seed, selection_seed = np.random.SeedSequence(seed).spawn(4)
    base_rng = np.random.Generator(np.random.PCG64(base_seed))
    free_rng = np.random.Generator(np.random.PCG64(free_seed))
    charge_rng = np.random.Generator(np.random.PCG64(charge_seed))
    selection_rng = np.random.Generator(np.random.PCG64(selection_seed))
    base_total = np.zeros(n_rounds,dtype=np.int64)
    base_scatter = np.zeros(n_rounds,dtype=np.int64)
    fs_counts = np.zeros(n_rounds,dtype=np.int64)
    base_stats,free_stats = _natural_stats(),_natural_stats()
    award_lookup = np.array([cfg.fs_awards.get(k,0) for k in range(16)],dtype=np.int64)
    for start in range(0,n_rounds,batch_size):
        end = min(start+batch_size,n_rounds)
        result = evaluator.evaluate(evaluator.sample_stops(base_rng,end-start))
        base_total[start:end] = result["total_units"]
        base_scatter[start:end] = result["scatter_units"]
        fs_counts[start:end] = award_lookup[result["scatter_counts"]]
        _add_natural(base_stats,result)
    owners = np.repeat(np.arange(n_rounds),fs_counts)
    free_count = len(owners)
    fs_total = np.zeros(free_count,dtype=np.int64)
    fs_scatter = np.zeros(free_count,dtype=np.int64)
    charges_by_reel = np.zeros(5,dtype=np.int64)
    for start in range(0,free_count,batch_size):
        end = min(start+batch_size,free_count)
        count = end-start
        stops = evaluator.sample_stops(free_rng,count)
        has_charge = charge_rng.integers(0,cfg.charge_probability.denominator,size=count) < cfg.charge_probability.numerator
        charges = np.full(count,-1,dtype=np.int64)
        weights = np.array(cfg.charge_weights,dtype=np.int64)
        selected_reels = 1+np.searchsorted(np.cumsum(weights),selection_rng.integers(0,int(weights.sum()),size=count),side="right")
        charges[has_charge] = selected_reels[has_charge]
        result = evaluator.evaluate(stops,charges)
        fs_total[start:end] = result["total_units"]
        fs_scatter[start:end] = result["scatter_units"]
        for index in (1,2,3):
            charges_by_reel[index] += int((charges==index).sum())
        _add_natural(free_stats,result)
    raw_bonus = np.zeros(n_rounds,dtype=np.int64)
    raw_bonus_scatter = np.zeros(n_rounds,dtype=np.int64)
    np.add.at(raw_bonus,owners,fs_total)
    np.add.at(raw_bonus_scatter,owners,fs_scatter)
    raw_total = base_total+raw_bonus
    paid_base = np.minimum(base_total,cfg.cap_units)
    paid_total = np.minimum(raw_total,cfg.cap_units)
    paid_bonus = paid_total-paid_base
    # Attribute each spin's credit in chronological order: lines, then scatter.
    paid_base_scatter = np.minimum(base_scatter,np.maximum(cfg.cap_units-(base_total-base_scatter),0))
    paid_free_scatter = np.zeros(free_count,dtype=np.int64)
    if free_count:
        cumulative = np.cumsum(fs_total)
        first = np.r_[0,np.flatnonzero(np.diff(owners))+1]
        before_group = np.repeat(np.r_[0,cumulative[first[1:]-1]],fs_counts[fs_counts>0])
        before_spin = cumulative-fs_total-before_group+base_total[owners]
        after_lines = before_spin+(fs_total-fs_scatter)
        paid_free_scatter = np.minimum(fs_scatter,np.maximum(cfg.cap_units-after_lines,0))
    scale = cfg.scale
    x = paid_total.astype(float)/scale
    raw_x = raw_total.astype(float)/scale
    sample_variance = float(x.var(ddof=1))
    standard_error = (sample_variance/n_rounds)**.5
    mean = float(x.mean())
    bonus_mask = fs_counts>0
    n_bonus = int(bonus_mask.sum())
    bonus_x = paid_bonus[bonus_mask].astype(float)/scale
    raw_bonus_x = raw_bonus[bonus_mask].astype(float)/scale
    charge_count = int(charges_by_reel.sum())
    rtp = lambda values: int(values.sum())/(scale*n_rounds)
    return {
        "method":"MONTE CARLO", "status":"PROTOTYPE / NOT MATH-FROZEN",
        "algorithm_version":ALGORITHM_VERSION,"rng":"numpy.random.Generator(PCG64)",
        "seed":seed,"seed_streams":{"base_stops_spawn_key":list(base_seed.spawn_key),"free_stops_spawn_key":list(free_seed.spawn_key),
                                    "charge_occurrence_spawn_key":list(charge_seed.spawn_key),"charge_selection_spawn_key":list(selection_seed.spawn_key)},
        "batch_size":batch_size,"python_version":platform.python_version(),"numpy_version":np.__version__,
        "code_sha256":_code_hash(),"config_version":cfg.version,"config_hash":cfg.config_hash,
        "paid_rounds":n_rounds,"total_bet":n_rounds,"scale":scale,
        "total_payout_units":int(paid_total.sum()),"total_payout":int(paid_total.sum())/scale,
        "raw_total_payout_units":int(raw_total.sum()),"elapsed_seconds":time.perf_counter()-started,
        "rtp_post_cap":{"total":rtp(paid_total),"base":rtp(paid_base),"bonus":rtp(paid_bonus),
                        "scatter":(int(paid_base_scatter.sum())+int(paid_free_scatter.sum()))/(scale*n_rounds)},
        "rtp_pre_cap":{"total":rtp(raw_total),"base":rtp(base_total),"bonus":rtp(raw_bonus),
                       "scatter":(int(base_scatter.sum())+int(raw_bonus_scatter.sum()))/(scale*n_rounds)},
        "scatter_attribution":"Chronological spins; within each spin line credits precede natural-board scatter credits. Base/bonus totals use chronological cap allocation.",
        "sample_variance":sample_variance,"sample_standard_deviation":sample_variance**.5,
        "raw_sample_variance":float(raw_x.var(ddof=1)),"rtp_standard_error":standard_error,
        "rtp_95pct_ci":[mean-1.959963984540054*standard_error,mean+1.959963984540054*standard_error],
        "ci_method":"Normal CLT interval using full paid-round sample variance (ddof=1); rare unobserved large payouts can make nominal coverage unreliable, especially 10k. Not proof of exact RTP or tail absence.",
        "bonus_count":n_bonus,"bonus_frequency":n_bonus/n_rounds,
        "bonus_mean_interval_paid_rounds":n_rounds/n_bonus if n_bonus else None,
        "mean_bonus_payout_given_bonus":float(bonus_x.mean()) if n_bonus else None,
        "mean_raw_bonus_payout_given_bonus":float(raw_bonus_x.mean()) if n_bonus else None,
        "free_spin_count":free_count,"mean_free_spins_given_bonus":free_count/n_bonus if n_bonus else None,
        "mean_free_spins_per_paid_round":free_count/n_rounds,
        "charge_count":charge_count,"charge_frequency_per_free_spin":charge_count/free_count if free_count else None,
        "mean_charge_count_per_bonus":charge_count/n_bonus if n_bonus else None,
        "charge_reel_selection_counts_1_based":{str(index+1):int(charges_by_reel[index]) for index in range(5)},
        "charge_reel_selection_probabilities_given_charge":{str(index+1):int(charges_by_reel[index])/charge_count if charge_count else None for index in range(5)},
        "natural_board_stats":{"base":_finish_natural(base_stats),"free_spins":_finish_natural(free_stats)},
        "frequency":{"hit_base":float((base_total>0).mean()),"hit_complete_round":float((paid_total>0).mean()),
                     "payout_gt_bet":float((paid_total>scale).mean()),
                     "positive_payout_lt_bet":float(((paid_total>0)&(paid_total<scale)).mean()),
                     "exact_stake_return":float((paid_total==scale).mean())},
        "hit_target_definition":"25-30% target interpreted as base spin payout>0, before awarded FS",
        "paid_round_payout_bins":_bins(paid_total,scale,cfg.cap_units),
        "bonus_paid_tail_probabilities_given_bonus":({"lt_1":float((bonus_x<1).mean()),
                         **{"gt_"+str(threshold):float((bonus_x>threshold).mean()) for threshold in (20,100,500,1000)}} if n_bonus else None),
        "maximum_observed_paid_round_payout":int(paid_total.max())/scale,
        "maximum_observed_raw_round_payout":int(raw_total.max())/scale,
        "maximum_observed_paid_bonus_payout":float(bonus_x.max()) if n_bonus else None,
        "cap_reached_count":int((raw_total>=cfg.cap_units).sum()),
        "cap_reduction_count":int((raw_total>cfg.cap_units).sum()),
        "cap_reduction_units":int((raw_total-paid_total).sum()),
        "cap_reduction_rtp":rtp(raw_total-paid_total),
        "all_awarded_free_spins_played":True,
        "accounting_assertions": {"paid_base_plus_bonus_equals_paid_total":bool(np.all(paid_base+paid_bonus==paid_total)),
                                  "bins_cover_all_paid_rounds":sum(row["count"] for row in _bins(paid_total,scale,cfg.cap_units))==n_rounds,
                                  "free_spins_equal_awards":free_count==int(fs_counts.sum())}
    }


def crosscheck_batch_reproducibility(cfg=None, seed=66251, rounds=10000):
    """Verify full statistics repeat for same seed across different batch sizes."""
    cfg = cfg or load_config()
    first = simulate(rounds,seed,cfg,batch_size=1000)
    second = simulate(rounds,seed,cfg,batch_size=333)
    for result in (first,second):
        result.pop("elapsed_seconds")
        result.pop("batch_size")
    assert first == second, "Numerical simulation results depend on batch size"
    return {"status":"PASS","rounds":rounds,"seed":seed,"batch_sizes":[1000,333],
            "comparison":"All result fields identical except processing batch size and elapsed time"}
