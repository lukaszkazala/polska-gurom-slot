"""Rebuild current exports into audit storage and compare without replacing the game."""
import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CURRENT = ROOT/'test-interface/stake_math'
OUT = HERE/'rebuild'
OUT.mkdir(exist_ok=True)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

before = {p.name:sha(p) for p in CURRENT.iterdir() if p.is_file()}
spec = importlib.util.spec_from_file_location('current_math_compiler',ROOT/'test-interface/build_math.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.TARGET = OUT
with (HERE/'rebuild.log').open('w',encoding='utf-8') as log, contextlib.redirect_stdout(log):
    module.build()
files = {name:{'current':before[name],'rebuilt':sha(OUT/name),'equal':before[name] == sha(OUT/name)}
         for name in ['index.json','books_base.jsonl.zst','lookUpTable_base_0.csv','selection.json']}
old = json.loads((CURRENT/'mathematics.json').read_text(encoding='utf-8'))
new = json.loads((OUT/'mathematics.json').read_text(encoding='utf-8'))
old.pop('elapsed_seconds'); new.pop('elapsed_seconds')
report = {'status':'PASS' if all(x['equal'] for x in files.values()) and old == new else 'FAIL',
          'math_version':old['math_version'],'files':files,'mathematics_identical_except_build_elapsed_time':old == new,
          'production_files_unchanged':before == {p.name:sha(p) for p in CURRENT.iterdir() if p.is_file()},
          'scope':'Actual deterministic rebuild of all100048 outcomes and integer calibration; audit target only'}
(HERE/'rebuild_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' and report['production_files_unchanged'] else 1)
