"""Offline checks of the exact tested release; no network or background processes."""
from pathlib import Path
import hashlib
import json
import re
import zipfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
APP = OUT / 'release/test-interface-any-start'
checks = []


def check(name, condition):
    assert condition, name
    checks.append(name)


original = json.loads((OUT / 'frozen_source_manifest.json').read_text('utf8'))
check('frozen sources unchanged since tests', all(hashlib.sha256((APP / name).read_bytes()).hexdigest() == sha for name, sha in original.items()))
regression = json.loads((OUT / 'regression_summary.json').read_text('utf8'))
check('all 16 suites passed on frozen release', regression['passed'] and len(regression['suites']) == 16 and all(row['exit_code'] == 0 for row in regression['suites']))
autoplay = json.loads((OUT / 'autoplay_logic_results.json').read_text('utf8'))
check('application hash matches actual tested source', autoplay['source_sha256'] == hashlib.sha256((APP / 'web/app.js').read_bytes()).hexdigest())

python_tests = 0
for name in ['test_server', 'test_cascades', 'test_network_faults', 'test_atomicity', 'test_bonus12_api', 'test_rgs_http', 'test_rgs_recovery_http']:
    matches = re.findall(r'Ran (\d+) test', (OUT / (name + '.log')).read_text('utf8'))
    check('test count present: ' + name, len(matches) == 1)
    python_tests += int(matches[0])
js_tests = 0
for name in ['autoplay_logic_results', 'network_logic_results', 'frontend_12fs_results', 'any_start_frontend', 'audit_fixes_frontend', 'rgs_results', 'rgs_recovery_results', 'replay_results', 'platform_currency_results']:
    data = json.loads((OUT / (name + '.json')).read_text('utf8'))
    check('all result checks passed: ' + name, all((data.get('passed') is True) if isinstance(row, str) else (row.get('passed', row.get('success', row.get('status') == 'pass'))) for row in data['checks']))
    js_tests += len(data['checks'])

baseline = json.loads((ROOT / 'audit/fixes_2026_10_21/after_manifest.json').read_text('utf8'))
math_files = [name for name in baseline if name.startswith(('engine/', 'stake_math/'))]
check('engine and mathematical export unchanged', all(hashlib.sha256((APP / name).read_bytes()).hexdigest() == baseline[name] for name in math_files))
check('demo settlement server unchanged', hashlib.sha256((APP / 'server.py').read_bytes()).hexdigest() == baseline['server.py'])
packages = {}
for name in ['POLSKA_GUROM_RGS_FRONTEND.zip', 'POLSKA_GUROM_RGS_TEST.zip', 'POLSKA_GUROM_TESTER.zip']:
    file = APP / name
    with zipfile.ZipFile(file) as archive:
        check(name + ': integrity', archive.testzip() is None)
        names = archive.namelist()
        check(name + ': no Python caches', all('__pycache__' not in item and not item.endswith('.pyc') for item in names))
        for item in names:
            if name.endswith('RGS_FRONTEND.zip'):
                source = APP / 'web' / item
                expected = source.read_text('utf8').replace('<html lang="pl">', '<html lang="pl" data-rgs-only="true">').encode('utf8') if item == 'index.html' else source.read_bytes()
            else:
                expected = (APP / item).read_bytes()
            check(name + ' source bytes: ' + item, archive.read(item) == expected)
        if name.endswith('RGS_FRONTEND.zip'):
            check('static frontend requires platform launch', 'data-rgs-only="true"' in archive.read('index.html').decode('utf8'))
            check('static frontend has no mock server or engine', not any(item.endswith('.py') or item.startswith(('engine/', 'qa/', 'stake_math/')) for item in names))
        if name.endswith('RGS_TEST.zip'):
            check('local test launcher and mock are included', all(item in names for item in ['START_RGS_TEST.cmd', 'qa/rgs_mock_server.py', 'qa/regression_fixtures.json', 'README_RGS_PL.md']))
    packages[name] = {'sha256': hashlib.sha256(file.read_bytes()).hexdigest(), 'files': len(names), 'bytes': file.stat().st_size}

browser = json.loads((OUT / 'browser_server_state.json').read_text('utf8'))
check('observed browser run: one charge and one payout', browser['charges'] == browser['settlements'] == 1 and not browser['active'])
check('observed browser run: correct settled balance and 12 FS', browser['balance']['amount'] == 179450000 and json.loads(browser['event'])['freeCompleted'] == 12)

report = {'passed': True, 'scope': 'Offline verification of frozen tested sources and release ZIPs; earlier browser evidence and local HTTP tests are recorded separately.', 'checks': checks, 'packages': packages, 'python_tests': python_tests, 'javascript_tests': js_tests, 'total_tests': python_tests + js_tests}
(OUT / 'frozen_package_verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
status = {'date': '2026-10-22', 'local_implementation_complete': True, 'local_tests_passed': True, 'total_tests': python_tests + js_tests, 'python_tests': python_tests, 'javascript_tests': js_tests, 'suites': len(regression['suites']), 'new_recovery_logic_tests': 33, 'new_recovery_http_tests': 6, 'engine_math_unchanged': True, 'live_stake_verified': False, 'release_directory': str(APP), 'packages': packages, 'extra_frozen_browser_preview': 'not started: automatic approval review unavailable due to account usage limit'}
(OUT / 'FINAL_STATUS.json').write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps({'passed': True, 'checks': len(checks), 'python_tests': python_tests, 'javascript_tests': js_tests, 'total_tests': python_tests + js_tests, 'packages': packages}, ensure_ascii=False))
