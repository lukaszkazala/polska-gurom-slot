"""Fresh rerun of current checks; all historical evidence stays unchanged."""
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'regression'
OUT.mkdir(parents=True, exist_ok=True)
sys.path[:0] = [str(ROOT / 'test-interface'), str(ROOT / 'test-interface/qa'), str(ROOT / 'test-interface/engine')]
from polska_gurom import config, selection

class RecordingResult(unittest.TextTestResult):
    def startTestRun(self):
        self.records = []
        super().startTestRun()
    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append({'name':test.id(),'status':'pass'})
    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records.append({'name':test.id(),'status':'fail','error':self._exc_info_to_string(err,test)})
    def addError(self, test, err):
        super().addError(test, err)
        self.records.append({'name':test.id(),'status':'error','error':self._exc_info_to_string(err,test)})

def main():
    started = datetime.now(timezone.utc).isoformat()
    ok = True
    steps = []
    for name, output in [('test_cascades','cascade_engine_results.json'),('test_server','server_api_results.json')]:
        result = unittest.TextTestRunner(verbosity=2,resultclass=RecordingResult).run(unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module(name)))
        report = {'status':'pass' if result.wasSuccessful() else 'fail','math_version':config.MATH_VERSION,'lut_sha256':selection.load_distribution()[0]['lut_sha256'],'tests_run':result.testsRun,'passed':sum(t['status']=='pass' for t in result.records),'tests':result.records,'failures':len(result.failures),'errors':len(result.errors)}
        (OUT/output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        steps.append({'name':name,'exit_code':0 if result.wasSuccessful() else 1})
        ok &= result.wasSuccessful()
    env = dict(os.environ, PG_QA_OUT_DIR=str(OUT), PG_QA_ARCHIVE=str(ROOT / 'test-interface/POLSKA_GUROM_v0_4_1_12FS_FIX.zip'), PG_QA_REQUIRE_EXPORTED='1')
    commands = [
        [sys.executable,'audit/bonus12_fix_2026_10_20/test_coverage.py','--report',str(OUT/'coverage_results.json')],
        ['node','test-interface/qa/test_autoplay.cjs'],
        ['node','test-interface/qa/test_network_logic.cjs'],
        [sys.executable,'test-interface/qa/test_network_faults.py'],
        [sys.executable,'test-interface/qa/portable_check.py'],
        [sys.executable,'test-interface/qa/test_bonus12_api.py','--require-exported'],
        ['node','test-interface/qa/test_bonus12_frontend.cjs'],
        [sys.executable,'audit/stake_cascades_v04/official_validation/run_official_validation.py','--report',str(OUT/'official_validation_report.json')],
    ]
    for command in commands:
        label = Path(command[1]).stem
        print('RUNNING', label, flush=True)
        with (OUT/(label+'.log')).open('w',encoding='utf-8') as stream:
            result = subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
        steps.append({'name':label,'exit_code':result.returncode})
        ok &= result.returncode == 0
        print('FINISHED', label, result.returncode, flush=True)
    report = {'started_at_utc':started,'completed_at_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS' if ok else 'FAIL','math_version':config.MATH_VERSION,'lut_sha256':selection.load_distribution()[0]['lut_sha256'],'source_fingerprint':selection.source_fingerprint(),'steps':steps,'scope':'Fresh existing regression cases plus local unmodified pinned public SDK, not private RGS integration or platform approval'}
    (OUT/'run_summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)
    return 0 if ok else 1

if __name__ == '__main__':
    raise SystemExit(main())
