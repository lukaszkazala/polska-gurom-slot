from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[2]
GAME = ROOT / 'test-interface-any-start'
OUT = Path(__file__).resolve().parent
checks = []
packages = []
for filename, prefix in [('POLSKA_GUROM_RGS_FRONTEND.zip', ''), ('POLSKA_GUROM_RGS_TEST.zip', 'web/')]:
    package = GAME / filename
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None
        for source in sorted((GAME / 'web').rglob('*')):
            if not source.is_file():
                continue
            relative = source.relative_to(GAME / 'web').as_posix()
            expected = source.read_bytes()
            if not prefix and relative == 'index.html':
                expected = source.read_text('utf-8').replace('<html lang="pl">', '<html lang="pl" data-rgs-only="true">').encode('utf-8')
            assert archive.read(prefix + relative) == expected, (filename, relative)
        if prefix:
            for relative in ['qa/rgs_mock_server.py', 'README_WALUTY_PL.md', 'README_RGS_PL.md']:
                assert archive.read(relative) == (GAME / relative).read_bytes()
        else:
            assert not any(name.startswith(('engine/', 'qa/')) or name.endswith('.py') for name in archive.namelist())
        checks.append({'package': filename, 'passed': True, 'files': len(archive.namelist())})
    packages.append({'file': filename, 'sha256': hashlib.sha256(package.read_bytes()).hexdigest()})

reports = []
for filename in ['platform_currency_results.json', 'rgs_results.json', 'rgs_recovery_results.json', 'audit_fixes_frontend.json', 'autoplay_logic_results.json', 'frontend_12fs_results.json', 'any_start_frontend.json']:
    data = json.loads((OUT / filename).read_text('utf-8'))
    assert data['passed'], filename
    reports.append({'file': filename, 'passed': True, 'checks': len(data['checks'])})
result = {'passed': True, 'date': '2026-10-22', 'packages': packages, 'package_checks': checks, 'test_reports': reports,
          'frontend_source_sha256': hashlib.sha256((GAME / 'web/app.js').read_bytes()).hexdigest(),
          'transport_source_sha256': hashlib.sha256((GAME / 'web/rgs-client.js').read_bytes()).hexdigest(),
          'live_platform_acceptance': False}
(OUT / 'delivery_verification.json').write_text(json.dumps(result, indent=2) + '\n', 'utf-8')
print(json.dumps(result))
