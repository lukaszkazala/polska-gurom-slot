"""Check release ZIP integrity and byte-for-byte web-source equivalence."""
from pathlib import Path
import hashlib
import json
import zipfile

PROJECT = Path(__file__).resolve().parents[2]
ROOT = PROJECT / 'test-interface-any-start'
WEB = ROOT / 'web'
results = {}
for name in ['POLSKA_GUROM_RGS_FRONTEND.zip', 'POLSKA_GUROM_RGS_TEST.zip', 'POLSKA_GUROM_TESTER.zip']:
    package = ROOT / name
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None, name
        checked = []
        for source in sorted(WEB.rglob('*')):
            if not source.is_file():
                continue
            relative = source.relative_to(WEB).as_posix()
            entry = relative if name == 'POLSKA_GUROM_RGS_FRONTEND.zip' else 'web/' + relative
            expected = source.read_bytes()
            if name == 'POLSKA_GUROM_RGS_FRONTEND.zip' and relative == 'index.html':
                expected = source.read_text('utf-8').replace('<html lang="pl">', '<html lang="pl" data-rgs-only="true">').encode('utf-8')
            assert archive.read(entry) == expected, (name, entry)
            checked.append(entry)
        results[name] = {
            'passed': True, 'sha256': hashlib.sha256(package.read_bytes()).hexdigest(),
            'bytes': package.stat().st_size, 'files': len(archive.infolist()),
            'web_sources_checked': checked,
        }
report = {'passed': True, 'math_version': '0.5.0-any-start', 'packages': results}
destination = Path(__file__).with_name('packages.json')
destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', 'utf-8')
print(json.dumps({'passed': True, 'packages': len(results), 'report': str(destination)}))
