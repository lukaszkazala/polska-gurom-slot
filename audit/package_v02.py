"""Package only the complete v0.2 deliverable, and verify its integrity."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import zipfile

WORKSPACE = Path(__file__).resolve().parent.parent
PROJECT = WORKSPACE / "polska_gurom_v0_2"
REFERENCE = Path(r"D:\Kazaluka_slots\polska_gurom_phase2_v0.1")
baseline = json.loads((WORKSPACE/"audit"/"original_hashes.json").read_text())
current = {str(p.relative_to(REFERENCE)): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in sorted(REFERENCE.rglob("*")) if p.is_file()}
if baseline != current:
    raise RuntimeError("Original reference changed; inspect before claiming preservation")
(PROJECT/"verification"/"original_reference_unchanged.json").write_text(
    json.dumps({"verified": True, "files": len(current), "sha256": current},indent=2),encoding="utf-8")

files = [p for p in sorted(PROJECT.rglob("*"))
         if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
         and p.name != "file_manifest.json"]
manifest = {str(p.relative_to(PROJECT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files}
manifest_path = PROJECT/"verification"/"file_manifest.json"
manifest_path.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
files.append(manifest_path)
archive_path = WORKSPACE/"polska_gurom_v0_2.zip"
with zipfile.ZipFile(archive_path,"w",compression=zipfile.ZIP_DEFLATED) as archive:
    for file in files:
        archive.write(file, str(file.relative_to(WORKSPACE)).replace("\\", "/"))
with zipfile.ZipFile(archive_path) as archive:
    if archive.testzip() is not None:
        raise RuntimeError("Archive failed integrity verification")
    for name, digest in manifest.items():
        payload = archive.read("polska_gurom_v0_2/"+name)
        if hashlib.sha256(payload).hexdigest() != digest:
            raise RuntimeError(f"Archive hash mismatch: {name}")
print(json.dumps({"archive":str(archive_path), "archive_bytes":archive_path.stat().st_size,
                  "files": len(files), "original_reference_files_unchanged": len(current),
                  "archive_integrity": "passed"},indent=2))
