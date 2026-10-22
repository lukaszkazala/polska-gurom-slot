"""Run existing assertions without changing implementation or prior evidence."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import random
import runpy
import sys
import time
import traceback

sys.dont_write_bytecode = True
WORKSPACE = Path(__file__).resolve().parents[3]
PROJECT = WORKSPACE / "polska_gurom_v0_2"
OUTPUT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))

started = time.monotonic()
results = []
for file in sorted((PROJECT / "tests").glob("test_*.py")):
    namespace = runpy.run_path(str(file))
    for name, function in sorted(namespace.items()):
        if name.startswith("test_") and callable(function):
            try:
                function()
                result = {"file": str(file), "name": name, "passed": True}
            except Exception:
                result = {"file": str(file), "name": name, "passed": False,
                          "error": traceback.format_exc()}
            results.append(result)
            print(f'{"PASS" if result["passed"] else "FAIL"} {name}', flush=True)

from polska_gurom import game, theory
from tools.math_config import compute_config_fingerprint

witnesses = []
for seed in range(100):
    result = game.play_round(random.Random(seed))
    if result.payout_units % 10:
        witnesses.append({"seed": seed, "payout_units": result.payout_units,
                          "payout_multiplier": result.payout,
                          "grid": result.base.grid,
                          "line_wins": [{"line_id": w.line_id, "symbol": w.symbol,
                                         "count": w.count, "payout_units": w.payout_units}
                                        for w in result.base.line_wins],
                          "has_bonus": bool(result.free_spins)})

moments = theory.exact_first_moments()
report = {"passed": sum(x["passed"] for x in results), "total": len(results),
          "seconds": time.monotonic() - started, "tests": results,
          "note": "The existing report assertion is only a regression assertion; fresh enumerated results are separate files in this audit directory.",
          "math_config_sha256": compute_config_fingerprint(),
          "fresh_first_moments": {k: {"fraction": str(v), "float": float(v)}
                                  for k, v in moments.items()},
          "payout_hundredths_not_divisible_by_ten_witnesses": witnesses,
          "source_hashes": {str(file): hashlib.sha256(file.read_bytes()).hexdigest()
                            for file in sorted(PROJECT.rglob("*.py"))}}
(OUTPUT / "test_results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"passed": report["passed"], "total": report["total"],
                  "precision_witnesses": witnesses[:3]}, indent=2), flush=True)
raise SystemExit(0 if report["passed"] == report["total"] else 1)
