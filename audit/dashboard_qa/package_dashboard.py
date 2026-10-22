import json
import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / 'results-dashboard' / 'dist'
OUT = ROOT / 'audit' / 'dashboard_delivery'
OUT.mkdir(exist_ok=True)
archive = OUT / 'POLSKA_GUROM_DASHBOARD.zip'
data = json.loads((DIST / 'data.json').read_text(encoding='utf-8'))
assert data['meta']['mathVersion'] == '0.4.1-weighted-12fs'
assert len(data['reports']) == 166
assets = ['index.html', 'style.css', 'app.js', 'data-embed.js', 'data.json', 'dashboard.html']
sources = {name: DIST / name for name in assets}
for report in data['reports']:
    relative = report['href']
    assert relative.startswith('reports/') and '..' not in Path(relative).parts
    source = DIST / relative
    assert source.resolve().is_relative_to(DIST.resolve())
    assert hashlib.sha256(source.read_bytes()).hexdigest() == report['sha256']
    sources[relative] = source
sources['CZYTAJ_MNIE.md'] = ROOT / 'results-dashboard/README_PL.md'
for src, dest in [
    ('audit/dashboard_qa/RAPORT_V041_PL.md', 'kontrola/RAPORT_V041_PL.md'),
    ('audit/dashboard_qa/results_v041.json', 'kontrola/results_v041.json'),
    ('audit/dashboard_qa/standalone_results.json', 'kontrola/standalone_results.json'),
    ('audit/bonus12_fix_2026_10_20/dashboard_update_results.json', 'kontrola/dashboard_update_results.json'),
]:
    sources[dest] = ROOT / src
for filename in ['results_v041.json', 'standalone_results.json']:
    report = json.loads((ROOT / 'audit/dashboard_qa' / filename).read_text(encoding='utf-8'))
    assert report['status'] == 'pass'
    assert report.get('math_version', report.get('mathVersion')) == data['meta']['mathVersion']
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for relative, source in sorted(sources.items()):
        z.write(source, relative)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    names = z.namelist()
    assert len(names) == len(set(names)) == len(sources)
    assert set(names) == set(sources)
    assert {n for n in names if n.startswith('reports/')} == {r['href'] for r in data['reports']}
    assert sum(n.startswith('reports/') for n in names) == 166
    assert not any('.git/' in n or '.openai/' in n for n in names)
    assert all(z.read(relative) == source.read_bytes() for relative, source in sources.items())
result = {'archive': str(archive), 'bytes': archive.stat().st_size, 'status': 'pass',
          'math_version': data['meta']['mathVersion'], 'files': len(sources), 'activeReports': 166,
          'unregisteredReportCopiesIncluded': 0, 'zipIntegrityChecked': True,
          'allMembersMatchSources': True, 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}
(ROOT / 'audit/dashboard_qa/package_results_v041.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
