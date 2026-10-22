"""Run existing engine/API regressions while preserving historical reports."""
import importlib
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / 'test-interface'), str(ROOT / 'test-interface/qa'), str(ROOT / 'test-interface/engine')]
from polska_gurom import config, selection

class Result(unittest.TextTestResult):
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

ok = True
for module_name, output in [('test_cascades','cascade_engine_results.json'),('test_server','server_api_results.json')]:
    if '--server-only' in sys.argv and module_name != 'test_server':
        continue
    suite = unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module(module_name))
    result = unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
    report = {'status':'pass' if result.wasSuccessful() else 'fail','math_version':config.MATH_VERSION,'lut_sha256':selection.load_distribution()[0]['lut_sha256'],'tests_run':result.testsRun,'passed':sum(t['status']=='pass' for t in result.records),'tests':result.records,'failures':len(result.failures),'errors':len(result.errors)}
    (HERE/output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    ok &= result.wasSuccessful()
raise SystemExit(0 if ok else 1)
