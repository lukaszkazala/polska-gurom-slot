"""Verify the cap-message delivery against the actual frontend and ZIP contents."""
from pathlib import Path
import hashlib
import json
import zipfile

OUT = Path(__file__).resolve().parent
GAME = OUT.parents[1] / 'test-interface-any-start'


def sha(data):
    return hashlib.sha256(data).hexdigest()


source_hash = sha((GAME / 'web/app.js').read_bytes())
reports = []
for name in ['cap_messages_results.json', 'audit_fixes_frontend.json',
             'rgs_results.json', 'rgs_recovery_results.json', 'replay_results.json',
             'platform_currency_results.json', 'autoplay_logic_results.json',
             'frontend_12fs_results.json']:
    data = json.loads((OUT / name).read_text('utf-8'))
    checks = data['checks']
    assert all(item.get('passed') is True or item.get('status') == 'pass' for item in checks), name
    if name == 'cap_messages_results.json':
        assert data['status'] == 'pass' and data['source_sha256'] == source_hash
    reports.append({'file': name, 'checks': len(checks), 'passed': True})

packages = []
for filename, prefix in [('POLSKA_GUROM_RGS_FRONTEND.zip', ''),
                         ('POLSKA_GUROM_RGS_TEST.zip', 'web/'),
                         ('POLSKA_GUROM_TESTER.zip', 'web/')]:
    package = GAME / filename
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None
        for source in sorted((GAME / 'web').rglob('*')):
            if not source.is_file():
                continue
            name = source.relative_to(GAME / 'web').as_posix()
            expected = source.read_bytes()
            if not prefix and name == 'index.html':
                expected = source.read_text('utf-8').replace(
                    '<html lang="pl">', '<html lang="pl" data-rgs-only="true">').encode('utf-8')
            assert archive.read(prefix + name) == expected, (filename, name)
        if not prefix:
            assert not any(name.endswith('.py') or name.startswith(('engine/', 'qa/'))
                           for name in archive.namelist())
        packages.append({'file': filename, 'sha256': sha(package.read_bytes()),
                         'files': len(archive.namelist()), 'current_frontend': True})

result = {
    'passed': True, 'date': '2026-10-22', 'math_version': '0.5.0-any-start',
    'frontend_source_sha256': source_hash,
    'layout_source_sha256': sha((GAME / 'web/player-layout.css').read_bytes()),
    'tests_passed': sum(report['checks'] for report in reports),
    'reports': reports, 'packages': packages,
    'browser_visual_qa': 'unavailable: in-app browser could not reach the local test server (ERR_CONNECTION_TIMED_OUT)',
    'live_platform_tested': False,
}
(OUT / 'delivery_verification.json').write_text(json.dumps(result, indent=2) + '\n', 'utf-8')
print(json.dumps(result))
