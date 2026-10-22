"""Checks the test wrapper only; does not claim a physical Safari test."""
import hashlib
import http.client
import json
from pathlib import Path
import sys
import threading
import unittest

sys.dont_write_bytecode = True
import phone_server as phone


class PhoneServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = phone.PhoneServer(("127.0.0.1", 0), key="phone-wrapper-test-key")
        cls.thread = threading.Thread(target=cls.app.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.app.shutdown()
        cls.app.server_close()
        cls.thread.join(5)

    def request(self, method, path, body=None, headers=None, auth=True):
        h = {"Cookie": f"{phone.ACCESS_COOKIE}={self.app.access_key}"} if auth else {}
        h.update(headers or {})
        client = http.client.HTTPConnection(*self.app.server_address, timeout=20)
        client.request(method, path, body=body, headers=h)
        response = client.getresponse()
        result = (response.status, dict(response.getheaders()), response.read())
        client.close()
        return result

    def test_no_access_without_link(self):
        self.assertEqual(self.request("GET", "/api/config", auth=False)[0], 403)
        self.assertEqual(self.request("GET", "/__phone/start?key=wrong", auth=False)[0], 403)

    def test_bootstrap_link_and_redirect(self):
        status, headers, _ = self.request("GET", "/__phone/start?key=" + self.app.access_key,
                                        headers={"Sec-Fetch-Site": "cross-site"}, auth=False)
        self.assertEqual(status, 303)
        self.assertEqual(headers["Location"], "/?studio=1&lang=pl")
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")

    def test_reject_other_hosts_and_origins(self):
        for headers in ({"Host": "example.com"}, {"Origin": "https://other.example"},
                        {"Sec-Fetch-Site": "cross-site"}):
            with self.subTest(headers=headers):
                self.assertEqual(self.request("GET", "/api/config", headers=headers)[0], 403)
        self.assertEqual(self.request("GET", "/api/config", headers={"Origin": self.app.origin})[0], 200)

    def test_reject_public_or_unspecified_bind(self):
        for host in ("0.0.0.0", "8.8.8.8", "::"):
            with self.subTest(host=host):
                with self.assertRaises(ValueError):
                    phone.PhoneServer((host, 0))

    def test_only_frozen_web_and_build_metadata_served(self):
        status, _, body = self.request("GET", "/__phone/build")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["build_id"], phone.BUILD["build_id"])
        for path in ("/../phone_build.json", "/%2e%2e/server.py", "/server.py"):
            self.assertEqual(self.request("GET", path)[0], 404)
        status, headers, body = self.request("GET", "/?studio=1&lang=pl")
        self.assertEqual(status, 200)
        self.assertIn(b'audio.js', body)
        self.assertEqual(headers["X-Frame-Options"], "DENY")

    def test_audio_assets_and_build_hashes(self):
        web = Path(phone.BUILD["build_directory"]) / "web"
        for p in sorted((web / "assets/audio").glob("*.wav")):
            with self.subTest(audio=p.name):
                status, _, data = self.request("GET", "/assets/audio/" + p.name)
                self.assertEqual(status, 200)
                self.assertEqual(hashlib.sha256(data).hexdigest(),
                                 phone.BUILD["files"]["web/assets/audio/" + p.name]["sha256"])
        self.assertEqual(self.request("GET", "/audio.js")[0], 200)

    def test_demo_round_remains_idempotent(self):
        _, headers, state_data = self.request("GET", "/api/state")
        state = json.loads(state_data)
        session_cookie = headers["Set-Cookie"].split(";", 1)[0]
        headers = {"Cookie": f"{phone.ACCESS_COOKIE}={self.app.access_key}; {session_cookie}",
                   "Content-Type": "application/json", "Origin": self.app.origin,
                   "X-Game-Session": state["session_id"]}
        payload = json.dumps({"bet_cents": 200, "mode": "random", "request_id": "phone-wrapper-check"})
        status, _, first = self.request("POST", "/api/spin", payload, headers=headers)
        self.assertEqual(status, 200)
        status, _, retry = self.request("POST", "/api/spin", payload, headers=headers)
        self.assertEqual(status, 200)
        self.assertEqual(first, retry)
        result = json.loads(first)
        self.assertEqual(result["stats"]["rounds"], 1)
        self.assertEqual(result["balance_cents"], state["balance_cents"] - 200 + result["win_cents"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
