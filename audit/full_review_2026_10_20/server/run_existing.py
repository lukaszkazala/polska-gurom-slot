from pathlib import Path
import os,subprocess,sys,json,time
out=Path(__file__).resolve().parent
app=out/'isolated_app'
env=dict(os.environ,PG_QA_OUT_DIR=str(out),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
rows=[]
for name,args in [('test_server',['-m','unittest','-v','test_server.py']),('test_cascades',['qa/test_cascades.py','-v']),('test_bonus12_api',['qa/test_bonus12_api.py','--require-exported']),('test_network_faults',['qa/test_network_faults.py'])]:
 start=time.monotonic()
 p=subprocess.run([sys.executable,'-B',*args],cwd=app,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (out/(name+'_unrestricted.log')).write_bytes(p.stdout)
 row={'suite':name,'exit_code':p.returncode,'seconds':round(time.monotonic()-start,3),'log':name+'_unrestricted.log'}
 rows.append(row)
 print(json.dumps(row),flush=True)
(out/'suite_results.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
raise SystemExit(any(x['exit_code'] for x in rows))
