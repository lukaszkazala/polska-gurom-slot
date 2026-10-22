"""Build stable replay deliveries and freeze them away from shared rolling ZIPs."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile

PROJECT = Path(__file__).resolve().parents[2]
ROOT = PROJECT / 'test-interface-any-start'
AUDIT = Path(__file__).resolve().parent

def sha(data):
    return hashlib.sha256(data).hexdigest()

def snapshot():
    files = []
    for folder in ['web', 'engine', 'stake_math']:
        files.extend(p for p in (ROOT / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc', '.pyo'})
    files.extend(p for p in ROOT.iterdir() if p.is_file() and p.suffix in {'.py', '.cmd', '.md', '.json'})
    files.extend(ROOT / name for name in ['server.py', 'START.cmd', 'START_UX.cmd', 'START_RGS_TEST.cmd', 'README_PL.md', 'README_RGS_PL.md', 'qa/rgs_mock_server.py', 'qa/regression_fixtures.json'])
    return {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in sorted(files)}

build_logs = []
for attempt in range(2):
    before = snapshot()
    for script in ['build_rgs.py', 'package_demo.py']:
        result = subprocess.run([sys.executable, str(ROOT / script)], check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        build_logs.append({'attempt': attempt + 1, 'script': script, 'stdout': result.stdout, 'stderr': result.stderr})
    after = snapshot()
    if before == after:
        break
    if attempt == 1:
        changed = sorted(set(before) ^ set(after) | {k for k in before.keys() & after.keys() if before[k] != after[k]})
        raise RuntimeError('Source changed during both build attempts: ' + ', '.join(changed))
else:
    raise RuntimeError('Could not stabilize build')

names = {
    'POLSKA_GUROM_TESTER.zip': 'POLSKA_GUROM_REPLAY_TESTER.zip',
    'POLSKA_GUROM_RGS_FRONTEND.zip': 'POLSKA_GUROM_REPLAY_RGS_FRONTEND.zip',
    'POLSKA_GUROM_RGS_TEST.zip': 'POLSKA_GUROM_REPLAY_RGS_TEST.zip',
}
packages = {}
for rolling, frozen in names.items():
    source = ROOT / rolling
    destination = AUDIT / frozen
    shutil.copy2(source, destination)
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None, frozen
        checked = []
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            key = 'web/' + entry.filename if rolling == 'POLSKA_GUROM_RGS_FRONTEND.zip' else entry.filename
            assert key in after, (frozen, key)
            expected = after[key]
            if rolling == 'POLSKA_GUROM_RGS_FRONTEND.zip' and entry.filename == 'index.html':
                expected = expected.decode('utf-8').replace('\r\n', '\n').replace('<html lang="pl">', '<html lang="pl" data-rgs-only="true">').encode('utf-8')
            assert archive.read(entry) == expected, (frozen, entry.filename)
            checked.append(entry.filename)
        packages[frozen] = {'passed': True, 'path': str(destination), 'sha256': sha(destination.read_bytes()), 'bytes': destination.stat().st_size, 'files': len(checked), 'sources_checked': checked}

# Frozen artifacts cannot be replaced by another chat rebuilding rolling deliveries.
assert snapshot() == after, 'Source changed while validating the frozen packages'
report = {'passed': True, 'math_version': '0.5.0-any-start', 'stable_build_attempt': attempt + 1, 'frozen': True,
          'source_sha256': {k: sha(v) for k, v in after.items()}, 'packages': packages, 'build_logs': build_logs}
(AUDIT / 'packages.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', 'utf-8')
print(json.dumps({'passed': True, 'stable_build_attempt': attempt + 1, 'packages': packages}, ensure_ascii=False))
