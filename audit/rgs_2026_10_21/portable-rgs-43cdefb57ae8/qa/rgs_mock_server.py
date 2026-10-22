"""Loopback-only, virtual-money RGS contract simulator. Never part of a release ZIP."""
from __future__ import annotations
import argparse
from copy import deepcopy
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import socket
import sys
import threading
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server as demo

FIXTURES = json.loads((ROOT / 'qa/regression_fixtures.json').read_text('utf-8'))
SESSION = 'local-test-session'


class MockServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address=('127.0.0.1', 8800), scenario='middle'):
        if address[0] != '127.0.0.1':
            raise ValueError('The RGS simulator must stay on loopback.')
        self.web_root = ROOT / 'web'
        self.lock = threading.RLock()
        self.balance = 100_000_000
        self.round = None
        self.authenticated = False
        self.charges = self.settlements = self.serial = 0
        self.calls = []
        self.faults = {}
        self.scenario = scenario
        self.config = {'minBet': 10000, 'maxBet': 2000000, 'stepBet': 10000,
                       'defaultBetLevel': 500000, 'betLevels': [10000, 100000, 500000, 1000000, 2000000],
                       'jurisdiction': {'socialCasino': False}}
        super().__init__(address, MockHandler)

    def wallet(self):
        return {'balance': {'amount': self.balance, 'currency': 'USD'}}


class MockHandler(demo.InterfaceHandler):
    def log_message(self, *_):
        pass  # In particular, never log launch query strings or request bodies.

    def _get(self, path):
        if path == '/__rgs-test/state':
            with self.server.lock:
                self._json({**self.server.wallet(), 'charges': self.server.charges,
                            'settlements': self.server.settlements,
                            'active': bool(self.server.round and self.server.round['active']),
                            'calls': self.server.calls})
        elif path.startswith('/api/'):
            self._json({'error': 'ERR_VAL'}, 404)
        else:
            super()._get(path)

    def _post(self, path):
        body = self._body()
        if body.get('sessionID') != SESSION:
            self._json({'error': 'ERR_IS'}, 401)
            return
        with self.server.lock:
            engine = self.server
            engine.calls.append(path)
            if path != '/wallet/authenticate' and not engine.authenticated:
                self._json({'error': 'ERR_IS'}, 401)
                return
            if path == '/wallet/authenticate':
                engine.authenticated = True
                result = {**engine.wallet(), 'config': engine.config, 'round': engine.round}
            elif path == '/wallet/balance':
                result = engine.wallet()
            elif path == '/wallet/play':
                amount = body.get('amount')
                if (engine.round and engine.round['active']) or type(amount) is not int or amount not in engine.config['betLevels'] or body.get('mode') != 'base':
                    self._json({'error': 'ERR_VAL'}, 400)
                    return
                if amount > engine.balance:
                    self._json({'error': 'ERR_IPB'}, 400)
                    return
                complete = deepcopy(FIXTURES['rounds'][engine.scenario])
                payout = amount * complete['payout_units'] // 100
                engine.balance -= amount
                engine.charges += 1
                engine.serial += 1
                engine.round = {'betID': engine.serial, 'mode': 'base', 'amount': amount,
                                'payout': payout, 'active': payout > 0,
                                'state': [{'index': 0, 'type': 'roundResult', 'data': complete}]}
                result = {**engine.wallet(), 'round': engine.round}
            elif path == '/wallet/end-round':
                if not engine.round or not engine.round['active']:
                    self._json({'error': 'ERR_VAL'}, 400)
                    return
                engine.balance += engine.round['payout']
                engine.round['active'] = False
                engine.settlements += 1
                result = engine.wallet()
            else:
                self._json({'error': 'ERR_VAL'}, 404)
                return
            if engine.faults.pop(path, None) == 'lost-response':
                self.close_connection = True
                self.connection.shutdown(socket.SHUT_RDWR)
                return
            self._json(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8800)
    parser.add_argument('--scenario', choices=list(FIXTURES['rounds']), default='middle')
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    app = MockServer(('127.0.0.1', args.port), args.scenario)
    url = f'http://127.0.0.1:{app.server_port}/?sessionID={SESSION}&rgs_url=127.0.0.1%3A{app.server_port}&demo=true&lang=pl'
    print('LOCAL RGS SIMULATOR - VIRTUAL BALANCE ONLY', flush=True)
    print(url, flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        app.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        app.server_close()


if __name__ == '__main__':
    main()
