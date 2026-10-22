"""Report bonus sampling fluctuation without inventing pass/fail thresholds."""
import json
import math
from pathlib import Path
from scipy.stats import binom, binomtest, beta, chisquare

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
source=json.loads((ROOT/'audit/bonus12_fix_2026_10_20/bonus_frequency.json').read_text(encoding='utf-8'))
probabilities={0:1-source['bonus_probability'],**{t['free_spins']:t['probability'] for t in source['bonus_types']}}
types=[0,8,10,12]
def examine(n,counts):
    per_type=[]
    for award in types:
        p=probabilities[award];k=counts[award]
        bounds=[int(binom.ppf(.025,n,p)),int(binom.ppf(.975,n,p))]
        per_type.append({'free_spins':award,'count':k,'expected':n*p,'probability':p,'central_95_prediction_counts':bounds,'inside_prediction_counts':bounds[0]<=k<=bounds[1],'upper_tail_probability':float(binom.sf(k-1,n,p)),'exact_two_sided_pvalue':float(binomtest(k,n,p).pvalue),'rate_clopper_pearson_95':[0.0 if k==0 else float(beta.ppf(.025,k,n-k+1)),1.0 if k==n else float(beta.ppf(.975,k+1,n-k))]})
    pearson=chisquare([counts[a] for a in types],[n*probabilities[a] for a in types])
    return {'rounds':n,'types':per_type,'four_category_pearson_chi_square':float(pearson.statistic),'degrees_of_freedom':3,'four_category_pearson_pvalue':float(pearson.pvalue)}
runs=[examine(r['rounds'],{int(a):k for a,k in r['by_free_spins'].items()}) for r in source['previous_simulations_aggregated']]
all_n=sum(r['rounds'] for r in source['previous_simulations_aggregated'])
all_counts={a:sum(r['by_free_spins'][str(a)] for r in source['previous_simulations_aggregated']) for a in types}
report={'status':'INFORMATIONAL_SAMPLING_VARIATION','method':'Exact binomial count predictions and two-sided probability-order binomial tests, plus four-category Pearson check. No new draws. No weights changed in response to results.','runs':runs,'aggregate':examine(all_n,all_counts),'interpretation':['The 50M 12FS count is 230 versus mean200.9388; it lies one above the central95% integer count band174..229.','For 50M, P(X>=230) is about0.02378. A valid random model may yield counts outside a95% band. Multiple categories and runs also increase the chance of at least one such result.','The 100M 10FS count29172 versus mean28687.567 is above the95% prediction band28356..29020; the unadjusted exact two-sided p-value is about0.004303. The aggregate10FS46356 versus mean45900.1072 is also above its95% band45481..46320, unadjusted p about0.03347.','All three RTP results lie inside their separately reported95% normal reference bands. That claim must not be extended to every bonus category.','The aggregate12FS count657 in160M is compared with mean643.00416 in the aggregate record. This is a separate aggregate description, not a reason to erase an individual tail observation.','Finite-model exact RTP is computed algebraically from all outcomes; simulation RTP is a sample estimate. Difference does not imply a payout-accounting error.']}
(HERE/'bonus_sampling_addendum.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'aggregate':report['aggregate'],'50M_12FS':runs[1]['types'][3]},ensure_ascii=False,indent=2))
