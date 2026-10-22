"""Reproduce arithmetic from visually inspected video tables and current config.

Frequency table inspected at 00:39, payout/count table at 01:37,
final fractions inspected at 02:07. Marginals do not specify joint labels
within dual-symbol stops; this script does not certify a unique stop mapping.
"""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT / "polska_gurom_v0_2"))
from polska_gurom import config
from polska_gurom.theory import exact_first_moments
from tools.math_config import compute_config_fingerprint

FREQUENCIES = {
    "seven": [1, 1, 1], "bar": [3, 2, 1], "melon": [2, 2, 2],
    "bell": [1, 5, 8], "plum": [7, 3, 3], "orange": [5, 5, 4],
    "cherry": [2, 6, 0], "lemon": [0, 0, 4],
}
ROWS = [
    ("seven seven seven", 200, 1, 1 * 1 * 1),
    ("bar bar bar", 100, 6, 3 * 2 * 1),
    ("melon melon melon", 100, 8, 2 * 2 * 2),
    ("melon melon bar", 100, 4, 2 * 2 * 1),
    ("bell bell bell", 18, 40, 1 * 5 * 8),
    ("bell bell bar", 18, 5, 1 * 5 * 1),
    ("plum plum plum", 14, 63, 7 * 3 * 3),
    ("plum plum bar", 14, 21, 7 * 3 * 1),
    ("orange orange orange", 10, 100, 5 * 5 * 4),
    ("orange orange bar", 10, 25, 5 * 5 * 1),
    ("cherry cherry any", 5, 240, 2 * 6 * 20),
    ("cherry non-cherry any", 2, 560, 2 * (20 - 6) * 20),
]


def main():
    for pattern, payout, displayed, recomputed in ROWS:
        if displayed != recomputed:
            raise ValueError(f"Row arithmetic mismatch: {pattern}")
    total_counts = sum(r[2] for r in ROWS)
    total_payout = sum(r[1] * r[2] for r in ROWS)
    if (total_counts, total_payout) != (1073, 7556):
        raise ValueError("Table total mismatch")
    rtp = F(total_payout, 20 ** 3)
    cost = F(94, 100)
    validation_path = ROOT / "polska_gurom_v0_2/verification/math_validation.json"
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    current = exact_first_moments()
    fingerprint = compute_config_fingerprint(config)
    if fingerprint != validation["math_config_sha256"]:
        raise ValueError("Project config differs from verified distribution")
    if str(current["total_rtp_uncapped"]) != validation["rtp_uncapped_fraction"]:
        raise ValueError("Current theory differs from independent verification")
    source_paths = ["polska_gurom_v0_2/polska_gurom/config.py",
                    "polska_gurom_v0_2/polska_gurom/game.py",
                    "polska_gurom_v0_2/polska_gurom/theory.py",
                    "polska_gurom_v0_2/docs/PAR_SHEET.md",
                    "polska_gurom_v0_2/docs/MATH_SPECIFICATION.md",
                    "polska_gurom_v0_2/docs/GAME_DESIGN_DOCUMENT.md",
                    "polska_gurom_v0_2/README.md"]
    result = {
        "date": "2026-10-18", "video_id": "BFlRH99TQOw",
        "visual_observation_times_seconds": [19, 39, 97, 127],
        "transcript_sha256": hashlib.sha256((OUT / "transcript.json").read_bytes()).hexdigest(),
        "frequency_table": FREQUENCIES,
        "symbol_label_totals": [sum(v[i] for v in FREQUENCIES.values()) for i in range(3)],
        "stops_per_reel_as_stated_in_video": 20,
        "table_rows": [{"pattern": p, "payout": a, "count": n, "row_return": a * n}
                       for p, a, n, _ in ROWS],
        "stop_combinations_three_reels": 20 ** 3,
        "sum_of_displayed_row_counts": total_counts,
        "sum_of_displayed_row_returns": total_payout,
        "row_count_ratio_percent": float(F(total_counts, 20 ** 3) * 100),
        "distinct_hit_count_independently_certified": False,
        "reason": "Dual-symbol stop mapping and payout priority are not fully specified by the marginal table.",
        "rtp_from_row_return_sum_fraction": str(rtp),
        "rtp_from_row_return_sum_percent": float(rtp * 100),
        "house_edge_if_this_aggregate_is_actual_settlement": float(1 - rtp),
        "fixed_absolute_prizes_new_cost_0_94": {
            "expected_payout": float(rtp), "expected_net": float(rtp - cost),
            "rtp_percent": float(rtp / cost * 100)},
        "proportionally_scaled_prizes_new_cost_0_94": {
            "expected_payout": float(rtp * cost), "expected_net": float((rtp - 1) * cost),
            "rtp_percent": float(rtp * 100)},
        "stop_combinations_five_reels": 20 ** 5,
        "project_stop_combinations": 36 ** 5,
        "project_math_config_sha256": fingerprint,
        "current_first_moments_match_previously_verified_distribution": True,
        "project_rtp_uncapped": float(current["total_rtp_uncapped"]),
        "project_positive_payout_probability": validation["positive_return_probability"],
        "project_net_profit_probability": validation["net_profit_probability"],
        "project_source_hashes": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in source_paths},
    }
    (OUT / "analysis_checks.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ["sum_of_displayed_row_counts", "sum_of_displayed_row_returns",
          "row_count_ratio_percent", "rtp_from_row_return_sum_percent", "project_rtp_uncapped"]}, indent=2))


if __name__ == "__main__":
    main()
