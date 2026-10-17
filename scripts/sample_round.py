import argparse
from pathlib import Path
import json
import random
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from polska_gurom.config import load_config
from polska_gurom.engine import play_round, round_to_dict, evaluate_spin, assemble_round
from polska_gurom import __version__

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed",type=int,default=20261017)
    parser.add_argument("--witness",action="store_true")
    parser.add_argument("--output",default="reports/sample_round.json")
    args = parser.parse_args()
    cfg = load_config()
    if args.witness:
        base = evaluate_spin(cfg,(33,33,33,33,33))
        fs = evaluate_spin(cfg,(31,31,31,31,31),True)
        result = assemble_round(cfg,base,[fs]*base.awarded_free_spins)
    else:
        result = play_round(cfg,random.Random(args.seed))
    data = dict(seed=None if args.witness else args.seed,engine_version=__version__,config_hash=cfg.config_hash,
                kind="positive-probability-witness" if args.witness else "natural-seeded-round",round=round_to_dict(result))
    path = Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in data.items() if k != "round"}))
    print("raw_units",result.raw_total_units,"paid_units",result.paid_total_units)

if __name__ == "__main__":
    main()
