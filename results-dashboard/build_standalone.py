"""Build a portable, complete HTML dashboard and version its local assets."""
import base64
import hashlib
import gzip
import json
import mimetypes
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / 'dist'
data = json.loads((DIST / 'data.json').read_text(encoding='utf-8'))
html = (DIST / 'index.html').read_text(encoding='utf-8')
for asset in ['style.css', 'app.js', 'data-embed.js']:
    digest = hashlib.sha256((DIST / asset).read_bytes()).hexdigest()[:12]
    html = re.sub(re.escape(asset) + r'(?:\?v=[a-z0-9]+)?', asset + '?v=' + digest, html)
(DIST / 'index.html').write_text(html, encoding='utf-8')

bundle = {}
for report in data['reports']:
    src = DIST / report['href']
    raw = src.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == report['sha256']
    mime = mimetypes.guess_type(str(src))[0] or 'application/octet-stream'
    if src.suffix.lower() in {'.json', '.md', '.txt', '.csv'}:
        bundle[report['path']] = {'text': raw.decode('utf-8'), 'mime': mime + ';charset=utf-8'}
    else:
        bundle[report['path']] = {'base64': base64.b64encode(raw).decode(), 'mime': mime}

def inline_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')

standalone = re.sub(r'<link rel="stylesheet" href="style\.css[^\"]*">', lambda _: '<style>' + (DIST / 'style.css').read_text(encoding='utf-8') + '</style>', html)
standalone = re.sub(r'<script src="data-embed\.js[^\"]*" defer></script><script src="app\.js[^\"]*" defer></script>', '', standalone)
standalone = re.sub(r'<a\b[^>]*data-download-html[^>]*>.*?</a>', '<button class="button subtle export-data" aria-label="Pobierz dane JSON">Pobierz dane JSON</button>', standalone, flags=re.S)
app = (DIST / 'app.js').read_text(encoding='utf-8').replace('</script', '<\\/script')
packed = base64.b64encode(gzip.compress(inline_json(bundle).encode('utf-8'), compresslevel=9, mtime=0)).decode()
bootstrap = '''(async()=>{try{
const packed=document.getElementById('embedded-reports').textContent;
const bytes=Uint8Array.from(atob(packed),c=>c.charCodeAt(0));
const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
window.DASHBOARD_REPORTS=JSON.parse(await new Response(stream).text());
'''+app+'''\n}catch(error){document.getElementById('overview-metrics').textContent='Nie udało się otworzyć raportów. Otwórz panel w aktualnej przeglądarce.';}})();'''
scripts = '<script>window.DASHBOARD_DATA=' + inline_json(data) + ';</script><script id="embedded-reports" type="application/octet-stream">' + packed + '</script><script>' + bootstrap + '</script>'
standalone = standalone.replace('</body>', scripts + '</body>')
output = DIST / 'dashboard.html'
output.write_text(standalone, encoding='utf-8')
assert output.stat().st_size < 25_000_000, 'Standalone exceeds static hosting file limit'
delivery = ROOT.parent / 'audit' / 'dashboard_delivery' / 'POLSKA_GUROM_DASHBOARD.html'
delivery.write_bytes(output.read_bytes())
print(json.dumps({'status':'pass', 'reports':len(bundle), 'bytes':output.stat().st_size, 'file':str(delivery)},ensure_ascii=False))
