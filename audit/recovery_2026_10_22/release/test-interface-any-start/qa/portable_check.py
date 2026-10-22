from __future__ import annotations

from pathlib import Path
import hashlib
import http.cookiejar
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
sys.path.insert(0, str(ROOT / "engine"))
from polska_gurom.config import MATH_VERSION as CURRENT_MATH_VERSION
REPORT_DIRECTORY = Path(os.environ.get("PG_QA_OUT_DIR", ROOT / "qa"))
ARCHIVE = Path(os.environ.get("PG_QA_ARCHIVE", ROOT / "POLSKA_GUROM_TESTER.zip"))
ARCHIVE_HASH = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
FOLDER = (REPORT_DIRECTORY / f"portable-smoke-{ARCHIVE_HASH[:12]}").resolve()
checks = []
report = {"success": False, "checks": checks}
process = None


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append({"name": name, "success": True})


def round_is_consistent(result, max_units):
    """Check settlement and falling survivors using only the serialized result."""
    spins = [result["base"], *result["free_spins"]]
    assert result["payout_units"] == result["base"]["payout_units"] + sum(result["free_spin_credits"])
    assert result["raw_payout_units"] == sum(spin["raw_payout_units"] for spin in spins)
    assert result["cap_reduction_units"] == result["raw_payout_units"] - result["payout_units"]
    assert 0 <= result["payout_units"] <= max_units
    remaining = max_units
    for spin in spins:
        steps = spin["cascades"]
        assert steps and steps[0]["evaluation_grid"] == spin["evaluation_grid"]
        assert steps[0]["line_wins"] == spin["line_wins"]
        assert spin["line_payout_units"] == sum(step["line_payout_units"] for step in steps)
        assert spin["raw_payout_units"] == spin["line_payout_units"] + spin["scatter_payout_units"]
        assert spin["payout_units"] == min(remaining, spin["raw_payout_units"])
        stage_remaining = remaining - min(remaining, spin["scatter_payout_units"])
        for index, step in enumerate(steps):
            assert step["line_payout_units"] == sum(win["payout_units"] for win in step["line_wins"])
            assert step["payout_units"] == min(stage_remaining, step["line_payout_units"])
            stage_remaining -= step["payout_units"]
            if index + 1 == len(steps):
                assert step["removed_positions"] == step["movements"] == []
                assert not step["line_wins"] or stage_remaining == 0 or spin["cascade_limit_reached"]
                continue
            removed = {(win["rows"][reel], reel) for win in step["line_wins"]
                       for reel in range(win.get("start_reel", 0), win.get("start_reel", 0) + win["count"])}
            assert {tuple(p) for p in step["removed_positions"]} == removed
            following = steps[index + 1]["evaluation_grid"]
            assert sum(move["from_row"] < 0 for move in step["movements"]) == len(removed)
            for reel in range(5):
                survivors = [step["evaluation_grid"][row][reel] for row in range(3)
                             if (row, reel) not in removed]
                if survivors:
                    assert [row[reel] for row in following][-len(survivors):] == survivors
            for move in step["movements"]:
                assert following[move["to_row"]][move["reel"]] == move["symbol"]
                if move["from_row"] < 0:
                    assert move["symbol"] != "SCATTER"
                else:
                    assert move["to_row"] > move["from_row"]
                    assert step["evaluation_grid"][move["from_row"]][move["reel"]] == move["symbol"]
        assert spin["payout_units"] == min(remaining, spin["scatter_payout_units"]) + sum(step["payout_units"] for step in steps)
        remaining -= spin["payout_units"]
    return True


try:
    assert FOLDER.is_relative_to(WORKSPACE) and FOLDER != WORKSPACE
    with zipfile.ZipFile(ARCHIVE) as archive:
        names = archive.namelist()
        check("zip_integrity", archive.testzip() is None)
        check("zip_no_python_cache", not any("__pycache__" in name or name.endswith((".pyc", ".pyo")) for name in names))
        for name in names:
            assert (FOLDER / name).resolve().is_relative_to(FOLDER)
        if not FOLDER.exists():
            FOLDER.mkdir(parents=True)
            archive.extractall(FOLDER)
        check("extracted_files_match_zip", all((FOLDER / name).read_bytes() == archive.read(name) for name in names))
    check("portable_files", all((FOLDER / path).is_file() for path in ["START.cmd", "README_PL.md", "server.py", "web/index.html", "web/assets/symbols.json", "engine/polska_gurom/game.py"]))
    bundled_reference = ROOT / "engine" / "polska_gurom"
    engine_reference = bundled_reference if bundled_reference.is_dir() else WORKSPACE / "polska_gurom_v0_2" / "polska_gurom"
    engine_files = [p for p in engine_reference.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix not in {".pyc", ".pyo"}]
    check("engine_bytes_match_current_reference", bool(engine_files) and all(p.read_bytes() == (FOLDER / "engine" / "polska_gurom" / p.relative_to(engine_reference)).read_bytes() for p in engine_files))
    with socket.socket() as selected:
        selected.bind(("127.0.0.1", 0))
        port = selected.getsockname()[1]
    check("isolated_port", port != 8765)
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    entry = "import server; print('ENGINE_PATH=' + str(server.game.__file__), flush=True); raise SystemExit(server.main())"
    process = subprocess.Popen([sys.executable, "-B", "-c", entry, "--port", str(port), "--no-browser"], cwd=FOLDER, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    base = f"http://127.0.0.1:{port}"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def get(path, raw=False):
        with opener.open(base + path, timeout=5) as response:
            body = response.read()
            return body.decode("utf-8") if raw else json.loads(body)

    def post(body):
        request = urllib.request.Request(base + "/api/spin", data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json", "X-Game-Session": initial["session_id"]}, method="POST")
        with opener.open(request, timeout=5) as response:
            return json.load(response)

    deadline = time.monotonic() + 12
    while True:
        if process.poll() is not None:
            raise AssertionError("Packaged server stopped during startup.")
        try:
            health = get("/api/health")
            break
        except (OSError, urllib.error.URLError):
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.05)
    check("packaged_server_health", health == {"ok": True, "engine": "polska_gurom", "math_version": CURRENT_MATH_VERSION})
    html = get("/", raw=True)
    check("homepage", "<html" in html.lower() and "POLSKA GUROM" in html)
    config = get("/api/config")
    check("config", len(config["symbols"]) == 10 and len(config["paylines"]) == 20 and config["free_spins"] == {"3": 8, "4": 10, "5": 12})
    check("cascade_version_metadata", config["math_version"] == CURRENT_MATH_VERSION and config["cascades_enabled"] and config["max_cascades"] == 1000)
    manifest = get("/assets/symbols.json")
    check("symbol_manifest", len(manifest) == 10 and manifest["P4"]["pl"] == "Husarz")
    initial = get("/api/state")
    check("initial_state", initial["balance_cents"] == 1000000 and initial["rounds"] == 0 and initial["recent_rounds"] == [])
    bet = config["bet_options_cents"][0]
    body = {"bet_cents": bet, "mode": "random", "request_id": "portable-normal-1"}
    normal = post(body)
    check("normal_spin_wallet", normal["balance_before_cents"] == initial["balance_cents"] and normal["balance_cents"] == initial["balance_cents"] - bet + normal["win_cents"] and normal["stats"]["rounds"] == 1 and normal["stats"]["total_bet_cents"] == bet and normal["stats"]["total_win_cents"] == normal["win_cents"])
    check("normal_spin_idempotency", post(body) == normal)
    check("normal_cascade_settlement", round_is_consistent(normal["round"], config["max_win_units"]))
    conflict = False
    try:
        post({**body, "bet_cents": config["bet_options_cents"][1]})
    except urllib.error.HTTPError as error:
        conflict = error.code == 409 and json.loads(error.read())["code"] == "request_conflict"
    check("request_id_conflict", conflict)
    scenario_body = {"bet_cents": bet, "mode": "expansion", "request_id": "portable-expansion-1"}
    expansion = post(scenario_body)
    check("expansion_scenario", expansion["is_scenario"] and expansion["round"]["base"]["bonus_triggered"] and any(item["expanding_reel"] is not None for item in expansion["round"]["free_spins"]))
    check("scenario_preserves_wallet_statistics", expansion["balance_cents"] == normal["balance_cents"] and expansion["balance_before_cents"] == normal["balance_cents"] and expansion["stats"] == normal["stats"])
    check("scenario_idempotency", post(scenario_body) == expansion)
    check("bonus_cascade_settlement", round_is_consistent(expansion["round"], config["max_win_units"]))
    cascade_body = {"bet_cents": bet, "mode": "cascade", "request_id": "portable-cascade-1"}
    cascade = post(cascade_body)
    stages = cascade["round"]["base"]["cascades"]
    check("cascade_scenario", cascade["is_scenario"] and cascade["scenario_seed"] == 2 and len(stages) >= 3 and not cascade["round"]["free_spins"])
    check("cascade_contains_falling_survivors", any(move["from_row"] >= 0 and move["to_row"] > move["from_row"] for stage in stages for move in stage["movements"]))
    check("cascade_serialized_transitions", round_is_consistent(cascade["round"], config["max_win_units"]))
    check("cascade_preserves_wallet_statistics", cascade["balance_cents"] == normal["balance_cents"] and cascade["stats"] == normal["stats"])
    check("cascade_idempotency", post(cascade_body) == cascade)
    state = get("/api/state")
    check("recent_rounds", [item["round_id"] for item in state["recent_rounds"]] == [cascade["round_id"], expansion["round_id"], normal["round_id"]] and state["rounds"] == 1 and state["balance_cents"] == normal["balance_cents"])
    process.terminate()
    output, _ = process.communicate(timeout=5)
    process = None
    engine_path = next(line.removeprefix("ENGINE_PATH=") for line in output.splitlines() if line.startswith("ENGINE_PATH="))
    check("server_imports_extracted_engine", Path(engine_path).resolve() == (FOLDER / "engine/polska_gurom/game.py").resolve())
    report.update(success=True, zip_file_count=len(names), zip_bytes=ARCHIVE.stat().st_size, zip_sha256=ARCHIVE_HASH, extracted_engine=str((FOLDER / "engine/polska_gurom/game.py").relative_to(WORKSPACE)), engine_reference=str(engine_reference), engine_files_verified=len(engine_files), math_version=health["math_version"])
except BaseException as error:
    report["error"] = f"{type(error).__name__}: {error}"
    raise
finally:
    if process is not None:
        process.terminate()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=5)
    REPORT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    (REPORT_DIRECTORY / "portable_check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
