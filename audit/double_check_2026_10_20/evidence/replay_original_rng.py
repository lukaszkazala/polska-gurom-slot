"""Reproduce existing streams, via histogram edges rather than selector code.

This verifies provenance after category tail observations; these are the SAME
three seeds and rounds, not three new independent Monte Carlo experiments.
"""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
FIX=ROOT/'audit/bonus12_fix_2026_10_20'
lut=ROOT/'test-interface/stake_math/lookUpTable_base_0.csv'
rows=[tuple(map(int,r)) for r in csv.reader(lut.open(encoding='utf-8'))]
report=json.loads((FIX/'weighted_results/weighted_simulation_report.json').read_text(encoding='utf-8'))
total=sum(w for _,w,_ in rows)
edges=np.concatenate((np.array([0],dtype=np.int64),np.cumsum(np.array([w for _,w,_ in rows],dtype=np.int64))))
assert all(w>0 for _,w,_ in rows)
results=[]
for source in report['runs']:
    n=source['rounds'];rng=np.random.Generator(np.random.PCG64(source['seed']))
    initial=hashlib.sha256(json.dumps(rng.bit_generator.state,sort_keys=True).encode()).hexdigest()
    counts=np.zeros(len(rows),dtype=np.int64)
    drawn=0;start=time.perf_counter()
    while drawn<n:
        batch=min(1_000_003,n-drawn)
        tickets=rng.integers(0,total,size=batch,dtype=np.uint64)
        # Different mapping algorithm from the original searchsorted+bincount.
        # Exact integer edges; no floating ticket/payout approximation.
        counts+=np.histogram(tickets,bins=edges)[0]
        drawn+=batch
    original=[int(r['observed_count']) for r in csv.DictReader((FIX/'weighted_results'/source['outcome_histogram_file']).open(encoding='utf-8'))]
    final=hashlib.sha256(json.dumps(rng.bit_generator.state,sort_keys=True).encode()).hexdigest()
    mismatch=np.flatnonzero(counts!=np.asarray(original,dtype=np.int64))
    result={'rounds':n,'seed':source['seed'],'same_original_stream_replayed':True,'counts_match_every_outcome':not len(mismatch),'outcome_count':len(counts),'sum':int(counts.sum()),'original_initial_rng_state_matches':initial==source['initial_rng_state_sha256'],'original_final_rng_state_matches':final==source['final_rng_state_sha256'],'mismatching_ids':mismatch.tolist(),'elapsed_seconds':time.perf_counter()-start}
    results.append(result)
    print(json.dumps(result),flush=True)
status=all(r['counts_match_every_outcome'] and r['original_initial_rng_state_matches'] and r['original_final_rng_state_matches'] and r['sum']==r['rounds'] for r in results)
output={'status':'PASS' if status else 'FAIL','created_utc':datetime.now(timezone.utc).isoformat(),'numpy_version':np.__version__,'lut_sha256':hashlib.sha256(lut.read_bytes()).hexdigest(),'method':'Same original PCG64 seeds; alternate batch size1000003; np.histogram exact integer CDF edges rather than original np.searchsorted+bincount. Full streams replayed, not new independent runs.','same_stream_tickets_regenerated':sum(r['rounds'] for r in results),'new_independent_experiments':0,'runs':results}
(HERE/'original_rng_replay.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
raise SystemExit(0 if status else 1)
