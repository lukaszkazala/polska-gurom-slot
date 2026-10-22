"""Run the independent assertion tests with the Python standard library."""
from __future__ import annotations
import json
from pathlib import Path
import runpy
import sys
import time
import traceback

sys.dont_write_bytecode = True
if not __debug__:
    raise SystemExit("Assertion tests must run without Python -O optimization")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
started = time.monotonic()
results = []
for file in sorted((ROOT/"tests").glob("test_*.py")):
    namespace = runpy.run_path(str(file))
    for name, function in sorted(namespace.items()):
        if name.startswith("test_") and callable(function):
            try:
                function()
                entry = {"file": file.name, "test": name, "passed": True}
            except Exception:
                entry = {"file": file.name, "test": name, "passed": False, "error": traceback.format_exc()}
            results.append(entry)
            print(f'{"PASS" if entry["passed"] else "FAIL"} {name}', flush=True)
report = {"passed": sum(x["passed"] for x in results), "total": len(results),
          "seconds": time.monotonic()-started, "results": results}
(ROOT/"verification").mkdir(exist_ok=True)
(ROOT/"verification"/"test_results.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(f'{report["passed"]}/{report["total"]} passed')
sys.exit(0 if all(x["passed"] for x in results) else 1)
