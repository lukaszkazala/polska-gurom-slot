import hashlib
import json
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / 'results-dashboard' / 'dist'
BEFORE = ROOT / 'audit/bonus12_fix_2026_10_20/before'
d = json.loads((DIST / 'data.json').read_text(encoding='utf-8'))
checks = []

def check(name, result):
    checks.append({'name': name, 'passed': bool(result)})

check('24 zapisane serie', len(d['simulations']) == 24)
check('166 dowodów', len(d['reports']) == d['summary']['reportCount'] == 166)
check('11 etapów historii', len(d['history']['phases']) == 11)
check('160 mln losowań końcowych', sum(x['rounds'] for x in d['simulations'] if x['kind'] == 'weighted') == 160_000_000)
check('160 mln osobnych rund generatora', sum(x['rounds'] for x in d['simulations'] if x['kind'] == 'natural') == 160_000_000)
regression = [s for s in d['suites'] if s['countedInRegressionTotal']]
check('135 testów w dziewięciu bieżących zestawach regresji', len(regression) == 9 and all(s['current'] and s['version'] == '0.4.1-weighted-12fs' for s in regression) and sum(s['testsCount'] for s in regression) == 135)
check('Wszystkie 135 testów zaliczone', sum(s['passedCount'] for s in regression) == d['summary']['regressionPassed'] == 135)
check('RTP 96% i brak otwartego błędu pokrycia bonusów', d['summary']['exactRtp'] == .96 and d['summary']['criticalOpen'] == 0)
check('12FS ma 24 wyniki i dodatnią masę potwierdzoną dowodami', d['summary']['bonus12Verified'] and any(x['free_spins'] == 12 and x['books'] == 24 and x['weight'] == 4018776 and x['probability'] == 4018776/10**12 for x in d['bonus']['bonus_types']))
check('Unikalne identyfikatory serii, zestawów i raportów', all(len({x['id'] for x in d[key]}) == len(d[key]) for key in ['simulations', 'suites', 'reports']))

def original_matches(report):
    relative = report['path']
    if relative.startswith('baseline-v040/'):
        relative = relative.removeprefix('baseline-v040/')
        candidates = [BEFORE / relative, ROOT / relative]
    else:
        candidates = [ROOT / relative]
    return any(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == report['sha256'] for path in candidates)

check('Każda kopia źródła jest identyczna z zachowanym oryginałem', all((DIST / r['href']).is_file() and hashlib.sha256((DIST / r['href']).read_bytes()).hexdigest() == r['sha256'] and original_matches(r) for r in d['reports']))
paths = {r['path'] for r in d['reports']}
check('Wszystkie odsyłacze historii mają pliki', all(p in paths for h in d['history']['phases'] for p in h.get('sourcepaths', [])))
embed = (DIST / 'data-embed.js').read_text(encoding='utf-8')
check('Dane osadzone zgodne z JSON', json.loads(embed[embed.index('=')+1:].rstrip().rstrip(';')) == d)
check('Polskie znaki bez znaków zastępczych', '\ufffd' not in json.dumps(d, ensure_ascii=False))

class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.assets = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        if tag == 'script' and 'src' in a: self.assets.append(a['src'])
        if tag == 'link' and a.get('rel') == 'stylesheet': self.assets.append(a['href'])

html = Elements()
html.feed((DIST / 'index.html').read_text(encoding='utf-8'))
check('Unikalne identyfikatory HTML', len(html.ids) == len(set(html.ids)))
check('Sześć widoków dostępnych w HTML', all('view-' + s in html.ids for s in ['overview','simulations','bonus','tests','history','reports']))
check('Wszystkie zasoby strony dostępne lokalnie', all((DIST / a.split('?')[0]).is_file() for a in html.assets))
check('Dawne trzy serie ważone są w archiwum, nowe trzy dotyczą 0.4.1', sum(x['kind'] == 'weighted' and x['version'] == '0.4.1-weighted-12fs' for x in d['simulations']) == 3 and sum(x['kind'] == 'historical' and x['id'].startswith('history-v040-weighted-') and x['rounds'] >= 10_000_000 for x in d['simulations']) == 3)
check('139 historycznych plików zachowanych osobno', sum(r['path'].startswith('baseline-v040/') for r in d['reports']) == 139)
result = {'checked_on': '2026-10-20', 'math_version': d['meta']['mathVersion'], 'status': 'pass' if all(c['passed'] for c in checks) else 'fail', 'checks': checks, 'browser_checked': [], 'browser_scope': 'Ten skrypt sprawdza strukturę, dane i pliki. Nie wykonuje testów przeglądarkowych.', 'limitations': ['Nie uruchamiano ponownie dużych symulacji na potrzeby tej kontroli dashboardu; panel przedstawia zapisane nowe wyniki 0.4.1 i osobno historię.', 'Lokalne sprawdzenie dashboardu i plików matematyki nie stanowi zatwierdzenia Stake.']}
(Path(__file__).parent / 'results_v041.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':result['status'],'passed':sum(c['passed'] for c in checks),'total':len(checks)},ensure_ascii=False))
raise SystemExit(0 if result['status'] == 'pass' else 1)
