"""Verify audit links and confirm implementation hashes remain unchanged."""
import hashlib
import json
from pathlib import Path
import re

OUTPUT = Path(__file__).resolve().parent
ROOT = OUTPUT.parents[1]
manifest = json.loads((OUTPUT / "delivery_checks.json").read_text(encoding="utf-8"))
changed = []
for name, expected in manifest["source_sha256"].items():
    path = ROOT / name
    actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    if actual != expected:
        changed.append(name)

report = OUTPUT / "RAPORT_STAKE_ENGINE_PL.md"
missing = []
link_count = 0


def absolute_link(match):
    global link_count
    label, target = match.group(1), match.group(2)
    if target.startswith(("https://", "http://", "#")):
        return match.group(0)
    path = Path(target)
    if not path.is_absolute():
        path = (OUTPUT / path).resolve()
    link_count += 1
    if not path.exists():
        missing.append(str(path))
    return f"[{label}]({path.as_posix()})"


text = report.read_text(encoding="utf-8")
text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", absolute_link, text)
report.write_text(text, encoding="utf-8")
result = {"implementation_source_hashes_unchanged": not changed,
          "source_files_checked": len(manifest["source_sha256"]),
          "changed_files": changed, "report_local_links_checked": link_count,
          "missing_link_targets": missing,
          "live_browser_check": "Not completed: local loopback unreachable from available browser",
          "remote_stake_validation": "Not performed"}
(OUTPUT / "final_verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(1 if changed or missing else 0)
