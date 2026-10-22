"""Read-only inspection of current publication artifacts and distributed ZIPs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check_zip(path, mapping):
    if not path.exists():
        return {"exists": False}
    with zipfile.ZipFile(path) as archive:
        files = {item.filename: item for item in archive.infolist() if not item.is_dir()}
        differences, checked, unmapped = [], 0, []
        for name in files:
            local = mapping(name)
            if local is None:
                unmapped.append(name)
                continue
            checked += 1
            if not local.is_file():
                differences.append({"entry": name, "status": "local file missing"})
            elif digest(archive.read(name)) != digest(local.read_bytes()):
                differences.append({"entry": name, "status": "contents differ"})
        return {"exists": True, "sha256": digest(path.read_bytes()),
                "crc_failure": archive.testzip(), "entries": len(files),
                "compared_files": checked, "differences": differences,
                "unmapped_entries": unmapped}


def tester_path(name):
    if name.startswith("engine/polska_gurom/"):
        return ROOT / "polska_gurom_v0_2" / "polska_gurom" / name.removeprefix("engine/polska_gurom/")
    return ROOT / "test-interface" / name


def engine_path(name):
    return ROOT / name if name.startswith("polska_gurom_v0_2/") else ROOT / "polska_gurom_v0_2" / name


def main():
    relevant = [ROOT / "polska_gurom_v0_2", ROOT / "test-interface"]
    files = [p for folder in relevant for p in folder.rglob("*") if p.is_file()
             and "__pycache__" not in p.parts and "qa" not in p.parts]
    code_files = [p for p in files if p.suffix in {".py", ".js", ".html", ".css", ".json", ".md", ".toml", ".cmd"}]
    report = {
        "date": "2026-10-19",
        "scope": "Current local engine and interface; no remote ACP/RGS validation",
        "publication_artifacts": {
            "index_json": [str(p.relative_to(ROOT)) for p in files if p.name == "index.json"],
            "books": [str(p.relative_to(ROOT)) for p in files if p.name.endswith((".jsonl.zst", ".jsonl.zstd"))],
            "lookup_csv": [str(p.relative_to(ROOT)) for p in files if p.suffix.lower() == ".csv"],
        },
        "archives": {
            "engine": check_zip(ROOT / "polska_gurom_v0_2.zip", engine_path),
            "tester": check_zip(ROOT / "test-interface" / "POLSKA_GUROM_TESTER.zip", tester_path),
        },
        "source_sha256": {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in sorted(code_files)},
    }
    (OUT / "delivery_checks.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "source_sha256"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
