"""Reproduce the arithmetic used in the accompanying Polish analysis.

Run from the project mirror root. Does not modify the game or sources/.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "polska_gurom_v0_2"))
from polska_gurom.theory import exact_first_moments
from tools.math_config import compute_config_fingerprint
from polska_gurom import config


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    checked = json.loads((OUT / "project_math_rechecked.json").read_text(encoding="utf-8"))
    current = exact_first_moments()
    assert checked["math_config_sha256"] == compute_config_fingerprint(config)
    assert checked["rtp_uncapped_fraction"] == str(current["total_rtp_uncapped"])
    assert abs(checked["trigger_probability"] - float(current["bonus_frequency"])) < 1e-15
    assert abs(checked["base_rtp"] - float(current["base_rtp"])) < 1e-15

    captions = json.loads((OUT / "transcript_en.json").read_text(encoding="utf-8"))
    jackpot = Fraction(8, 72 ** 3)
    q = current["bonus_frequency"]
    grid_count = math.prod(len(s) for s in config.REEL_STRIPS)
    examples = []
    for name, hit, award in [("A", Fraction(1, 2), Fraction(48, 25)),
                             ("B", Fraction(1, 100), Fraction(96))]:
        mean = hit * award
        variance = hit * award ** 2 - mean ** 2
        examples.append({"name": name, "hit_probability": float(hit), "award_x": float(award),
                         "rtp": float(mean), "standard_deviation_x": math.sqrt(float(variance))})

    paths = ["polska_gurom_v0_2/polska_gurom/config.py",
             "polska_gurom_v0_2/polska_gurom/game.py",
             "polska_gurom_v0_2/polska_gurom/theory.py",
             "polska_gurom_v0_2/tools/verify_math.py",
             "polska_gurom_v0_2/tools/math_config.py",
             "polska_gurom_v0_2/verification/joint_counts.npz",
             "polska_gurom_v0_2/README.md",
             "polska_gurom_v0_2/docs/PAR_SHEET.md",
             "polska_gurom_v0_2/docs/MATH_SPECIFICATION.md",
             "polska_gurom_v0_2/docs/GAME_DESIGN_DOCUMENT.md"]
    result = {
        "analysis_date": "2026-10-18", "video_id": "bjXhjbf1M4o",
        "caption_language": "en", "caption_kind": "auto-generated",
        "caption_segments": len(captions),
        "last_caption_end_seconds": max(x["start"] + x["duration"] for x in captions),
        "transcript_sha256": file_hash(OUT / "transcript_en.json"),
        "source_paper_sha256": file_hash(OUT / "reference_harrigan_dixon.pdf"),
        "project_math_config_sha256": checked["math_config_sha256"],
        "project_source_hashes": {name: file_hash(ROOT / name) for name in paths},
        "independent_verifier_matches_current_theory": True,
        "paper_example": {"combinations": 72 ** 3, "jackpot_outcomes": 8,
                          "jackpot_probability_fraction": str(jackpot),
                          "jackpot_probability_percent": float(jackpot * 100),
                          "mean_spins_per_jackpot": float(1 / jackpot),
                          "zero_payout_probability": 319928 / (72 ** 3),
                          "single_cherry_probability": 18960 / (72 ** 3)},
        "project_no_bonus_probability": {str(n): float((1 - q) ** n) for n in [100, 200, 500, 1000]},
        "project_combinations": grid_count,
        "probability_one_specified_grid_seen_after_10m_spins": -math.expm1(10000000 * math.log1p(-1 / grid_count)),
        "same_rtp_different_volatility_examples": examples,
        "positive_payout_fraction_that_is_below_bet": checked["positive_below_bet_probability"] / checked["positive_return_probability"],
    }
    (OUT / "analysis_checks.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
