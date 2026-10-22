"""Real HTTP transport tests against the loopback-only RGS simulator."""
from pathlib import Path
import json
import subprocess
import threading
import unittest
from rgs_mock_server import MockServer

ROOT = Path(__file__).resolve().parent


class RgsHttpTests(unittest.TestCase):
    def probe(self, scenario='middle', fault='none'):
        app = MockServer(('127.0.0.1', 0), scenario)
        if fault != 'none':
            app.faults['/wallet/' + ('play' if fault == 'play' else 'end-round')] = 'lost-response'
        worker = threading.Thread(target=app.serve_forever, daemon=True)
        worker.start()
        try:
            result = subprocess.run(['node', str(ROOT / 'test_rgs_http.cjs'), f'http://127.0.0.1:{app.server_port}', fault],
                                    capture_output=True, text=True, timeout=40)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(report['passed'])
            self.assertEqual(app.charges, 1)
        finally:
            app.shutdown()
            app.server_close()
            worker.join(timeout=5)

    def test_positive_round(self):
        self.probe()

    def test_zero_round(self):
        self.probe('loss')

    def test_full_bonus(self):
        self.probe('bonus12')

    def test_lost_play_response(self):
        self.probe(fault='play')

    def test_lost_settlement_response(self):
        self.probe(fault='end')


if __name__ == '__main__':
    unittest.main(verbosity=2)
