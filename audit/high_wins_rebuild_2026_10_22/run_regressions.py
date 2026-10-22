"""Run local high-win/selection/settlement/presentation regressions once.

Refreshes feature fixtures from the current validated bank before running suites.
Outputs stay in this audit directory; sources/ is never touched.
"""
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INTERFACE = ROOT / "test-interface-any-start"
OUT = HERE / "regressions"
OUT.mkdir(parents=True, exist_ok=True)
ENV = {**os.environ, "PG_QA_OUT_DIR": str(OUT), "PYTHON": sys.executable,
       "PYTHONDONTWRITEBYTECODE": "1"}
PARSER = argparse.ArgumentParser()
PARSER.add_argument("--failed-only", action="store_true", help="Rerun failed suites, preserving earlier passing checks")
PARSER.add_argument("--only", nargs="+", default=[], help="Rerun named suites and retain other recorded results")
ARGS = PARSER.parse_args()
SUMMARY = HERE / "regression_summary.json"
PREVIOUS = json.loads(SUMMARY.read_text(encoding="utf-8")) if (ARGS.failed_only or ARGS.only) and SUMMARY.exists() else {}
PREVIOUS_CHECKS = {row["name"]: row for row in PREVIOUS.get("checks", [])}
ATTEMPT = HERE / "regression_attempts" / str(time.time_ns())
if PREVIOUS:
    ATTEMPT.mkdir(parents=True, exist_ok=True)
    (ATTEMPT / "regression_summary.json").write_bytes(SUMMARY.read_bytes())


def run(name, command):
    if (name in PREVIOUS_CHECKS and ARGS.only and name not in ARGS.only
            or PREVIOUS_CHECKS.get(name, {}).get("passed") and name not in ARGS.only):
        return PREVIOUS_CHECKS[name]
    old_log = OUT / f"{name}.log"
    if PREVIOUS and old_log.exists():
        (ATTEMPT / old_log.name).write_bytes(old_log.read_bytes())
    started = time.perf_counter()
    try:
        result = subprocess.run(command, cwd=INTERFACE, env=ENV, capture_output=True, timeout=240)
        output = result.stdout + b"\n" + result.stderr
        status = result.returncode
    except subprocess.TimeoutExpired as error:
        output = (error.stdout or b"") + b"\n" + (error.stderr or b"") + b"\nTIMEOUT\n"
        status = 124
    (OUT / f"{name}.log").write_bytes(output)
    entry = {"name": name, "passed": status == 0, "exit_code": status,
             "elapsed_seconds": round(time.perf_counter() - started, 3),
             "log": f"regressions/{name}.log"}
    print(json.dumps(entry), flush=True)
    return entry


if __name__ == "__main__":
    generated = run("generate_current_fixtures", [sys.executable, "-B", "qa/generate_regression_fixtures.py"])
    if not generated["passed"]:
        raise SystemExit(1)
    fixtures = json.loads((INTERFACE / "qa/regression_fixtures.json").read_text(encoding="utf-8"))
    # Existing presentation suites accept a relocated output/fixture directory.
    # Use current complete-round exports, never overwrite old audit evidence.
    for filename, kind in (("middle_fixture.json", "middle"), ("actual_export_12fs_fixture.json", "bonus12")):
        if PREVIOUS and (OUT / filename).exists():
            continue
        (OUT / filename).write_text(json.dumps({
            "scope": "Current positive-weight exported round; selected by manifest feature metadata",
            "math_version": fixtures["config"]["math_version"],
            "book_id": fixtures["book_ids"][kind], "round": fixtures["rounds"][kind],
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # This API suite also writes the 12FS fixture consumed by its frontend suite.
    # Finish that write before dispatching the independent checks below.
    bonus_api = run("bonus12_api", [sys.executable, "-B", "qa/test_bonus12_api.py", "--require-exported"])
    commands = [
        ("server", [sys.executable, "-B", "-m", "unittest", "-v", "test_server.py"]),
        ("settlement_atomicity", [sys.executable, "-B", "qa/test_settlement_atomicity.py"]),
        ("cascades", [sys.executable, "-B", "qa/test_cascades.py"]),
        ("high_wins", [sys.executable, "-B", str(HERE / "test_high_wins.py"), "--output", str(OUT / "high_win_regressions.json")]),
    ]
    for name in ("cap_messages", "audit_fixes", "replay", "rgs", "rgs_recovery", "autoplay",
                 "network_logic", "platform_currency", "localization", "bonus12_frontend", "any_start_frontend"):
        commands.append((name, ["node", f"qa/test_{name}.cjs"]))
    commands.append(("high_wins_frontend", ["node", str(HERE / "test_high_wins.cjs")]))
    with ThreadPoolExecutor(max_workers=3) as pool:
        checks = [generated, bonus_api, *pool.map(lambda row: run(*row), commands)]
    report = {
        "math_version": fixtures["config"]["math_version"],
        "scope": "Local selector, engine, HTTP wallet, UI logic and RGS contract regressions. Minimal DOM tests do not establish browser visuals or platform approval.",
        "passed": all(check["passed"] for check in checks),
        "suites_run": len(checks), "suites_passed": sum(check["passed"] for check in checks),
        "checks": checks,
        "fixture_sha256": hashlib.sha256((INTERFACE / "qa/regression_fixtures.json").read_bytes()).hexdigest(),
        "source_sha256": {name: hashlib.sha256((INTERFACE / name).read_bytes()).hexdigest()
                          for name in ("engine/polska_gurom/config.py", "engine/polska_gurom/game.py",
                                       "engine/polska_gurom/selection.py", "server.py", "web/app.js",
                                       "web/rgs-client.js", "web/game-config.json", "stake_math/lookUpTable_base_0.csv")},
        "prior_attempt_directories": [path.relative_to(HERE).as_posix()
                                      for path in sorted((HERE / "regression_attempts").iterdir())]
                                     if (HERE / "regression_attempts").exists() else [],
    }
    SUMMARY.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("math_version", "passed", "suites_run", "suites_passed")}), flush=True)
    raise SystemExit(not report["passed"])
