from __future__ import annotations
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import random


def main():
    parser = argparse.ArgumentParser(description="POLSKA GUROM v0.2 mathematical prototype")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("theory", help="Exact rational first moments")
    sim = sub.add_parser("simulate", help="Simulate the actual game engine")
    sim.add_argument("--spins", type=int, default=100000)
    sim.add_argument("--seed", type=int, default=20261018)
    sim.add_argument("--out", type=Path)
    sample = sub.add_parser("sample", help="One auditable result, including all line paths")
    sample.add_argument("--seed", type=int, default=20261018)
    args = parser.parse_args()
    if args.command == "simulate":
        from .sim import simulate
        result = simulate(args.spins, args.seed)
    elif args.command == "sample":
        from .game import play_round
        result = asdict(play_round(random.Random(args.seed)))
    else:
        from .theory import theoretical_metrics
        result = theoretical_metrics()
    encoded = json.dumps(result, indent=2, ensure_ascii=False)
    if getattr(args, "out", None):
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
