"""Build a separately named portable UX tester and verify its art mapping."""
from pathlib import Path
import hashlib
import json
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "test-interface"))
import package_demo

AUDIT = Path(__file__).resolve().parent
before = json.loads((AUDIT / "math_before.json").read_text())
assert all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in before.items())
browser = json.loads((AUDIT / "browser_themes.json").read_text())
assert len(browser) == 3
assert all(row["cells"] == row["art"] == row["clips"] == 15 for row in browser)
assert all(row["rows"] == 8 and row["active"] == 10 and row["catalog"] == 18 for row in browser)
assert all(row["payouts"] == browser[0]["payouts"] for row in browser)

package_demo.OUTPUT = ROOT / "test-interface" / "POLSKA_GUROM_UX_18_SYMBOLI.zip"
release = package_demo.build()
with zipfile.ZipFile(release, "a", compression=zipfile.ZIP_DEFLATED) as archive:
    archive.write(ROOT / "test-interface" / "START_UX.cmd", "START_UX.cmd")
with zipfile.ZipFile(release) as archive:
    assert archive.testzip() is None
    for name in ["web/art-catalog.js", "web/art-theme.css", "web/assets/art/polskie-motywy.png", "web/assets/art/rama.png", "START_UX.cmd"]:
        assert name in archive.namelist()
    for path, digest in before.items():
        relative = Path(path).relative_to("test-interface").as_posix()
        assert hashlib.sha256(archive.read(relative)).hexdigest() == digest

report = {"passed": True, "math_files_unchanged": len(before), "themes": 3,
          "artwork_catalog": 18, "game_symbols_per_theme": 10,
          "browser_checks": "18 catalogue entries, 15 visible sprites and clipping paths, 8 payout rows, 10 active artwork entries per theme; all payout cells identical across themes",
          "release": str(release), "release_bytes": release.stat().st_size,
          "sha256": hashlib.sha256(release.read_bytes()).hexdigest()}
(AUDIT / "release_checks.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
