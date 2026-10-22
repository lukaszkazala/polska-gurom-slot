"""Back up the current target before an explicitly requested v0.2 update."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

workspace = Path(__file__).resolve().parents[1]
source = workspace/"polska_gurom_v0_2"
target = Path(r"D:\Kazaluka_slots\polska_gurom_phase2_v0.1")
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = json.loads((source/"verification"/"file_manifest.json").read_text())
for name, digest in manifest.items():
    if sha(source/name) != digest:
        raise RuntimeError(f"Source manifest mismatch: {name}")
manifest["verification/file_manifest.json"] = sha(source/"verification"/"file_manifest.json")
old_files = {str(p.relative_to(target)).replace("\\", "/"): sha(p)
             for p in sorted(target.rglob("*")) if p.is_file()}
backup_folder = workspace/"backups"
backup_folder.mkdir(exist_ok=True)
number = 1
while True:
    backup = backup_folder/f"polska_gurom_before_v0_2_2026-10-18_{number:02d}.zip"
    if not backup.exists():
        break
    number += 1
with ZipFile(backup,"x",compression=ZIP_DEFLATED) as archive:
    for name in old_files:
        archive.write(target/name, f"{target.name}/{name}")
with ZipFile(backup) as archive:
    if archive.testzip() is not None:
        raise RuntimeError("Backup archive is corrupt")
    for name,digest in old_files.items():
        if hashlib.sha256(archive.read(f"{target.name}/{name}")).hexdigest() != digest:
            raise RuntimeError("Backup verification failed")
plan = dict(source=str(source), target=str(target), source_files=manifest,
            original_files=old_files, backup=str(backup), backup_sha256=sha(backup),
            backup_name=backup.name)
(workspace/"audit"/"deployment_plan.json").write_text(json.dumps(plan,indent=2),encoding="utf-8")
print(json.dumps({"source_files":len(manifest),"original_files":len(old_files),
                  "backup":str(backup),"backup_verified":True},indent=2))
