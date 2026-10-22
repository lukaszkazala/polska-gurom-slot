"""Read-only source audit, isolated deterministic rebuild and packaging checks."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import sys
import time
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "test-interface-any-start"
OUT = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def import_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def snapshot():
    return {p.relative_to(APP).as_posix(): {"sha256": digest(p.read_bytes()), "bytes": p.stat().st_size}
            for p in sorted(APP.rglob("*")) if p.is_file()
            and "__pycache__" not in p.parts and "qa" not in p.relative_to(APP).parts
            and p.suffix != ".zip"}


def main():
    start = time.perf_counter()
    before = snapshot()
    (OUT / "source_manifest.json").write_text(json.dumps(before, indent=2), encoding="utf-8")
    compiler = import_path("audited_compiler", APP / "build_math.py")
    compiler.HERE = OUT
    compiler.TARGET = OUT / "rebuilt_math"
    compiler.build()
    compared = {}
    for p in sorted((APP / "stake_math").iterdir()):
        if not p.is_file():
            continue
        rebuilt = compiler.TARGET / p.name
        if p.name == "mathematics.json":
            original_json = json.loads(p.read_text())
            rebuilt_json = json.loads(rebuilt.read_text())
            original_json.pop("elapsed_seconds", None)
            rebuilt_json.pop("elapsed_seconds", None)
            matches = original_json == rebuilt_json
            comparison = "all JSON values except elapsed_seconds"
        else:
            matches = p.read_bytes() == rebuilt.read_bytes()
            comparison = "byte-for-byte"
        compared[p.name] = {"matches": matches, "comparison": comparison,
                            "original_sha256": digest(p.read_bytes()),
                            "rebuilt_sha256": digest(rebuilt.read_bytes())}
    packager = import_path("audited_packager", APP / "package_demo.py")
    packager.OUTPUT = OUT / "POLSKA_GUROM_AUDITED_DEMO.zip"
    archive_path = packager.build()
    with zipfile.ZipFile(archive_path) as archive:
        entries = archive.namelist()
        archive_checks = {
            "crc_error": archive.testzip(),
            "file_count": len(entries),
            "duplicate_paths": len(entries) - len(set(entries)),
            "all_packaged_files_match_audited_source": all(
                (APP / name).is_file() and archive.read(name) == (APP / name).read_bytes()
                for name in entries),
            "has_start_ux": "START_UX.cmd" in entries,
            "has_start": "START.cmd" in entries,
            "has_build_math": "build_math.py" in entries,
            "has_test_suite": any(name.startswith("qa/") for name in entries),
            "sha256": digest(archive_path.read_bytes()),
            "bytes": archive_path.stat().st_size,
        }
    result = {
        "version": "0.5.0-any-start",
        "rebuild_checks": compared,
        "rebuild_identical": all(x["matches"] for x in compared.values()),
        "package": archive_checks,
        "source_unchanged": before == snapshot(),
        "elapsed_seconds": time.perf_counter() - start,
        "note": "New audit demo archive, not proof of an earlier delivered or uploaded ZIP.",
    }
    (OUT / "release_results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
