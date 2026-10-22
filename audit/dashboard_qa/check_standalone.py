"""Verify the portable HTML contains the original data and all source bytes."""
import base64
import gzip
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path

root = Path(__file__).resolve().parents[2]
dist = root / 'results-dashboard' / 'dist'
text = (dist / 'dashboard.html').read_text(encoding='utf-8')

class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.scripts = []
        self.external = []
        self.script_id = None
        self.compressed = ''
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'script':
            self.in_script = True
            self.script_id = a.get('id')
            if 'src' in a: self.external.append(a['src'])
        if tag == 'link' and a.get('rel') == 'stylesheet':
            self.external.append(a.get('href'))
    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_script = False
            self.script_id = None
    def handle_data(self, data):
        if self.in_script:
            self.scripts.append(data)
            if self.script_id == 'embedded-reports':self.compressed += data

p = Scripts()
p.feed(text)
assert not p.external, p.external
script = next(s for s in p.scripts if s.startswith('window.DASHBOARD_DATA='))
d = json.loads(script.removeprefix('window.DASHBOARD_DATA=').rstrip(';'))
bundle = json.loads(gzip.decompress(base64.b64decode(p.compressed)))
assert d == json.loads((dist / 'data.json').read_text(encoding='utf-8'))
assert len(bundle) == len(d['reports'])
for report in d['reports']:
    item = bundle[report['path']]
    raw = base64.b64decode(item['base64']) if 'base64' in item else item['text'].encode('utf-8')
    assert hashlib.sha256(raw).hexdigest() == report['sha256'], report['path']
assert '\ufffd' not in text
assert text.count('id="view-') == 6
result = {'status':'pass','sourceReports':len(bundle),'copiesByteIdentical':True,'embeddedDataMatchesJson':True,'externalScriptOrStyleDependencies':0,'singleFileBytes':(dist / 'dashboard.html').stat().st_size,'bundleCompression':'gzip+base64; all raw report bytes preserved','mathVersion':d['meta']['mathVersion']}
(Path(__file__).parent / 'standalone_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
