"""Ensure delivered local files and ZIPs are exactly the verified artifacts."""
import hashlib
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CANONICAL = ROOT / "test-interface-any-start"
LEGACY = ROOT / "test-interface"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    audit = load(HERE / "final_verification.json")
    regressions = load(HERE / "regression_summary.json")
    assert audit["success"] and audit["acceptance_required"] and regressions["passed"]
    for name, expected in audit["source_fingerprint"].items():
        assert digest((CANONICAL / "engine/polska_gurom" / name).read_bytes()) == expected, name
    for name, expected in audit["export_sha256"].items():
        assert digest((CANONICAL / "stake_math" / name).read_bytes()) == expected, name
    for name, expected in regressions["source_sha256"].items():
        assert digest((CANONICAL / name).read_bytes()) == expected, name
    assert digest((HERE / "verify_events.py").read_bytes()) == audit["verification_script_sha256"]
    assert digest((HERE / "tuning_targets.json").read_bytes()) == audit["predeclared_plan_sha256"]
    assert digest((CANONICAL / "qa/regression_fixtures.json").read_bytes()) == regressions["fixture_sha256"]
    mirror_files = ["engine/polska_gurom/config.py", "engine/polska_gurom/game.py",
                    "engine/polska_gurom/selection.py", "build_math.py", "high_win_design.py"]
    mirror_files += ["stake_math/" + p.name for p in (CANONICAL / "stake_math").iterdir() if p.is_file()]
    for name in mirror_files:
        assert (CANONICAL / name).read_bytes() == (LEGACY / name).read_bytes(), name
    legacy_qa = load(HERE / "legacy_cap_regressions.json")
    assert legacy_qa["passed"] == legacy_qa["tests_run"] == 45
    assert digest((LEGACY / "web/app.js").read_bytes()) == legacy_qa["source_sha256"]
    for name in ("portable", "legacy_portable"):
        assert load(HERE / name / "portable_check.json")["success"]
    assert (CANONICAL / "engine/polska_gurom/game.py").read_bytes() == (HERE / "baseline/engine/polska_gurom/game.py").read_bytes()
    old_config = (HERE / "baseline/engine/polska_gurom/config.py").read_text(encoding="utf-8")
    new_config = (CANONICAL / "engine/polska_gurom/config.py").read_text(encoding="utf-8")
    assert new_config == old_config.replace('MATH_VERSION = "0.5.0-any-start"', 'MATH_VERSION = "0.6.0-high-wins"')
    archives = {}
    for folder in (CANONICAL, LEGACY):
        path = folder / "POLSKA_GUROM_TESTER.zip"
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            for name in archive.namelist():
                assert archive.read(name) == (folder / name).read_bytes(), name
        archives[str(path.relative_to(ROOT))] = {"sha256": digest(path.read_bytes()), "bytes": path.stat().st_size}
    for suffix in ("RGS_FRONTEND", "RGS_TEST"):
        path = CANONICAL / f"POLSKA_GUROM_{suffix}.zip"
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            config_name = "game-config.json" if suffix == "RGS_FRONTEND" else "web/game-config.json"
            assert json.loads(archive.read(config_name))["math_version"] == "0.6.0-high-wins"
            prefix = "" if suffix == "RGS_FRONTEND" else "web/"
            assert archive.read(prefix + "rgs-client.js") == (CANONICAL / "web/rgs-client.js").read_bytes()
            assert archive.read(prefix + "app.js") == (CANONICAL / "web/app.js").read_bytes()
            if suffix == "RGS_FRONTEND":
                assert "server.py" not in archive.namelist()
                assert all(not n.startswith(("engine/", "stake_math/")) for n in archive.namelist())
            else:
                assert archive.read("qa/regression_fixtures.json") == (CANONICAL / "qa/regression_fixtures.json").read_bytes()
        archives[str(path.relative_to(ROOT))] = {"sha256": digest(path.read_bytes()), "bytes": path.stat().st_size}
    # Review/upload bundle: the actual bank, with its own provenance metadata.
    math_zip = HERE / "POLSKA_GUROM_MATH_v0_6_0_HIGH_WINS.zip"
    with zipfile.ZipFile(math_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted((CANONICAL / "stake_math").iterdir()):
            if path.is_file():
                archive.write(path, path.name)
    with zipfile.ZipFile(math_zip) as archive:
        assert archive.testzip() is None
        for name in archive.namelist():
            assert archive.read(name) == (CANONICAL / "stake_math" / name).read_bytes()
    archives[str(math_zip.relative_to(ROOT))] = {"sha256": digest(math_zip.read_bytes()), "bytes": math_zip.stat().st_size}
    protected = {"unchanged_game_rules": True, "config_change_only_version": True,
                 "sources_directory_present": (ROOT / "sources").is_dir(),
                 "sources_modified_by_task": False}
    evidence = load(ROOT / "decisions/high_wins_2026_10_22/EVIDENCE.json")
    for source, expected in evidence["source_sha256"].items():
        local = source.removeprefix("test-interface-any-start/")
        assert digest((HERE / "baseline" / local).read_bytes()) == expected, source
    provenance_paths = [CANONICAL / "build_math.py", CANONICAL / "high_win_design.py",
                        HERE / "verify_events.py", HERE / "RAPORT_PL.md", HERE / "COMPARISON.json",
                        HERE / "tuning_targets.json", HERE / "final_verification.json",
                        HERE / "regression_summary.json", HERE / "legacy_cap_regressions.json",
                        HERE / "browser_smoke.json", HERE / "bonus_cap_browser.png"]
    report = {"passed": True, "math_version": "0.6.0-high-wins", "same_bank_in_both_local_variants": True,
              "tested_sources_still_current": True, "all_zip_contents_match_current_files": True,
              "protected_baseline": protected, "archives": archives,
              "provenance_sha256": {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in provenance_paths}}
    (HERE / "DELIVERY.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"passed": True, "archives": len(archives), "math_version": report["math_version"]}))


if __name__ == "__main__":
    main()
