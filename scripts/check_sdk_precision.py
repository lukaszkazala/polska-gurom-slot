"""Find an actual reachable round violating the current SDK payout step.

This does not export a weighted book, round credits or change the math.
"""
from pathlib import Path
import json
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from polska_gurom.config import load_config
from polska_gurom.engine import play_round, round_to_dict
from polska_gurom.sdk_adapter import current_sdk_payout_compatible

def main():
    cfg = load_config()
    seed = 20261017
    rng = random.Random(seed)
    for index in range(10000):
        result = play_round(cfg,rng)
        if not current_sdk_payout_compatible(result.paid_total_units,cfg.scale):
            data = dict(status="BLOCKED_BY_CURRENT_SDK_PAYOUT_STEP",seed=seed,
                        round_index_zero_based=index,config_hash=cfg.config_hash,
                        sdk_rule="Exact integer payoutMultiplier in x100 TOTAL BET, divisible by 10",
                        observed_payout_units=result.paid_total_units,
                        unit_scale=cfg.scale,round=round_to_dict(result))
            path = ROOT/"reports/sdk_payout_step_witness.json"
            path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
            print(json.dumps({k:v for k,v in data.items() if k != "round"}))
            return
    raise RuntimeError("No incompatible payout found in 10000 natural rounds; compatibility not proved")

if __name__ == "__main__":
    main()
