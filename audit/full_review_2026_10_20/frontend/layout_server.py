"""Read-only layout fixture: original web assets, GET API samples, no betting POST."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import build_opener, ProxyHandler
ROOT=Path(__file__).resolve().parents[3]
WEB=ROOT/'test-interface-any-start/web'
OUT=Path(__file__).resolve().parent
opener=build_opener(ProxyHandler({}))
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(WEB),**kwargs)
    def do_GET(self):
        if self.path.startswith('/__audit'):
            body=(OUT/'layout_probe.html').read_bytes().replace(b'http://127.0.0.1:8795/',b'/')
            kind='text/html; charset=utf-8'
        elif self.path in ('/api/config','/api/state'):
            with opener.open('http://127.0.0.1:8795'+self.path,timeout=5) as r:body=r.read()
            kind='application/json'
        else:return super().do_GET()
        self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
ThreadingHTTPServer(('127.0.0.1',8797),Handler).serve_forever()
