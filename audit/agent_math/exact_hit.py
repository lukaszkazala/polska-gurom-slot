import sys,json,math,os
from itertools import product
from fractions import Fraction
from collections import Counter
sys.dont_write_bytecode=True
sys.path.insert(0,r'D:\Kazaluka_slots\polska_gurom_phase2_v0.1')
from polska_gurom import config as c
strip=c.REEL_STRIPS[0]
windows=[tuple(strip[(st+row)%36] for row in range(3)) for st in range(36)]
prefixes=set(line[:3] for line in c.PAYLINES)
nohit_sc=Counter();hit=0
for stops in product(range(36),repeat=3):
    linehit=False
    for rows in prefixes:
        syms={windows[stops[r]][rows[r]] for r in range(3)}-{c.WILD}
        if not syms or (len(syms)==1 and next(iter(syms)) in c.REGULAR_SYMBOLS):
            linehit=True;break
    if linehit:hit+=1
    else:nohit_sc[sum(c.SCATTER in windows[s] for s in stops)]+=1
line_prob=Fraction(hit,36**3)
scatter_extra=sum(Fraction(count,36**3)*sum(Fraction(math.comb(2,k)*11**(2-k),12**2) for k in range(3-sc,3)) for sc,count in nohit_sc.items() if sc>=1)
out={'unique_line_prefixes':len(prefixes),'line_hit_numerator_over_36cubed':hit,'no_line_win_scatter_count_distribution_first3':dict(nohit_sc),
     'line_hit_probability':float(line_prob),'scatter_only_hit_probability':float(scatter_extra),
     'hit_probability':float(line_prob+scatter_extra),'hit_probability_fraction':str(line_prob+scatter_extra)}
print(json.dumps(out,indent=2))
with open(os.path.join(os.path.dirname(__file__),'exact_hit_results.json'),'w') as f:
    json.dump(out,f,indent=2)
