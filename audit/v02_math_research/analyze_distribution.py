"""Moments, cap bound and payout distribution from exhaustive v0.2 histograms.

The input joint distributions enumerate the 36**5 correlated reel windows.
Payouts below are multiples of TOTAL BET. Moment arithmetic uses fractions;
FFT is used only for descriptive tail probabilities and quantiles.
"""
from fractions import Fraction as F
from pathlib import Path
import json
import math
import numpy as np
from scipy.fft import rfft, irfft, next_fast_len
from scipy.optimize import minimize_scalar
from scipy.special import logsumexp

HERE=Path(__file__).resolve().parent
D=36**5
P=F(216905037,10**9)
C=5000
SP=np.array([0,0,0,100,500,2000],dtype=np.int64)
NS=np.array([0,0,0,8,10,12],dtype=np.int64)
joint=np.load(HERE.parent/'v02_distribution/joint_counts.npz')
base=joint['base']
forced=[joint[f'forced_{r}'] for r in (1,2,3)]
assert base.sum()==D
assert all(x.sum()==D for x in forced)

def sparse(hist, multiplier):
    line,sc=np.nonzero(hist)
    return multiplier*line+SP[sc],hist[line,sc]

def fs_hist(hist):
    x,w=sparse(hist,4)
    return np.bincount(x,weights=w,minlength=int(x.max())+1)/D

fa=fs_hist(base)
fbs=[fs_hist(x) for x in forced]
lenfs=max(map(len,[fa,*fbs]))
pad=lambda a:np.pad(a,(0,lenfs-len(a)))
fa=pad(fa)
fb=sum(map(pad,fbs))/3
fz=(1-float(P))*fa+float(P)*fb
z=np.flatnonzero(fz)
fsmax=int(z[-1])/100

def fs_moment(k):
    nums=[]
    for hist in [base,*forced]:
        x,w=sparse(hist,4)
        nums.append(sum(int(a)**k*int(b) for a,b in zip(x,w)))
    return ((1-P)*F(nums[0],D)+P*sum(F(n,D) for n in nums[1:])/3)/100**k

mu=fs_moment(1)
z2=fs_moment(2)
varz=z2-mu**2
base_moments={}
for k in (1,2):
    x,w=sparse(base,1)
    base_moments[k]=F(sum(int(a)**k*int(b) for a,b in zip(x,w)),D*100**k)
EN=F(sum(int(base[:,sc].sum())*int(NS[sc]) for sc in range(6)),D)
ENN1=F(sum(int(base[:,sc].sum())*int(NS[sc]*(NS[sc]-1)) for sc in range(6)),D)
EXN=F(sum(int(n)*(int(line)+int(SP[sc]))*int(NS[sc]) for line,sc in zip(*np.nonzero(base)) for n in [base[line,sc]]),D*100)
q=F(int(base[:,3:].sum()),D)
mean=base_moments[1]+EN*mu
y2=base_moments[2]+2*mu*EXN+EN*z2+ENN1*mu**2
vary=y2-mean**2
bonus_mean=EN*mu/q
bonus_y2=(EN*z2+ENN1*mu**2)/q
bonus_var=bonus_y2-bonus_mean**2

base_dists=[]
maxima=[]
for sc in range(6):
    line=np.flatnonzero(base[:,sc])
    x=line+SP[sc]
    dd=np.zeros(int(x[-1])+1)
    dd[x]=base[line,sc]/D
    base_dists.append(dd)
    maxima.append(int(x[-1])/100)
roundmax=max(maxima[sc]+int(NS[sc])*fsmax for sc in range(6))

# Chernoff stop-loss bound: for t>0 and any y,
# (y-C)+ <= exp(t*(y-C))/(e*t). Base/trigger correlation is preserved.
# This bounds the amount RTP can lose to the cap, not only its frequency.
def log_stoploss_bound(t):
    log_mz=logsumexp(np.log(fz[z])+t*z/100)
    terms=[]
    for sc in (3,4,5):
        dd=base_dists[sc]
        xx=np.flatnonzero(dd)
        terms.append(logsumexp(np.log(dd[xx])+t*xx/100)+int(NS[sc])*log_mz)
    return float(logsumexp(terms)-t*C-1-math.log(t))
opt=minimize_scalar(log_stoploss_bound,bounds=(0.00001,0.2),method='bounded',options={'xatol':1e-13})
cap_loss_bound=math.exp(opt.fun)
cap_prob_bound=math.e*opt.x*cap_loss_bound
second_loss_bound=(roundmax+C)*cap_loss_bound

# Gross positive return and strictly net-positive paid rounds.
line,sc=np.nonzero(base)
bp=line+SP[sc]
w=base[line,sc]
base_hit=F(int(w[bp>0].sum()),D)
base_profit=F(int(w[bp>100].sum()),D)
at_one_trigger=F(int(base[0,3]),D)
pfs0=(1-P)*F(int(base[0,:3].sum()),D)+P*sum(F(int(h[0,:3].sum()),D) for h in forced)/3
profit=base_profit+at_one_trigger*(1-pfs0**8)
small_positive=F(int(w[(bp>0)&(bp<100)].sum()),D)
break_even=base_hit-small_positive-profit

maxunits=int(round(roundmax*100))
nfft=next_fast_len(maxunits+1,real=True)
ffz=rfft(fz,nfft)
fy=np.zeros(nfft//2+1,dtype=np.complex128)
fbonus=np.zeros_like(fy)
for sc in range(6):
    fbase=rfft(base_dists[sc],nfft)
    fy+=fbase*ffz**int(NS[sc])
    if sc>=3:
        fbonus+=base_dists[sc].sum()/float(q)*ffz**int(NS[sc])
raw=irfft(fy,nfft)[:maxunits+1]
rawbonus=irfft(fbonus,nfft)[:maxunits+1]
negative_mass=float(-raw[raw<0].sum())
negative_bonus_mass=float(-rawbonus[rawbonus<0].sum())
pmf=np.maximum(raw,0);pmf/=pmf.sum()
pmb=np.maximum(rawbonus,0);pmb/=pmb.sum()
cdf=np.cumsum(pmf);cb=np.cumsum(pmb)
quantiles=lambda c:{str(v):float(np.searchsorted(c,v))/100 for v in (.5,.75,.9,.95,.99,.999,.9999,.99999)}
tail=lambda a:{str(v):float(a[int(v*100)+1:].sum()) for v in (1,5,10,20,50,100,250,500,1000)}

out={
    'parameters':{'free_spin_line_multiplier':4,'expanding_probability':float(P),'expanding_probability_fraction':str(P),'cap':C},
    'rtp_uncapped':float(mean),'rtp_capped_interval':[float(mean)-cap_loss_bound,float(mean)],
    'rtp_capped_interval_expression':f'[{mean} - {cap_loss_bound:.17g}, {mean}]',
    'rtp_uncapped_fraction':str(mean),
    'base_rtp':float(base_moments[1]),'bonus_rtp':float(EN*mu),
    'base_standard_deviation':math.sqrt(float(base_moments[2]-base_moments[1]**2)),
    'paid_round_standard_deviation_uncapped':math.sqrt(float(vary)),
    'paid_round_variance_uncapped':float(vary),
    'paid_round_variance_uncapped_fraction':str(vary),
    'round_second_moment_loss_to_cap_bound':second_loss_bound,
    'free_spin_mean':float(mu),'free_spin_standard_deviation':math.sqrt(float(varz)),
    'mean_bonus_given_trigger':float(bonus_mean),'bonus_standard_deviation_given_trigger':math.sqrt(float(bonus_var)),
    'positive_return_probability':float(base_hit),'positive_below_bet_probability':float(small_positive),
    'net_profit_probability':float(profit),'break_even_probability':float(break_even),
    'free_spin_zero_probability':float(pfs0),'zero_bonus_probability_given_trigger':float(sum(F(int(base[:,sc].sum()),D)*pfs0**int(NS[sc]) for sc in (3,4,5))/q),
    'trigger_probability':float(q),'rounds_per_bonus':float(1/q),
    'cap_stoploss_chernoff_bound':cap_loss_bound,'cap_probability_chernoff_bound':cap_prob_bound,'chernoff_t':float(opt.x),
    'max_base_by_scatter':maxima,'max_free_spin':fsmax,'max_round_before_cap':roundmax,
    'round_gross_payout_quantiles_fft':quantiles(cdf),'bonus_payout_quantiles_given_trigger_fft':quantiles(cb),
    'round_gross_payout_tail_probabilities_gt_fft':tail(pmf),'bonus_tail_probabilities_given_trigger_gt_fft':tail(pmb),
    'fft_negative_mass_round':negative_mass,'fft_negative_mass_bonus':negative_bonus_mass,
    'notes':[
        'All units are multiples of total bet. Paid round includes its triggered bonus.',
        'Moments before cap use exact rational arithmetic, including base/trigger covariance.',
        'The mathematically derived Chernoff bound uses numerically evaluated finite MGFs. It bounds cap loss, so the calibrated uncapped RTP interval also controls capped RTP.',
        'FFT quantiles/tails are descriptive numerical distributions, not used to assert ultra-rare cap probabilities.',
        'There is no universal numerical industry boundary for volatility classes; report SD and payout quantiles with the medium-high design label.'
    ]
}
(HERE/'distribution_analysis.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps(out,indent=2))
