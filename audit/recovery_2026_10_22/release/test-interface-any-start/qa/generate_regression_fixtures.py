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
ids = {"loss": 1, "bonus8": 484, "cap": 100020, "middle": 100048, "bonus12": 100024}
assert payouts[ids["loss"]] == 0
payload = {"config": config[0], "book_ids": ids,
           "rounds": {name: asdict(server.selection.replay_spec(manifest["books"][book_id]))
                      for name, book_id in ids.items()}}
(ROOT / "qa/regression_fixtures.json").write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
print({"math_version": config[0]["math_version"], "fixtures": len(ids)})
