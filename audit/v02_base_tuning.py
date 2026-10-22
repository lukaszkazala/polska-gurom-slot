"""Compute exact sensitivity of existing base pay awards, without editing it."""
import sys, json
from itertools import product
from collections import Counter
from fractions import Fraction
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, r'D:\Kazaluka_slots\polska_gurom_phase2_v0.1')
from polska_gurom import config as c
counts = Counter(c.REEL_STRIPS[0])
coeff = Counter()
for seq in product(c.SYMBOLS, repeat=5):
    multiplicity = 1
    for s in seq: multiplicity *= counts[s]
    best = 0
    choice = None
    for target in c.REGULAR_SYMBOLS:
        n = 0
        for s in seq:
            if s not in (target, c.WILD): break
            n += 1
        if n >= 3 and c.PAYTABLE[target][n] > best:
            best = c.PAYTABLE[target][n]
            choice = (target, n)
    if choice: coeff[choice] += multiplicity
base = Fraction(45018881,60466176)
target = Fraction(735,1000)
rates = {key: Fraction(v*20, 36**5) for key,v in coeff.items()}
options = []
for a,b,d in product(range(0,11),repeat=3):
    r = base - (a*rates['L1',3] + b*rates['L2',3] + d*rates['L3',3])/100
    options.append((abs(r-target), a+b+d, a,b,d,r))
options.sort()
out = {'coefficients': {f'{s}_{n}':float(v) for (s,n),v in sorted(rates.items())},
       'best_simple_three_low_reductions': [dict(error=float(err), total_ticks=t, L1_3_reduction=a/100, L2_3_reduction=b/100,L3_3_reduction=d/100, base_rtp=float(r)) for err,t,a,b,d,r in options[:12]]}
Path(__file__).with_name('v02_base_tuning.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
