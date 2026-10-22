"""Read-only tests of the actual copied project; results stay in the workspace."""
import hashlib
import json
from pathlib import Path
import runpy
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
plan = json.loads((here/"deployment_plan.json").read_text())
target = Path(plan["target"])
for name, digest in plan["source_files"].items():
    assert hashlib.sha256((target/name).read_bytes()).hexdigest() == digest
for name in ("PHASE2_REPORT.md", "simulation_10000.json", "simulation_100000.json", "simulation_1m.json", "theory.json"):
    assert not (target/name).exists()
    assert hashlib.sha256((target/"legacy_v0_1"/name).read_bytes()).hexdigest() == plan["original_files"][name]
sys.path.insert(0,str(target))
import polska_gurom
assert Path(polska_gurom.__file__).resolve().is_relative_to(target.resolve())
assert polska_gurom.__version__ == "0.2.0"
passed = []
for file in sorted((target/"tests").glob("test_*.py")):
    for name,function in sorted(runpy.run_path(str(file)).items()):
        if name.startswith("test_") and callable(function):
            function()
            passed.append(name)
for name,digest in plan["source_files"].items():
    assert hashlib.sha256((target/name).read_bytes()).hexdigest() == digest
result = dict(target=str(target), version=polska_gurom.__version__, tests_passed=len(passed),
              copied_file_hashes_verified=len(plan["source_files"]), files_unchanged_by_tests=True,
              legacy_reports_verified=5, package_imported_from=str(polska_gurom.__file__))
(here/"deployment_verification.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
