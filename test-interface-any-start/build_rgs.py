"""Produce a static RGS frontend; do not ship the demo server or local outcome selector."""
from pathlib import Path
import hashlib
import json
import sys
import zipfile

sys.dont_write_bytecode = True
import server

ROOT = Path(__file__).resolve().parent


def build():
    handler = object.__new__(server.InterfaceHandler)
    collected = []
    handler._json = lambda data: collected.append(data)
    handler._get('/api/config')
    config = collected[0]
    config.pop('bet_options_cents')
    config.pop('initial_balance_cents')
    (ROOT / 'web/game-config.json').write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    destination = ROOT / 'POLSKA_GUROM_RGS_FRONTEND.zip'
    temporary = destination.with_suffix('.zip.tmp')
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for file in sorted((ROOT / 'web').rglob('*')):
                if file.is_file():
                    name = file.relative_to(ROOT / 'web').as_posix()
                    if name == 'index.html':
                        archive.writestr(name, file.read_text('utf-8').replace('<html lang="pl">', '<html lang="pl" data-rgs-only="true">'))
                    else:
                        archive.write(file, name)
        with zipfile.ZipFile(temporary) as archive:
            assert archive.testzip() is None
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    print(json.dumps({'output': str(destination), 'math_version': config['math_version'], 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}))
    test_package = ROOT / 'POLSKA_GUROM_RGS_TEST.zip'
    with zipfile.ZipFile(test_package, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for file in sorted((ROOT / 'web').rglob('*')):
            if file.is_file():
                archive.write(file, file.relative_to(ROOT).as_posix())
        for name in ['server.py', 'START_RGS_TEST.cmd', 'README_RGS_PL.md', 'README_WALUTY_PL.md', 'README_JEZYKI_PL.md', 'qa/rgs_mock_server.py', 'qa/regression_fixtures.json']:
            archive.write(ROOT / name, name)
        for file in sorted((ROOT / 'engine').rglob('*.py')):
            archive.write(file, file.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(test_package) as archive:
        assert archive.testzip() is None
    print(json.dumps({'local_test_package': str(test_package), 'sha256': hashlib.sha256(test_package.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    build()
