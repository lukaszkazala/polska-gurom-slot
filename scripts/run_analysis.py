"""Write exact natural-generator expectation analysis as reviewable JSON."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from polska_gurom.config import load_config
from polska_gurom.analytics import analyze

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config")
    parser.add_argument("--output",default=str(ROOT/"reports"/"results"/"analysis.json"))
    args = parser.parse_args()
    result = analyze(load_config(args.config))
    path = Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"file":str(path),"total_rtp_pre_cap":result["total_rtp_pre_cap"]["value"],
                      "bonus_probability":result["bonus_probability"]["value"],
                      "cap_loss_upper_bound":result["cap"]["rtp_loss_upper_bound"]["value"]},indent=2))

if __name__ == "__main__":
    main()
