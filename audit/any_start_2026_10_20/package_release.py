from pathlib import Path
from fractions import Fraction
import csv
import hashlib
import json
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
ACTIVE = ROOT / "test-interface"
AUDIT = Path(__file__).resolve().parent
sys.path.insert(0,str(ACTIVE))
import package_demo
manifest = json.loads((ACTIVE/"stake_math/selection.json").read_text())
assert manifest["math_version"] == "0.5.0-any-start"
for name,digest in manifest["source_fingerprint"].items():
    assert hashlib.sha256((ACTIVE/"engine/polska_gurom"/name).read_bytes()).hexdigest() == digest
rows = [tuple(map(int,r)) for r in csv.reader((ACTIVE/"stake_math/lookUpTable_base_0.csv").open())]
assert Fraction(sum(w*p for _,w,p in rows),sum(w for _,w,_ in rows)*100) == Fraction(24,25)
package_demo.OUTPUT = ACTIVE / "POLSKA_GUROM_v0_5_PODGLAD.zip"
release = package_demo.build()
with zipfile.ZipFile(release,"a",zipfile.ZIP_DEFLATED) as z:
    z.write(ACTIVE/"START_UX.cmd","START_UX.cmd")
    z.write(AUDIT/"player-desktop.png","PODGLAD_GRY.png")
with zipfile.ZipFile(release) as z:
    assert z.testzip() is None
    for path in ["web/game-layout.js","web/player-layout.css","web/assets/art/symbole-specjalne.png","START_UX.cmd","PODGLAD_GRY.png"]:
        assert path in z.namelist()
    for name,digest in manifest["source_fingerprint"].items():
        assert hashlib.sha256(z.read("engine/polska_gurom/"+name)).hexdigest() == digest
report = {"passed":True,"math_version":manifest["math_version"],"rtp_exact":"24/25", "books":len(rows),
          "release":str(release),"bytes":release.stat().st_size,
          "sha256":hashlib.sha256(release.read_bytes()).hexdigest()}
(AUDIT/"release.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
