"""Conservative cap bound with outward-rounded Decimal finite MGFs.

Payout lattice is 0.01 total bet. The tail-integral Chernoff inequality gives
E[(Y-C)+] <= exp(-t*C) E[exp(t*Y); trigger] / t. Unlike the tighter e-factor
bound this uses only positive sums/products, exp and division by an exact t.
Every operation rounds upward. Decimal.exp is correctly rounded; next_plus
turns its rounding-to-nearest result into an upper bound.
"""
from collections import Counter
from decimal import Decimal as Dec, localcontext, ROUND_CEILING
from pathlib import Path
import json
import numpy as np

HERE=Path(__file__).resolve().parent
j=np.load(HERE.parent/'v02_distribution/joint_counts.npz')
D=36**5
PN=216905037
PD=10**9
assert PN%3==0
scpay=[0,0,0,100,500,2000]
fs_counts=Counter()
for key,mult in [('base',PD-PN),('forced_1',PN//3),('forced_2',PN//3),('forced_3',PN//3)]:
    h=j[key]
    for line,sc in zip(*np.nonzero(h)):
        fs_counts[4*int(line)+scpay[sc]]+=int(h[line,sc])*mult
assert sum(fs_counts.values())==D*PD

with localcontext() as ctx:
    ctx.prec=60
    ctx.rounding=ROUND_CEILING
    t=Dec('0.024')
    def exp_upper(x):return x.exp().next_plus()
    fs_mgf=Dec(0)
    for payout,num in fs_counts.items():
        fs_mgf+=Dec(num)*exp_upper(t*Dec(payout)/100)/Dec(D*PD)
    total_mgf=Dec(0)
    h=j['base']
    for sc,n in [(3,8),(4,10),(5,12)]:
        base_mgf=Dec(0)
        for line in np.flatnonzero(h[:,sc]):
            base_mgf+=Dec(int(h[line,sc]))*exp_upper(t*Dec(int(line)+scpay[sc])/100)/Dec(D)
        total_mgf+=base_mgf*fs_mgf**n
    probability_upper=exp_upper(-t*5000)*total_mgf
    loss_upper=probability_upper/t
    out={'t':str(t),'precision':ctx.prec,'rounding':ctx.rounding,
         'free_spin_mgf_upper':str(fs_mgf),'triggered_round_mgf_upper':str(total_mgf),
         'cap_probability_upper_bound':str(probability_upper),
         'cap_rtp_loss_upper_bound':str(loss_upper),
         'conservative_joint_upper_bound':'1e-40',
         'method':'Outward-rounded Decimal finite MGFs, tail integral Chernoff bound. exp().next_plus() bounds correctly rounded exp upward.'}
(HERE/'cap_bound_decimal.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps(out,indent=2))
