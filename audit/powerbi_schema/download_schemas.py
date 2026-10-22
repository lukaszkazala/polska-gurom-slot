import json, urllib.request, urllib.parse, pathlib, collections, time

HERE = pathlib.Path(__file__).parent
ROOT = HERE / 'downloads'
BASE = 'https://raw.githubusercontent.com/microsoft/json-schemas/main/'
SEEDS = [
 'fabric/item/report/definition/visualContainer/1.5.0/schema.json',
 'fabric/item/report/definition/visualContainer/1.4.0/schema.json',
 'fabric/item/report/definition/report/1.2.0/schema.json',
 'fabric/item/report/definition/page/1.3.0/schema.json',
 'fabric/item/report/definition/pagesMetadata/1.0.0/schema.json',
 'fabric/item/report/definition/versionMetadata/1.0.0/schema.json',
 'fabric/item/report/definitionProperties/2.0.0/schema.json',
 'fabric/pbip/pbipProperties/1.0.0/schema.json',
]
def refs(obj):
 if isinstance(obj, dict):
  for k,v in obj.items():
   if k == '$ref' and isinstance(v,str): yield v
   else: yield from refs(v)
 elif isinstance(obj,list):
  for v in obj: yield from refs(v)
q = collections.deque(SEEDS); seen = set(); manifest = []
while q:
 path = q.popleft()
 if path in seen: continue
 seen.add(path)
 target = ROOT / path
 try:
  content = urllib.request.urlopen(BASE + path,timeout=25).read()
  obj = json.loads(content)
  target.parent.mkdir(exist_ok=True,parents=True)
  target.write_bytes(content)
  manifest.append({'path':path,'url':BASE+path,'bytes':len(content),'status':'downloaded'})
  for ref in refs(obj):
   if ref.startswith('#'): continue
   ur = urllib.parse.urljoin('https://developer.microsoft.com/json-schemas/' + path, ref).split('#')[0]
   if '/json-schemas/' not in ur: continue
   nextpath = ur.split('/json-schemas/',1)[1]
   if nextpath not in seen:q.append(nextpath)
 except Exception as exc:
  manifest.append({'path':path,'url':BASE+path,'error':str(exc),'status':'error'})
  print('ERROR',path,str(exc))
(HERE/'schema_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({'downloaded':sum(x['status']=='downloaded' for x in manifest),'errors':sum(x['status']=='error' for x in manifest)}))
