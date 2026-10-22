"""Recheck existing evidence freshness and summarize bonus/tail limits only."""
from pathlib import Path
from fractions import Fraction
from collections import defaultdict
import csv
import hashlib
import importlib.util
import json
import math
import sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
spec = importlib.util.spec_from_file_location('independent_audit', OUT / 'independent_full_bank.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
report = json.loads((OUT / 'independent_full_bank_results.json').read_text())
assert report['success'] is True
hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == saved
          for name,saved in report['source_sha256'].items()}
assert all(hashes.values())
rows = [tuple(map(int,r)) for r in csv.reader((audit.GAME / 'stake_math/lookUpTable_base_0.csv').open())]
manifest,_,payouts = audit.selection.load_distribution()
total = sum(w for _,w,_ in rows)
mean = Fraction(sum(w*p for _,w,p in rows),total*100)
var = Fraction(sum(w*p*p for _,w,p in rows),total*10000)-mean**2
assert str(mean)==report['metrics']['exact_rtp']
assert str(var)==report['metrics']['variance_fraction']
groups = {}
for fs,coverage in manifest['bonus_coverage'].items():
    data = []
    for i in coverage['book_ids']:
        result = audit.selection.replay_spec(manifest['books'][i])
        data.append((i,rows[i][1],result))
    mass = sum(w for _,w,_ in data)
    groups[fs] = {
        'books':len(data),'probability':mass/total,
        'min_complete_round_bet_multiple':min(r.payout_units for _,_,r in data)/100,
        'max_complete_round_bet_multiple':max(r.payout_units for _,_,r in data)/100,
        'min_bonus_only_bet_multiple':min(r.bonus_payout_units for _,_,r in data)/100,
        'max_bonus_only_bet_multiple':max(r.bonus_payout_units for _,_,r in data)/100,
        'conditional_mean_round_bet_multiple':sum(w*r.payout_units for _,w,r in data)/(mass*100),
        'conditional_mean_bonus_bet_multiple':sum(w*r.bonus_payout_units for _,w,r in data)/(mass*100),
        'expansion_fraction':sum(w*r.expansions for _,w,r in data)/sum(w*len(r.free_spins) for _,w,r in data),
        'maximum_round_ids':[i for i,_,r in data if r.payout_units==500000],
    }
examples = json.loads((OUT / 'ten_examples.json').read_text())
for example in examples:
    calculated = audit.expected_wins(example['base_initial_grid'],1)
    assert calculated==example['first_stage_line_wins']
    assert example['total_credited_units']==payouts[example['book_id']]
    assert example['total_credited_units']==example['base_credited_units']+example['bonus_credited_units']
    assert example['bonus_credited_units']==sum(example['free_spin_credits'])
forced = json.loads((OUT / 'forced_and_sample_cascade_checks.json').read_text())
assert forced['success'] and all(forced['forced_cases'].values())
mc = {}
pmax = Fraction(1,8000000)
for n in (100000,1000000):
    mc[str(n)] = {'exact_standard_error_percentage_points':100*math.sqrt(float(var)/n),
                 'normal_95_half_width_percentage_points':196*math.sqrt(float(var)/n),
                 'probability_of_zero_maximum_hits':math.exp(n*math.log1p(-float(pmax))),
                 'expected_maximum_hits':n*float(pmax)}
result = {
    'success':True,'scope':'No repeat of exhaustive bank; freshness, exact LUT totals, all bonus records, ten examples.',
    'current_artifact_hashes_match_original_audit':hashes,
    'oracle_review':'All six legal length >=3 intervals enumerated independently; regular/Wild intersection and highest award, leftmost tie break. Paytable is strictly increasing per regular symbol, so shorter subsets cannot defeat a matching longer run.',
    'fresh_lut_rtp_fraction':str(mean),'fresh_lut_variance_fraction':str(var),
    'bonus_groups':groups,'ten_example_ids_recalculated':[e['book_id'] for e in examples],
    'existing_forced_check_success':forced['success'],
    'existing_forced_sample_is_natural_candidates_not_weighted_rgs':True,
    'monte_carlo_uncertainty':mc,
    'rounds_for_95_percent_chance_of_at_least_one_maximum':math.ceil(math.log(.05)/math.log1p(-float(pmax))),
    'limitations':['Audit establishes payout conformance to explicit local spec, not regulatory approval.',
                   'Reel-window reachability uses configured strips; final outcome probabilities use final book weights.',
                   'Normal confidence intervals approximate a rare-tail distribution and cannot establish rare feature support.']}
(OUT / 'evidence_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
