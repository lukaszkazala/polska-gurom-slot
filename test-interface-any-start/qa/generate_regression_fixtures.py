"""Export real, reachable fixtures for transport and presentation regressions."""
from pathlib import Path
from dataclasses import asdict
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("fixture_server", ROOT / "server.py")
server = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = server
spec.loader.exec_module(server)
handler = object.__new__(server.InterfaceHandler)
config = []
handler._json = lambda data: config.append(data)
handler._get("/api/config")
manifest, _, payouts = server.selection.load_distribution()
# Book IDs are export-local. Resolve the actual feature witnesses from the
# current manifest rather than silently carrying IDs from an older compiler.
bonus_ids = {int(fs): group["book_ids"] for fs, group in manifest["bonus_coverage"].items()}
all_bonus_ids = {book_id for group in bonus_ids.values() for book_id in group}
ids = {
    "loss": next(i for i, payout in enumerate(payouts) if payout == 0),
    "bonus8": next(i for i in bonus_ids[8] if payouts[i] < server.config.MAX_WIN_UNITS),
    "cap": next(i for i, payout in enumerate(payouts)
                if payout == server.config.MAX_WIN_UNITS and i not in all_bonus_ids
                and server.selection.replay_spec(manifest["books"][i]).cap_reduction_units > 0),
    "middle": manifest["regression_book_ids"]["middle_run"],
    "bonus12": next(i for i in bonus_ids[12] if payouts[i] < server.config.MAX_WIN_UNITS),
}
for fs, group in bonus_ids.items():
    candidates = [i for i in group if payouts[i] == server.config.MAX_WIN_UNITS]
    if candidates:
        ids[f"bonus_cap{fs}"] = next(
            (i for i in candidates if len(server.selection.replay_spec(manifest["books"][i]).free_spins) < fs),
            candidates[0])
payload = {"config": config[0], "book_ids": ids,
           "rounds": {name: asdict(server.selection.replay_spec(manifest["books"][book_id]))
                      for name, book_id in ids.items()}}
assert payload["rounds"]["bonus8"]["base"]["free_spins_awarded"] == 8
assert payload["rounds"]["bonus12"]["base"]["free_spins_awarded"] == 12
assert payload["rounds"]["cap"]["payout_units"] == server.config.MAX_WIN_UNITS
assert not payload["rounds"]["cap"]["base"]["bonus_triggered"]
assert any(win["symbol"] == "L1" and win.get("start_reel", 0) == 1 and win["count"] == 3
           for win in payload["rounds"]["middle"]["base"]["line_wins"])
(ROOT / "qa/regression_fixtures.json").write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
print({"math_version": config[0]["math_version"], "fixtures": len(ids)})
