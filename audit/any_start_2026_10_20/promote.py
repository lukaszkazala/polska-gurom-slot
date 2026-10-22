"""Install only the audited local release; preserve the pre-change ZIP."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[2]
AUDIT = Path(__file__).resolve().parent
STAGE = ROOT / "test-interface-any-start"
ACTIVE = ROOT / "test-interface"
report = json.loads((AUDIT/"independent_audit.json").read_text())
assert report["passed"] and report["complete_books_checked"] == 100049
assert report["rtp_exact_fraction"] == "24/25"
assert json.loads((AUDIT/"any_start_frontend.json").read_text())["passed"]

with zipfile.ZipFile(AUDIT/"before_change.zip") as backup:
    unexpected = [name for name in backup.namelist()
                  if (ACTIVE/name).read_bytes() != backup.read(name)]
assert not unexpected, f"Active files changed since baseline: {unexpected}"

for folder in ("web","engine","stake_math","qa"):
    for source in (STAGE/folder).rglob("*"):
        if not source.is_file() or "__pycache__" in source.parts:
            continue
        target = ACTIVE/source.relative_to(STAGE)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
for name in ("server.py","build_math.py","package_demo.py","README_PL.md","START.cmd","START_UX.cmd","test_server.py"):
    shutil.copy2(STAGE/name, ACTIVE/name)

manifest = json.loads((ACTIVE/"stake_math/selection.json").read_text())
for name, digest in manifest["source_fingerprint"].items():
    assert hashlib.sha256((ACTIVE/"engine/polska_gurom"/name).read_bytes()).hexdigest() == digest
print("Installed audited 0.5.0-any-start release into the active tester.")
