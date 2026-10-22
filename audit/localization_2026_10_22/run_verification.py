"""Verify the current frontend without network access or changes to reference files."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
GAME = ROOT / 'test-interface-any-start'
TESTS = [
    'test_localization.cjs', 'test_rgs.cjs', 'test_rgs_recovery.cjs',
    'test_platform_currency.cjs', 'test_replay.cjs', 'test_network_logic.cjs',
    'test_audit_fixes.cjs', 'test_autoplay.cjs',
]


def run(name):
    environment = dict(os.environ, PG_QA_OUT_DIR=str(OUT))
    result = subprocess.run(['node', str(GAME / 'qa' / name)], cwd=ROOT,
                            env=environment, capture_output=True, text=True,
                            encoding='utf-8', timeout=180)
    (OUT / (name + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
    return {'test': name, 'passed': result.returncode == 0,
            'exit_code': result.returncode, 'log': name + '.log'}


def hashes(paths):
    return {str(path.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths if path.is_file()}


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        tests = list(pool.map(run, TESTS))
    report = {
        'date': '2026-10-22', 'passed': all(test['passed'] for test in tests),
        'tests': tests,
        'source_sha256': hashes([GAME / 'web' / name for name in
                                 ['app.js', 'rgs-client.js', 'index.html', 'game-layout.js']]),
        'math_sha256_before_packaging': hashes(sorted((GAME / 'stake_math').rglob('*'))),
        'limitations': [
            'Deterministic UI/model/API tests; no browser rendering or real platform acceptance.',
            'Local HTTP tests failed to connect with EACCES in sandbox.',
            'Escalated HTTP test was not executed: automatic approval review could not finish because of an account usage limit.',
        ],
    }
    (OUT / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': report['passed'], 'suites': len(tests), 'tests': tests}, ensure_ascii=False))
    sys.exit(0 if report['passed'] else 1)
