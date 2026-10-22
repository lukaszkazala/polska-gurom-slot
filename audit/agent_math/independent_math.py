"""Independent integer/fraction reference model; never imports game or theory."""
import os
import sys
import json
from itertools import product
from fractions import Fraction
from collections import Counter
import numpy as np

sys.dont_write_bytecode = True
sys.path.insert(0, r'D:\Kazaluka_slots\polska_gurom_phase2_v0.1')
from polska_gurom import config as c

ids = {s: i for i,s in enumerate(c.SYMBOLS)}
wild = ids[c.WILD]
scat = ids[c.SCATTER]
pay = {ids[s]: {n: round(v*20) for n,v in row.items()} for s,row in c.PAYTABLE.items()}

def score(sequence):
    # Every payable prefix: after removing Wild it must contain <=1 regular type.
    # Select the largest award over all prefix lengths / regular interpretations.
    awards = [0]
    for length in (3,4,5):
        real = set(sequence[:length]) - {wild}
        if not real:
            awards.extend(row[length] for row in pay.values())
        elif len(real) == 1 and next(iter(real)) in pay:
            awards.append(pay[next(iter(real))][length])
    return max(awards)

lut = np.fromiter((score(s) for s in product(range(10), repeat=5)), dtype=np.int16)
counts = np.array([Counter(r) for r in c.REEL_STRIPS],dtype=object)

def exact_line(forced=None):
    numerator = 0
    for sequence in product(*[([wild] if i==forced else range(10)) for i in range(5)]):
        multiplicity = 1
        for r,s in enumerate(sequence):
            if r != forced:
                multiplicity *= counts[r][c.SYMBOLS[s]]
        numerator += score(sequence)*multiplicity
    return Fraction(numerator,20*36**(5-(forced is not None)))

base_line = exact_line()*20
expanded = [exact_line(i)*20 for i in (1,2,3)]
scatter_probs = {k: Fraction(__import__('math').comb(5,k)*11**(5-k),12**5) for k in range(6)}
scatter_ev = sum(p*Fraction(str(c.SCATTER_PAYTABLE.get(k,0))) for k,p in scatter_probs.items())
freq = sum(p for k,p in scatter_probs.items() if k>=3)
fs_unconditional = sum(p*c.FREE_SPINS.get(k,0) for k,p in scatter_probs.items())
free_ev = base_line*Fraction(3,4)+sum(expanded)/12+scatter_ev
rtp = base_line+scatter_ev+fs_unconditional*free_ev
out = {'base_line_rtp':float(base_line),'expanded_line_by_reel':list(map(float,expanded)),
       'expanded_line_average':float(sum(expanded)/3),'scatter_rtp':float(scatter_ev),
       'bonus_frequency':float(freq),'frequency_reciprocal':float(1/freq),
       'expected_fs_unconditional':float(fs_unconditional),'average_fs_per_bonus':float(fs_unconditional/freq),
       'free_spin_ev':float(free_ev),'bonus_ev_per_bonus':float(fs_unconditional*free_ev/freq),
       'bonus_rtp':float(fs_unconditional*free_ev),'total_rtp':float(rtp),
       'rtp_fraction':str(rtp),'rtp_with_expansion_100pct':float(base_line+scatter_ev+fs_unconditional*(sum(expanded)/3+scatter_ev)),
       'required_expansion_probability_for_96pct':float((Fraction(96,100)-(base_line+scatter_ev)-fs_unconditional*(base_line+scatter_ev))/(fs_unconditional*(sum(expanded)/3-base_line)))}
print(json.dumps(out,indent=2),flush=True)

# All rotations have exactly the same window set. Use BASE windows for each reel;
# reported stop positions are BASE-equivalent, then convert to real strip stops.
strip = c.REEL_STRIPS[0]
windows = np.array([[ids[strip[(st+row)%36]] for row in range(3)] for st in range(36)],dtype=np.int8)
scatter_in_window = (windows==scat).sum(axis=1)
digits = np.array(list(product(range(36),repeat=4)),dtype=np.int8)
sp_lookup = np.array([round(c.SCATTER_PAYTABLE.get(k,0)*20) for k in range(6)],dtype=np.int16)

def payouts_for_stops(stops,forced=None):
    payout = np.zeros(len(stops),dtype=np.int32)
    for line in c.PAYLINES:
        index = np.zeros(len(stops),dtype=np.int32)
        for reel,row in enumerate(line):
            index *= 10
            index += wild if reel==forced else windows[stops[:,reel],row]
        payout += lut[index]
    sc = scatter_in_window[stops].sum(axis=1)
    return payout+sp_lookup[sc],sc

def maximize_base():
    maxima = [-1]*6
    winners = [None]*6
    for st in range(36):
        stops = np.column_stack((np.full(len(digits),st,dtype=np.int8),digits))
        p,sc = payouts_for_stops(stops)
        for k in range(6):
            masked = np.where(sc==k,p,-1)
            i = int(masked.argmax())
            if int(masked[i]) > maxima[k]:
                maxima[k]=int(masked[i]); winners[k]=stops[i].tolist()
    return maxima,winners

base_max,base_witness = maximize_base()
print(json.dumps({'base_maximum_by_scatter':[x/20 for x in base_max], 'base_witness_base_equivalent_stops':base_witness}),flush=True)
fs_maxima=[]; fs_witness=[]
for forced in (1,2,3):
    # Choose a scatter-containing natural window for the overwritten reel. It
    # cannot reduce line wins and can only increase Scatter payout.
    forced_stop = int(np.flatnonzero(scatter_in_window)[0])
    stops=np.insert(digits,forced,forced_stop,axis=1)
    p,sc=payouts_for_stops(stops,forced)
    i=int(p.argmax())
    fs_maxima.append(int(p[i])); fs_witness.append(stops[i].tolist())
out.update({'base_maximum_by_scatter':[x/20 for x in base_max],
            'base_witness_base_equivalent_stops':base_witness,
            'free_spin_expanded_maximum_by_reel':[x/20 for x in fs_maxima],
            'free_spin_witness_base_equivalent_stops':fs_witness})
fs_max=max(base_max+fs_maxima)
out['free_spin_maximum']=fs_max/20
round_candidates=[base_max[k]+c.FREE_SPINS.get(k,0)*fs_max for k in range(6)]
out['round_maximum_by_trigger_scatter']=[x/20 for x in round_candidates]
out['round_maximum']=max(round_candidates)/20
with open(os.path.join(os.path.dirname(__file__),'independent_math_results.json'),'w') as f:
    json.dump(out,f,indent=2)
print(json.dumps(out,indent=2),flush=True)
