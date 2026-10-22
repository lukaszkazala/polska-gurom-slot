"""Read-only verification of the downloaded prototype; results stay in audit/."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import runpy
import sys
import time
import traceback

sys.dont_write_bytecode = True
PROJECT = Path(r"D:\Kazaluka_slots\polska_gurom_phase2_v0.1")
OUTPUT = Path(__file__).resolve().parent
OUTPUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(PROJECT))


def snapshot():
    return {
        str(p.relative_to(PROJECT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(PROJECT.rglob("*")) if p.is_file()
    }


def compare(actual, expected, prefix=""):
    differences = []
    if isinstance(expected, dict):
        actual = {str(k): v for k, v in actual.items()}
        if set(actual) != set(expected):
            differences.append({"field": prefix, "actual_keys": sorted(actual),
                                "expected_keys": sorted(expected)})
        for key in expected.keys() & actual.keys():
            differences.extend(compare(actual[key], expected[key], f"{prefix}.{key}"))
    elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
        if not math.isclose(actual, expected, rel_tol=1e-11, abs_tol=1e-12):
            differences.append({"field": prefix, "actual": actual, "expected": expected})
    elif actual != expected:
        differences.append({"field": prefix, "actual": actual, "expected": expected})
    return differences


def save(name, value):
    (OUTPUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


before = snapshot()
save("original_hashes.json", before)
print("Runtime:", sys.version, flush=True)

# These original tests are plain assertion functions, with no pytest fixtures,
# parametrization or hooks. Invoke them directly because pytest is not bundled.
namespace = runpy.run_path(str(PROJECT / "tests" / "test_math.py"))
test_results = []
for name, function in sorted(namespace.items()):
    if name.startswith("test_") and callable(function):
        try:
            function()
            test_results.append({"name": name, "passed": True})
        except Exception:
            test_results.append({"name": name, "passed": False, "error": traceback.format_exc()})
save("original_test_results.json", {"runner": "direct plain-function invocation; pytest unavailable",
                                    "results": test_results})
print("Original assertion tests:", sum(r["passed"] for r in test_results), "/", len(test_results), flush=True)

from polska_gurom.theory import theoretical_metrics
from polska_gurom.sim import simulate

theory_start = time.perf_counter()
theory = theoretical_metrics()
theory_comparison = compare(theory, json.loads((PROJECT / "theory.json").read_text()))
save("reproduced_theory.json", theory)
print("Theory:", json.dumps({"seconds": time.perf_counter()-theory_start,
                             "total_rtp": theory["total_rtp"],
                             "differences": theory_comparison}), flush=True)

simulations = []
for n, stored in [(10_000, "simulation_10000.json"), (100_000, "simulation_100000.json"),
                  (1_000_000, "simulation_1m.json")]:
    start = time.perf_counter()
    result = simulate(n, seed=20261015)
    save("reproduced_" + stored, result)
    differences = compare(result, json.loads((PROJECT / stored).read_text()))
    record = {"spins": n, "seconds": time.perf_counter()-start,
              "differences": differences, "rtp": result["rtp"],
              "hit_frequency": result["hit_frequency"]}
    simulations.append(record)
    print("Simulation:", json.dumps(record), flush=True)

after = snapshot()
summary = {"python": sys.version, "original_test_count": len(test_results),
           "original_test_passed": sum(r["passed"] for r in test_results),
           "theory_differences": theory_comparison, "simulations": simulations,
           "original_files_unchanged": before == after,
           "original_file_count": len(before)}
save("reproduction_summary.json", summary)
print("Summary:", json.dumps(summary), flush=True)
