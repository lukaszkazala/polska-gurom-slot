"""Explicit LAN-only wrapper for a frozen, virtual-money phone test build."""
from __future__ import annotations

import argparse
from http.cookies import SimpleCookie
from http.server import ThreadingHTTPServer
import ipaddress
import json
import os
from pathlib import Path
import secrets
import sys
import threading
from urllib.parse import parse_qs, urlencode, urlsplit

sys.dont_write_bytecode = True
TASK = Path(__file__).resolve().parent
BUILD = json.loads((TASK / "phone_build.json").read_text("utf-8"))
sys.path.insert(0, BUILD["build_directory"])
import server as demo

ACCESS_COOKIE = "pg_phone_access"
PRIVATE_NETWORKS = tuple(ipaddress.ip_network(n) for n in
                         ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))


class PhoneServer(demo.InterfaceServer):
    def __init__(self, address, key=None):
        ip = ipaddress.ip_address(address[0])
        if ip.version != 4 or not (ip.is_loopback or any(ip in n for n in PRIVATE_NETWORKS)):
            raise ValueError("Use one explicit private IPv4 address or loopback.")
        self.web_root = (Path(BUILD["build_directory"]) / "web").resolve()
        self.sessions = {}
        self.sessions_lock = threading.Lock()
        self.access_key = key or secrets.token_urlsafe(24)
        demo.selection.load_distribution()
        ThreadingHTTPServer.__init__(self, address, PhoneHandler)

    @property
    def origin(self):
        return f"http://{self.server_address[0]}:{self.server_port}"


class PhoneHandler(demo.InterfaceHandler):
    def log_message(self, *args):
        pass  # Do not record access links, cookies or game session identifiers.

    def _guard(self):
        expected = f"{self.server.server_address[0]}:{self.server.server_port}"
        hosts = self.headers.get_all("Host", [])
        if len(hosts) != 1 or hosts[0] != expected:
            raise demo.APIError(403, "invalid_host", "Nieprawidłowy adres testu.")
        origin = self.headers.get("Origin")
        if origin is not None and origin != self.server.origin:
            raise demo.APIError(403, "invalid_origin", "Żądanie z innej strony odrzucone.")
        parsed = urlsplit(self.path)
        if parsed.path == "/__phone/start" and self.command in {"GET", "HEAD"}:
            keys = parse_qs(parsed.query).get("key", [])
            if len(keys) == 1 and secrets.compare_digest(keys[0], self.server.access_key):
                return
        if self.headers.get("Sec-Fetch-Site", "").lower() == "cross-site":
            raise demo.APIError(403, "cross_site", "Otwórz link bezpośrednio w Safari.")
        cookies = SimpleCookie()
        try:
            cookies.load(self.headers.get("Cookie", ""))
        except Exception:
            pass
        access = cookies.get(ACCESS_COOKIE)
        if not access or not secrets.compare_digest(access.value, self.server.access_key):
            raise demo.APIError(403, "phone_access_required", "Otwórz pełny link testowy z czatu.")

    def _get(self, path):
        if path == "/__phone/start":
            self.send_response(303)
            self.send_header("Location", "/?studio=1&lang=pl")
            self.send_header("Set-Cookie", f"{ACCESS_COOKIE}={self.server.access_key}; Path=/; HttpOnly; SameSite=Lax")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif path == "/__phone/build":
            self._json({"build_id": BUILD["build_id"], "manifest_sha256": BUILD["manifest_sha256"],
                        "virtual_money_only": True, "platform": False})
        else:
            super()._get(path)

    def _post(self, path):
        if path == "/__phone/stop":
            if self.client_address[0] not in {self.server.server_address[0], "127.0.0.1"}:
                raise demo.APIError(403, "local_only", "Zatrzymaj test na komputerze.")
            self._json({"stopping": True})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        else:
            super()._post(path)


def main():
    parser = argparse.ArgumentParser(description="Test iPhone/Safari w lokalnym Wi-Fi")
    parser.add_argument("--host", help="Dokładny adres IPv4 komputera w Wi-Fi")
    parser.add_argument("--port", type=int, default=8785)
    parser.add_argument("--stop", action="store_true")
    args = parser.parse_args()
    runtime = TASK / "phone_runtime.json"
    if args.stop:
        from urllib.request import build_opener, HTTPCookieProcessor, Request
        info = json.loads(runtime.read_text("utf-8"))
        opener = build_opener(HTTPCookieProcessor())
        opener.open(info["access_url"], timeout=5).close()
        response = opener.open(Request(info["origin"] + "/__phone/stop", data=b"",
                                       headers={"Origin": info["origin"]}), timeout=5)
        print(response.read().decode())
        return
    if not args.host or not 1 <= args.port <= 65535:
        parser.error("Podaj --host i port 1–65535.")
    app = PhoneServer((args.host, args.port))
    info = {"pid": os.getpid(), "origin": app.origin, "build_id": BUILD["build_id"],
            "access_url": app.origin + "/__phone/start?" + urlencode({"key": app.access_key}),
            "device": "iPhone 15", "browser": "Safari", "state": "running"}
    runtime.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ready": True, "origin": app.origin, "build_id": BUILD["build_id"]}), flush=True)
    try:
        app.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        app.server_close()
        info["state"] = "stopped"
        runtime.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
