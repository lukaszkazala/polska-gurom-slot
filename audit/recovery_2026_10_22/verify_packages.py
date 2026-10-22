from pathlib import Path
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
import zipfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
APP = ROOT / 'test-interface-any-start'
checks = []


def check(name, condition):
    assert condition, name
    checks.append(name)


packages = {}
for name in ['POLSKA_GUROM_RGS_FRONTEND.zip', 'POLSKA_GUROM_RGS_TEST.zip', 'POLSKA_GUROM_TESTER.zip']:
    file = APP / name
    sha = hashlib.sha256(file.read_bytes()).hexdigest()
    with zipfile.ZipFile(file) as archive:
        check(name + ': zip integrity', archive.testzip() is None)
        names = archive.namelist()
        check(name + ': no cache files', all('__pycache__' not in p and not p.endswith('.pyc') for p in names))
        if name.endswith('RGS_FRONTEND.zip'):
            check('frontend: static only', not any(p.endswith('.py') or p.startswith(('stake_math/', 'qa/', 'engine/')) for p in names))
            check('frontend: no demo fallback', 'data-rgs-only="true"' in archive.read('index.html').decode('utf8'))
            for item in names:
                expected = (APP / 'web' / item).read_bytes()
                if item == 'index.html':
                    expected = (APP / 'web' / item).read_text('utf8').replace('<html lang="pl">', '<html lang="pl" data-rgs-only="true">').encode('utf8')
                check('frontend source: ' + item, expected == archive.read(item))
        else:
            for item in names:
                check(name + ' source: ' + item, archive.read(item) == (APP / item).read_bytes())
        if name.endswith('RGS_TEST.zip'):
            folder = OUT / ('portable-rgs-' + sha[:12])
            folder.mkdir(exist_ok=True)
            for item in names:
                check('safe archive path: ' + item, (folder / item).resolve().is_relative_to(folder.resolve()))
            archive.extractall(folder)
    packages[name] = {'sha256': sha, 'files': len(names), 'bytes': file.stat().st_size}

baseline = json.loads((ROOT / 'audit/fixes_2026_10_21/after_manifest.json').read_text('utf8'))
math_files = [name for name in baseline if name.startswith(('engine/', 'stake_math/'))]
check('engine and mathematical export unchanged', all(hashlib.sha256((APP / name).read_bytes()).hexdigest() == baseline[name] for name in math_files))
check('local settlement server unchanged', hashlib.sha256((APP / 'server.py').read_bytes()).hexdigest() == baseline['server.py'])

with socket.socket() as port_socket:
    port_socket.bind(('127.0.0.1', 0))
    port = port_socket.getsockname()[1]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
with (OUT / 'portable_rgs_server.log').open('w', encoding='utf8') as log:
    process = subprocess.Popen([sys.executable, '-I', '-B', str(folder / 'qa/rgs_mock_server.py'), '--port', str(port), '--no-browser'], cwd=folder, env=env, stdout=log, stderr=subprocess.STDOUT)
    try:
        for _ in range(100):
            try:
                urllib.request.urlopen(f'http://127.0.0.1:{port}/game-config.json', timeout=1).close()
                break
            except OSError:
                if process.poll() is not None:
                    raise RuntimeError((OUT / 'portable_rgs_server.log').read_text('utf8'))
                time.sleep(0.05)
        probe = subprocess.run(['node', str(APP / 'qa/test_rgs_http.cjs'), f'http://127.0.0.1:{port}'], capture_output=True, text=True, env=env, timeout=40)
        check('extracted RGS test package runs in isolation', probe.returncode == 0)
        (OUT / 'portable_rgs_http_result.json').write_text(probe.stdout, encoding='utf8')
    finally:
        process.terminate()
        process.wait(timeout=10)

browser=json.load(urllib.request.urlopen('http://127.0.0.1:8804/__rgs-test/state',timeout=5))
check('browser: one bet and one settlement after loss, new tab and refresh', browser['charges']==1 and browser['settlements']==1 and not browser['active'] and browser['balance']['amount']==179450000)
check('browser: recovered bonus completed all 12 free spins', json.loads(browser['event'])['freeCompleted']==12)
(OUT/'browser_server_state.json').write_text(json.dumps(browser,indent=2),encoding='utf8')
report = {'passed': True, 'packages': packages, 'checked_engine_math_files': len(math_files), 'checks': checks}
(OUT / 'package_verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps({'passed': True, 'checks': len(checks), 'packages': packages}, ensure_ascii=False))
