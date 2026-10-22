"""Temporary browser fault relay. Control file affects this isolated lab only."""
from __future__ import annotations
import argparse
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import server

CONTROL = HERE / "browser_fault_control.json"
EVENTS = HERE / "browser_fault_events.jsonl"


class Lab(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, port):
        server.COOKIE_NAME = "pg_network_qa"
        self.guard = threading.Lock()
        self.backend = server.InterfaceServer(("127.0.0.1", 0))
        threading.Thread(target=self.backend.serve_forever, daemon=True).start()
        super().__init__(("127.0.0.1", port), Handler)

    def fault(self):
        with self.guard:
            try:
                rule = json.loads(CONTROL.read_text())
            except (OSError, ValueError):
                return "off"
            if rule.get("remaining", 0) <= 0:
                return "off"
            rule["remaining"] -= 1
            CONTROL.write_text(json.dumps(rule))
            return rule["fault"]

    def log(self, entry):
        with self.guard:
            with EVENTS.open("a",encoding="utf-8") as out:
                out.write(json.dumps({"time":time.time(),**entry})+"\n")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def do_GET(self): self.forward()
    def do_POST(self): self.forward()

    def drop(self):
        self.close_connection = True
        try: self.connection.shutdown(socket.SHUT_RDWR)
        except OSError: pass

    def forward(self):
        lab = self.server
        spin = self.command == "POST" and self.path == "/api/spin"
        fault = lab.fault() if spin else "off"
        body = self.rfile.read(int(self.headers.get("Content-Length",0)))
        request = json.loads(body) if spin else None
        if fault == "offline_before":
            lab.log({"fault":fault,"request":request,"forwarded":False})
            return self.drop()
        headers = {k:v for k,v in self.headers.items() if k.lower() not in ("host","connection","content-length","origin")}
        headers["Host"] = f"127.0.0.1:{lab.backend.server_port}"
        if self.headers.get("Origin"):
            headers["Origin"] = "http://"+headers["Host"]
        upstream = http.client.HTTPConnection("127.0.0.1",lab.backend.server_port,timeout=5)
        try:
            upstream.request(self.command,self.path,body or None,headers)
            response = upstream.getresponse()
            payload = response.read()
            status = response.status
            response_headers = dict(response.getheaders())
        finally:
            upstream.close()
        if spin:
            result = json.loads(payload)
            lab.log({"fault":fault,"request":request,"forwarded":True,"status":status,
                     "round_id":result.get("round_id"),"book_id":result.get("book_id"),
                     "balance_cents":result.get("balance_cents"),"stats":result.get("stats")})
        if fault == "drop_after": return self.drop()
        if fault == "delay_after": time.sleep(18)
        if fault == "wrong_json_after": payload = b'{}'
        try:
            self.send_response(status)
            for key in ("Content-Type","Set-Cookie","Cache-Control"):
                if key in response_headers: self.send_header(key,response_headers[key])
            self.send_header("Content-Length",str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except (BrokenPipeError,ConnectionResetError,OSError): pass


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--port",type=int,default=8774)
    p.add_argument("--arm",choices=["off","offline_before","drop_after","delay_after","wrong_json_after"])
    p.add_argument("--count",type=int,default=1)
    args = p.parse_args()
    if args.arm:
        CONTROL.write_text(json.dumps({"fault":args.arm,"remaining":args.count}))
        print("Armed isolated browser lab",args.arm,args.count)
    else:
        CONTROL.write_text(json.dumps({"fault":"off","remaining":0}))
        EVENTS.write_text("")
        lab = Lab(args.port)
        print(f"Isolated network QA: http://127.0.0.1:{lab.server_port}/",flush=True)
        try: lab.serve_forever()
        except KeyboardInterrupt: pass
        finally:
            lab.shutdown();lab.server_close();lab.backend.shutdown();lab.backend.server_close()
