"""Exact bonus frequencies and observed counts from the new immutable LUT."""
from collections import Counter
import csv
from fractions import Fraction
import hashlib
import io
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT/'audit/stake_cascades_v04/dependencies'),str(ROOT/'test-interface/engine')]
import zstandard
from polska_gurom import config

folder = ROOT/'test-interface/stake_math'
lut = folder/'lookUpTable_base_0.csv'
rows = [tuple(map(int,row)) for row in csv.reader(lut.open(encoding='utf-8'))]
total = sum(w for _,w,_ in rows)
weights = {i:w for i,w,_ in rows}
award_by_id = {}
type_counts, masses, scatter_counts = Counter(), Counter(), {}
bonus_credits = expanded_mass = 0
with (folder/'books_base.jsonl.zst').open('rb') as src:
    with zstandard.ZstdDecompressor().stream_reader(src) as reader:
        for line in io.TextIOWrapper(reader,encoding='utf-8'):
            book=json.loads(line)
            data=book['events'][0]['data']
            award=data['base']['free_spins_awarded']
            i=book['id'];w=weights[i]
            award_by_id[i]=award
            if award:
                type_counts[award]+=1;masses[award]+=w
                scatter_counts[award]=data['base']['scatter_count']
                bonus_credits+=w*data['bonus_payout_units']
                if any(s['expanding_reel'] is not None for s in data['free_spins']):expanded_mass+=w

bonus_weight=sum(masses.values());p=bonus_weight/total
types=[]
for scatters,fs in config.FREE_SPINS.items():
    mass=masses[fs]
    types.append({'scatters':scatters,'free_spins':fs,'books':type_counts[fs],'weight':mass,'probability_fraction':str(Fraction(mass,total)),'probability':mass/total,'one_in':total/mass if mass else None,'share_of_bonuses':mass/bonus_weight})
weighted=json.loads((HERE/'weighted_results/weighted_simulation_report.json').read_text(encoding='utf-8'))
assert weighted['lut_sha256']==hashlib.sha256(lut.read_bytes()).hexdigest()
runs=[]
for run in weighted['runs']:
    counts=Counter()
    histogram=HERE/'weighted_results'/run['outcome_histogram_file']
    with histogram.open(encoding='utf-8',newline='') as src:
        for row in csv.DictReader(src):counts[award_by_id[int(row['id'])]]+=int(row['observed_count'])
    n=run['rounds'];bonuses=sum(c for fs,c in counts.items() if fs)
    assert sum(counts.values())==n
    runs.append({'rounds':n,'bonuses':bonuses,'bonus_frequency':bonuses/n,'one_in':n/bonuses,'by_free_spins':{str(k):v for k,v in sorted(counts.items())},'expected_bonuses':n*p,'binomial_z':(bonuses-n*p)/math.sqrt(n*p*(1-p)),'histogram_file':str(histogram.relative_to(ROOT)).replace('\\','/'),'seed':run['seed'],'twelve_fs_count':counts[12],'expected_twelve_fs_count':n*masses[12]/total})

natural=Fraction(1,248832)
report={'scope':'Exact repaired finite weighted complete-round model; current new10/50/100M sampled tickets, not historical frequencies','math_version':config.MATH_VERSION,'lut_sha256':weighted['lut_sha256'],'total_weight':total,'bonus_weight':bonus_weight,'probability_fraction':str(Fraction(bonus_weight,total)),'bonus_probability':p,'mean_paid_rounds_to_bonus':1/p,'waiting_time_quantiles':{str(q):math.ceil(math.log1p(-q)/math.log1p(-p)) for q in [.5,.9,.95,.99]},'bonus_types':types,'series_probabilities':[{'paid_rounds':n,'expected_bonus_count':n*p,'probability_at_least_one_bonus':-math.expm1(n*math.log1p(-p)),'probability_no_bonus':math.exp(n*math.log1p(-p))} for n in [25,50,100,200,500,1000]],'previous_simulations_aggregated':runs,'mean_awarded_free_spins_per_bonus':sum(fs*m for fs,m in masses.items())/bonus_weight,'bonus_with_at_least_one_expansion_probability':expanded_mass/bonus_weight,'conditional_mean_credited_free_spin_return_x_bet':bonus_credits/(100*bonus_weight),'free_spin_rtp_contribution':bonus_credits/(100*total),'missing_declared_bonus_types':[t for t in types if not t['books'] or not t['weight']],'natural_five_scatter_probability_fraction':str(natural),'probability_missing_five_scatter_in_100k':math.exp(100000*math.log1p(-float(natural))),'note':'Independent paid rounds only; free spins and cascades are parts of one paid round. Published12FS probability is quantized to integer weights. Earlier simulation reports remain historical.'}
assert not report['missing_declared_bonus_types']
assert report['bonus_weight']==4_969_935_540 and masses[12]==4_018_776
(HERE/'bonus_frequency.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'types':types,'runs':[{k:r[k] for k in ['rounds','bonuses','twelve_fs_count','expected_twelve_fs_count']} for r in runs]},ensure_ascii=False))
