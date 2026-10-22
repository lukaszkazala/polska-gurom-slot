"""Read-only audit probes against current server code; creates audit evidence only."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from types import SimpleNamespace
from unittest.mock import patch

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT / "test-interface"))
import server


def invoke(session, body):
    handler = object.__new__(server.InterfaceHandler)
    handler._body = lambda: body
    handler._session = lambda: (session, None)
    responses = []
    handler._json = lambda payload, **kwargs: responses.append(payload)
    handler._post("/api/spin")
    return responses[0]


session = server.Session(rng=random.Random(1))
body = {"bet_cents": 100, "mode": "random", "request_id": "paid-original"}
first = invoke(session, body)
immediate = invoke(session, body)
assert first == immediate and session.rounds == 1
for i in range(100):
    invoke(session, {"bet_cents": 100, "mode": "win", "request_id": f"preview-{i}"})
assert body["request_id"] not in session.results
after_eviction = invoke(session, body)
assert session.rounds == 2 and after_eviction["round_id"] != first["round_id"]

# A retry can return an older wallet snapshot after another round has settled.
session2 = server.Session(rng=random.Random(1))
old = invoke(session2, {**body, "request_id": "a"})
new = invoke(session2, {**body, "request_id": "b"})
cached = invoke(session2, {**body, "request_id": "a"})
assert cached == old and cached["stats"]["rounds"] == 1 and session2.rounds == 2

def grid(stops):
    return [[server.config.REEL_STRIPS[column][(stops[column] + row) % 36]
             for column in range(5)] for row in range(3)]
base = grid((33, 26, 20, 14, 6))
free = grid((21, 15, 0, 3, 30))
class ExpansionRng:
    def random(self): return 0.0
    def choice(self, eligible): return 2
with patch.object(server.game, "generate_grid", side_effect=[base] + [free] * 12):
    capped = server.game.play_round(ExpansionRng(), expansion_probability=1)
with patch.object(server.game, "play_round", return_value=capped):
    capped_response = invoke(server.Session(), {**body, "request_id": "cap"})

config = {
    "symbols": server.config.SYMBOLS, "paylines": server.config.PAYLINES,
    "paytable_units": server.config.PAYTABLE_UNITS,
    "scatter_paytable_units": server.config.SCATTER_PAYTABLE_UNITS,
    "free_spins": server.config.FREE_SPINS, "payout_scale": server.config.PAYOUT_SCALE,
    "max_win_units": server.config.MAX_WIN_UNITS,
    "fs_line_multiplier": server.config.FS_LINE_MULTIPLIER,
    "bet_options_cents": server.BET_OPTIONS_CENTS,
    "initial_balance_cents": server.INITIAL_BALANCE_CENTS,
}
fixtures = {"config": config, "cap": capped_response, "history": old,
            "symbols": json.loads((ROOT / "test-interface/web/assets/symbols.json").read_text(encoding="utf-8"))}
(OUT / "fixtures.json").write_text(json.dumps(fixtures, ensure_ascii=False, indent=2), encoding="utf-8")
report = {
    "source_sha256": hashlib.sha256((ROOT / "test-interface/server.py").read_bytes()).hexdigest(),
    "method": "Current InterfaceHandler._post invoked in-process with captured JSON; engine unchanged; no HTTP mocks of settlement.",
    "immediate_retry": {"same_response": immediate == first, "rounds_after": 1},
    "eviction_after_100_previews": {
        "first_round_id": first["round_id"], "retry_round_id": after_eviction["round_id"],
        "new_round_on_retry": after_eviction["round_id"] != first["round_id"], "paid_rounds_after": session.rounds,
    },
    "cached_wallet_snapshot": {
        "cached_rounds": cached["stats"]["rounds"], "actual_rounds": session2.rounds,
        "cached_balance_cents": cached["balance_cents"], "actual_balance_cents": session2.balance_cents,
    },
    "cap_fixture": {"payout_units": capped.payout_units, "last_credits": capped.free_spin_credits[-5:],
                    "last_spin_line_count": len(capped.free_spins[-1].line_wins)},
}
(OUT / "server_probe_results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
