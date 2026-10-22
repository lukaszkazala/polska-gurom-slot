"""Run the current regression suites with isolated audit outputs and real exits."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json
import os
import shutil
import subprocess
import sys
import time

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
APP=OUT/'release/test-interface-any-start'
NODE=shutil.which('node')
env=os.environ.copy()
env.update(PG_QA_OUT_DIR=str(OUT),PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
results=[]

def run(name,command):
    start=time.monotonic()
    with (OUT/(name+'.log')).open('w',encoding='utf-8') as log:
        process=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
    row={'suite':name,'exit_code':process.returncode,'seconds':round(time.monotonic()-start,3)}
    print(json.dumps(row),flush=True)
    return row

python_suites=[('test_server',APP/'test_server.py'),('test_cascades',APP/'qa/test_cascades.py'),
               ('test_network_faults',APP/'qa/test_network_faults.py'),
               ('test_atomicity',APP/'qa/test_settlement_atomicity.py'),
               ('test_bonus12_api',APP/'qa/test_bonus12_api.py'),('test_rgs_http',APP/'qa/test_rgs_http.py'),('test_rgs_recovery_http',APP/'qa/test_rgs_recovery_http.py')]
with ThreadPoolExecutor(max_workers=3) as pool:
    futures=[pool.submit(run,name,[sys.executable,'-B',str(file)]+(['--require-exported'] if name=='test_bonus12_api' else [])) for name,file in python_suites]
    results.extend(f.result() for f in futures)
if not any(row['exit_code'] for row in results):
    shutil.copy2(ROOT/'audit/full_review_2026_10_20/frontend/middle_fixture.json',OUT/'middle_fixture.json')
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(run,name,[str(NODE),str(APP/'qa'/file)]) for name,file in (
            ('test_autoplay','test_autoplay.cjs'),('test_network_logic','test_network_logic.cjs'),
            ('test_bonus12_frontend','test_bonus12_frontend.cjs'),('test_any_start_frontend','test_any_start_frontend.cjs'),
            ('test_audit_fixes','test_audit_fixes.cjs'),('test_rgs','test_rgs.cjs'),('test_rgs_recovery','test_rgs_recovery.cjs'),('test_replay','test_replay.cjs'),('test_platform_currency','test_platform_currency.cjs'))]
        results.extend(f.result() for f in futures)
report={'passed':not any(row['exit_code'] for row in results),'suites':results}
(OUT/'regression_summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
raise SystemExit(0 if report['passed'] else 1)
