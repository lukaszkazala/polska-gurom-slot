"""Independent exact rational calibration for the v0.2 design."""
from collections import Counter
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import json
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, r'D:\Kazaluka_slots\polska_gurom_phase2_v0.1')
from polska_gurom import config as c

pay = {s: {n: round(v*100) for n,v in row.items()} for s,row in c.PAYTABLE.items()}
pay['L1'][3] = 16
counts = [Counter(strip) for strip in c.REEL_STRIPS]
def score(seq):
    best = 0
    for target in c.REGULAR_SYMBOLS:
        count = 0
        for s in seq:
            if s not in (target,c.WILD): break
            count += 1
        if count >= 3: best = max(best,pay[target][count])
    return best
def line_mean(forced=None):
    num = 0
    for seq in product(*[([c.WILD] if i==forced else c.SYMBOLS) for i in range(5)]):
        w = 1
        for r,s in enumerate(seq):
            if r != forced: w *= counts[r][s]
        num += score(seq)*w
    return F(num,100*36**(5-(forced is not None)))
L=20*line_mean()
E=sum(20*line_mean(i) for i in (1,2,3))/3
S=F(1505,248832)
N=F(569,13824)
Q=F(211,41472)
B=L+S
M=4
p=( (F(24,25)-B)/N - M*L-S )/(M*(E-L))
pr=F(round(float(p)*10**9),10**9)
fs=M*(L+pr*(E-L))+S
out={'line_mean':L,'expanded_line_mean':E,'scatter_mean':S,'base_rtp':B,
     'expected_free_spins_per_paid_round':N,'trigger_probability':Q,
     'p_exact_uncapped':p,'p_rational_1e9':pr,'free_spin_mean':fs,
     'mean_bonus_on_trigger':N*fs/Q,'bonus_rtp':N*fs,'rtp_uncapped':B+N*fs}
encoded={k:{'value':float(v),'fraction':str(v)} for k,v in out.items()}
Path(__file__).with_name('line_expectations.json').write_text(json.dumps(encoded,indent=2),encoding='utf8')
print(json.dumps(encoded,indent=2))
