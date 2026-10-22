"""Actual HTTP recovery/refresh scenarios on the loopback RGS simulator; no live Stake access."""
from pathlib import Path
import json
import os
import subprocess
import threading
import unittest
from rgs_mock_server import MockServer

ROOT = Path(__file__).resolve().parent
REPORTS = []


class RecoveryHttpTests(unittest.TestCase):
    def probe(self, fault):
        app = MockServer(('127.0.0.1', 0), 'bonus12')
        endpoint = {'auth-before': '/wallet/authenticate', 'event-before': '/bet/event',
                    'event-lost': '/bet/event', 'end-before': '/wallet/end-round',
                    'end-lost': '/wallet/end-round'}.get(fault)
        if endpoint:
            app.faults[endpoint] = 'network-before' if fault.endswith('before') else 'lost-response'
        worker = threading.Thread(target=app.serve_forever, daemon=True)
        worker.start()
        try:
            result = subprocess.run(['node', str(ROOT / 'test_rgs_recovery_http.cjs'), f'http://127.0.0.1:{app.server_port}', fault],
                                    capture_output=True, text=True, timeout=40)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(report['passed'])
            self.assertEqual(app.charges, 1)
            self.assertEqual(app.settlements, 1)
            REPORTS.append(report)
        finally:
            app.shutdown()
            app.server_close()
            worker.join(timeout=5)

    def test_fresh_browser_without_old_local_storage(self):
        self.probe('none')

    def test_authentication_connection_lost(self):
        self.probe('auth-before')

    def test_checkpoint_request_not_received(self):
        self.probe('event-before')

    def test_checkpoint_committed_response_lost(self):
        self.probe('event-lost')

    def test_settlement_request_not_received(self):
        self.probe('end-before')

    def test_settlement_committed_response_lost(self):
        self.probe('end-lost')


if __name__ == '__main__':
    outcome = unittest.main(verbosity=2, exit=False).result
    out = Path(os.environ.get('PG_QA_OUT_DIR', ROOT))
    out.mkdir(parents=True, exist_ok=True)
    (out / 'rgs_recovery_http_results.json').write_text(json.dumps({'passed': outcome.wasSuccessful(), 'tests': outcome.testsRun, 'scenarios': REPORTS}, indent=2), encoding='utf8')
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
