"""Run real independent sampled-book draws against the published Stake LUT.

Each round consumes one unbiased NumPy integer ticket in [0, sum(weights)).
An exact uint64 cumulative table maps every ticket to the published outcome.
No multinomial shortcut or theoretical RTP is substituted for sampled draws.
"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
from scipy.stats import beta, binom

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DEFAULT_LUT = ROOT / 'test-interface' / 'stake_math' / 'lookUpTable_base_0.csv'
SCALE = 100

def sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_lut(path):
    rows = []
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        for lineno, row in enumerate(csv.reader(f), 1):
            if not row: continue
            if len(row) != 3: raise ValueError(f'LUT row {lineno}: expected id,weight,payout')
            try: values = tuple(map(int, row))
            except ValueError: raise ValueError(f'LUT row {lineno}: all fields must be integers')
            rows.append(values)
    if not rows: raise ValueError('Empty LUT')
    ids, weights, payouts = map(list, zip(*rows))
    if len(set(ids)) != len(ids): raise ValueError('Duplicate outcome ids')
    if any(i < 0 for i in ids): raise ValueError('Negative outcome id')
    if any(w < 0 for w in weights): raise ValueError('Negative outcome weight')
    if any(p < 0 or p > 500000 or p % 10 for p in payouts):
        raise ValueError('Payout must be 0..500000 integer cents, in steps of 10')
    total = sum(weights)
    if not 0 < total < 2**64: raise ValueError('Weight sum outside uint64 range')
    weights_a = np.asarray(weights, dtype=np.uint64)
    payout_a = np.asarray(payouts, dtype=np.int64)
    cdf = np.cumsum(weights_a, dtype=np.uint64)
    assert int(cdf[-1]) == total
    # Independently check exact transition tickets around every CDF boundary.
    positive = np.flatnonzero(weights_a)
    left = cdf[positive] - weights_a[positive]
    right = cdf[positive] - np.uint64(1)
    assert np.array_equal(np.searchsorted(cdf, left, side='right'), positive)
    assert np.array_equal(np.searchsorted(cdf, right, side='right'), positive)
    # A separate linear exact oracle validates random tickets against bisect.
    from bisect import bisect_right
    probes = np.random.default_rng(752719).integers(0, total, size=10000, dtype=np.uint64)
    cdf_list = cdf.tolist()
    assert np.array_equal(np.searchsorted(cdf, probes, side='right'),
                          np.asarray([bisect_right(cdf_list, int(x)) for x in probes]))
    mean = Fraction(sum(w*p for w, p in zip(weights, payouts)), total*SCALE)
    second = Fraction(sum(w*p*p for w, p in zip(weights, payouts)), total*SCALE*SCALE)
    var = second - mean*mean
    return ids, weights, payout_a, cdf, total, mean, var

def rate_interval(count, n, confidence=.95):
    alpha = 1-confidence
    low = 0.0 if count == 0 else float(beta.ppf(alpha/2, count, n-count+1))
    high = 1.0 if count == n else float(beta.ppf(1-alpha/2, count+1, n-count))
    return [low, high]

def run(lut, out_dir, sizes, seeds, chunk):
    out_dir.mkdir(parents=True, exist_ok=True)
    source_hash = sha256(__file__)
    lut_hash = sha256(lut)
    ids, weights, payouts, cdf, weight_total, exact_mean, exact_var = load_lut(lut)
    probability_hit = Fraction(sum(w for w,p in zip(weights,payouts) if p>0),weight_total)
    cap_probability = Fraction(sum(w for w,p in zip(weights,payouts) if p==500000),weight_total)
    report = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Independent actual sampled draws from the final published weighted payout table; no animation or natural reel-generation coverage is claimed',
        'method': 'One PCG64 uniform uint64 integer ticket per paid round, exact uint64 CDF, numpy.searchsorted(side=right), outcome histogram checked against generated draw count',
        'numpy_version': np.__version__, 'source_sha256': source_hash,
        'lut_path': str(lut.resolve()), 'lut_sha256': lut_hash,
        'outcomes': len(ids), 'weight_total': weight_total,
        'payout_unit': 'one hundredth of total bet',
        'quantization_step_units': 10,
        'cdf_validation': {'boundary_tickets_checked': 2*sum(w>0 for w in weights),
                           'independent_bisect_probes': 10000, 'result': 'passed'},
        'reference': {'exact_rtp_fraction': str(exact_mean), 'rtp': float(exact_mean),
                      'exact_variance_fraction': str(exact_var), 'variance': float(exact_var),
                      'standard_deviation': math.sqrt(float(exact_var)),
                      'hit_frequency': float(probability_hit),
                      'max_win': 5000, 'max_win_probability_fraction': str(cap_probability),
                      'max_win_probability': float(cap_probability)},
        'runs': []}
    progress_path = out_dir / 'progress.jsonl'
    progress_path.write_text('', encoding='utf-8')
    bucket_bounds = [0, 1, 100, 500, 2000, 10000, 50000, 100000, 500000, 500001]
    bucket_names = ['0x', '>0x-1x', '1x-5x', '5x-20x', '20x-100x', '100x-500x', '500x-1000x', '1000x-5000x', '5000x']
    for n, seed in zip(sizes, seeds):
        rng = np.random.Generator(np.random.PCG64(seed))
        initial_state_hash = hashlib.sha256(json.dumps(rng.bit_generator.state, sort_keys=True).encode()).hexdigest()
        counts = np.zeros(len(ids), dtype=np.int64)
        drawn = 0
        next_log = 5_000_000
        start = time.perf_counter()
        while drawn < n:
            size = min(chunk, n-drawn)
            tickets = rng.integers(0, weight_total, size=size, dtype=np.uint64)
            indices = np.searchsorted(cdf, tickets, side='right')
            assert len(indices) == size and (indices >= 0).all() and (indices < len(ids)).all()
            counts += np.bincount(indices, minlength=len(ids))
            drawn += size
            if drawn >= next_log or drawn == n:
                event = {'run_rounds': n, 'seed': seed, 'actual_draws_completed': drawn,
                         'elapsed_seconds': time.perf_counter()-start}
                with progress_path.open('a', encoding='utf-8') as f: f.write(json.dumps(event)+'\n')
                print(json.dumps(event), flush=True)
                next_log += 5_000_000
        elapsed = time.perf_counter()-start
        assert int(counts.sum()) == n == drawn
        # Python ints preserve exact accounting even for squared maximum payouts.
        total_units = sum(int(k)*int(p) for k,p in zip(counts,payouts))
        square_units = sum(int(k)*int(p)*int(p) for k,p in zip(counts,payouts))
        empirical_rtp = total_units/(n*SCALE)
        empirical_variance = (square_units*n-total_units*total_units)/(n*n*SCALE*SCALE)
        se = math.sqrt(float(exact_var)/n)
        half95, half99 = 1.959963984540054*se, 2.5758293035489004*se
        cap_hits = int(counts[payouts==500000].sum())
        hits = int(counts[payouts>0].sum())
        hist_path = out_dir / f'outcome_counts_{n}.csv'
        with hist_path.open('w',newline='',encoding='utf-8') as f:
            writer=csv.writer(f);writer.writerow(['id','weight','payout_units','observed_count'])
            writer.writerows((i,w,int(p),int(k)) for i,w,p,k in zip(ids,weights,payouts,counts))
        buckets = {}
        for name,lo,hi in zip(bucket_names,bucket_bounds,bucket_bounds[1:]):
            mask=(payouts>=lo)&(payouts<hi)
            observed=int(counts[mask].sum())
            expected=Fraction(sum(w for w,m in zip(weights,mask) if m),weight_total)
            buckets[name]={'observed_count':observed,'observed_frequency':observed/n,
                           'exact_probability':str(expected),'expected_count':float(expected*n)}
        assert sum(v['observed_count'] for v in buckets.values())==n
        cp=float(cap_probability)
        result={'rounds':n,'seed':seed,'actual_integer_tickets_drawn':drawn,
                'accounted_outcome_counts':int(counts.sum()),'total_payout_units':total_units,
                'squared_payout_units_sum':square_units,'rtp':empirical_rtp,
                'empirical_variance':empirical_variance,'reference_standard_error':se,
                'normal_95_interval_around_observed':[empirical_rtp-half95,empirical_rtp+half95],
                'normal_99_interval_around_observed':[empirical_rtp-half99,empirical_rtp+half99],
                'rtp_difference_from_reference':empirical_rtp-float(exact_mean),
                'z_score':(empirical_rtp-float(exact_mean))/se if se else 0,
                'within_95_normal_reference_band':abs(empirical_rtp-float(exact_mean))<=half95,
                'within_99_normal_reference_band':abs(empirical_rtp-float(exact_mean))<=half99,
                'hit_count':hits,'hit_frequency':hits/n,
                'hit_frequency_clopper_pearson_95':rate_interval(hits,n),
                'max_observed_payout_units':int(payouts[counts>0].max()),
                'max_win_hits':cap_hits,'max_win_expected_hits':n*cp,
                'max_win_binomial_95_prediction_count_interval':[int(binom.ppf(.025,n,cp)),int(binom.ppf(.975,n,cp))],
                'max_win_observed_rate_clopper_pearson_95':rate_interval(cap_hits,n),
                'win_buckets':buckets,'elapsed_seconds':elapsed,
                'final_rng_state_sha256':hashlib.sha256(json.dumps(rng.bit_generator.state,sort_keys=True).encode()).hexdigest(),
                'initial_rng_state_sha256':initial_state_hash,
                'outcome_histogram_file':hist_path.name,'outcome_histogram_sha256':sha256(hist_path)}
        report['runs'].append(result)
        (out_dir/'weighted_simulation_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    assert sha256(lut)==lut_hash, 'LUT changed during simulation'
    report['total_actual_draws']=sum(r['actual_integer_tickets_drawn'] for r in report['runs'])
    report['immutable_lut_confirmed']=True
    report['interval_note']='Normal intervals describe Monte Carlo sampling uncertainty around the exact finite weighted distribution. 95% intervals may miss the reference by chance; passing a simulation is not certification.'
    (out_dir/'weighted_simulation_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'report':str(out_dir/'weighted_simulation_report.json'),
                      'total_actual_draws':report['total_actual_draws'],
                      'runs':[{k:r[k] for k in ['rounds','rtp','z_score','max_win_hits','elapsed_seconds']} for r in report['runs']]},indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--lut',type=Path,default=DEFAULT_LUT)
    p.add_argument('--out',type=Path,default=HERE/'weighted_results')
    p.add_argument('--sizes',type=int,nargs='+',default=[10_000_000,50_000_000,100_000_000])
    p.add_argument('--seeds',type=int,nargs='+',default=[2026101901,2026101902,2026101903])
    p.add_argument('--chunk',type=int,default=1_000_000)
    a=p.parse_args()
    if len(a.sizes)!=len(a.seeds) or len(set(a.seeds))!=len(a.seeds): p.error('Provide one distinct seed per run')
    if any(n<=0 for n in a.sizes) or not 0<a.chunk<=1_000_000: p.error('Positive sizes and chunk 1..1000000 required')
    run(a.lut,a.out,a.sizes,a.seeds,a.chunk)
