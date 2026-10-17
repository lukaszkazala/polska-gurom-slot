"""Run independent seeded 10k/100k/1M complete-paid-round simulations."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from polska_gurom.config import load_config
from polska_gurom.simulation import crosscheck, crosscheck_batch_reproducibility, simulate

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config")
    parser.add_argument("--rounds",type=int,nargs="+",default=[10000,100000,1000000])
    parser.add_argument("--seed",type=int,default=20261017)
    parser.add_argument("--batch-size",type=int,default=100000)
    parser.add_argument("--output-dir",default=str(ROOT/"reports"/"results"))
    args = parser.parse_args()
    cfg = load_config(args.config)
    output = Path(args.output_dir)
    output.mkdir(parents=True,exist_ok=True)
    check = crosscheck(cfg)
    (output/"vector_scalar_crosscheck.json").write_text(json.dumps(check,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(check),flush=True)
    repeat = crosscheck_batch_reproducibility(cfg)
    (output/"simulation_reproducibility.json").write_text(json.dumps(repeat,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(repeat),flush=True)
    for n in args.rounds:
        seed = args.seed+n
        result = simulate(n,seed,cfg,args.batch_size)
        path = output/f"simulation_{n}.json"
        path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print(json.dumps({"file":str(path),"rounds":n,"seed":seed,
                          "rtp":result["rtp_post_cap"],"95pct_ci":result["rtp_95pct_ci"],
                          "hit_base":result["frequency"]["hit_base"],
                          "bonus_count":result["bonus_count"],
                          "maximum_observed":result["maximum_observed_paid_round_payout"]}),flush=True)

if __name__ == "__main__":
    main()
