"""Read-only payline analysis of the existing mathematical prototype."""
from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter
from fractions import Fraction
from itertools import product
from pathlib import Path

sys.dont_write_bytecode = True
PROJECT = Path(r"D:\Kazaluka_slots\polska_gurom_phase2_v0.1")
OUTPUT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))

from polska_gurom import config as c
from polska_gurom.theory import theoretical_metrics


def snapshot():
    return {str(p.relative_to(PROJECT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(PROJECT.rglob("*")) if p.is_file()}


def exact_hit(lines):
    # Any positive line award is determined by the first three reels.
    # Every paying Scatter trigger already has a positive paid-spin award.
    # The five strips are rotations of the same sequence under uniform stops.
    strip = c.REEL_STRIPS[0]
    windows = [tuple(strip[(st + row) % len(strip)] for row in range(3))
               for st in range(len(strip))]
    prefixes = set(line[:3] for line in lines)
    line_hit = 0
    misses_by_scatter = Counter()
    for stops in product(range(36), repeat=3):
        won = False
        for rows in prefixes:
            real = {windows[stops[r]][rows[r]] for r in range(3)} - {c.WILD}
            if not real or (len(real) == 1 and next(iter(real)) in c.REGULAR_SYMBOLS):
                won = True
                break
        if won:
            line_hit += 1
        else:
            misses_by_scatter[sum(c.SCATTER in windows[s] for s in stops)] += 1
    prob_line = Fraction(line_hit, 36**3)
    scatter_extra = sum(
        Fraction(n, 36**3)
        * sum((Fraction(math.comb(2, k) * 11**(2-k), 12**2)
               for k in range(max(0, 3-sc), 3)), Fraction())
        for sc, n in misses_by_scatter.items()
    )
    return {"line_hit_probability": float(prob_line),
            "paid_round_positive_payout_probability": float(prob_line + scatter_extra),
            "exact_fraction": str(prob_line + scatter_extra),
            "unique_three_reel_prefixes": len(prefixes)}


before = snapshot()
theory = theoretical_metrics()
q = theory["bonus_frequency"]
base = theory["base_rtp"]
expected_fs = q * theory["average_free_spins_per_trigger"]
bonus_needed = 0.96 - base
simulation = json.loads((PROJECT / "simulation_1m.json").read_text())
counts = Counter(c.REEL_STRIPS[0])
p_one_line_hit = (sum(Fraction(counts[s] + counts[c.WILD], 36)**3
                     for s in c.REGULAR_SYMBOLS)
                  - (len(c.REGULAR_SYMBOLS)-1) * Fraction(counts[c.WILD], 36)**3)
results = {
    "project": str(PROJECT),
    "theory": theory,
    "paylines": [{"id": i+1, "rows_zero_based": list(line)}
                 for i, line in enumerate(c.PAYLINES)],
    "line_count": len(c.PAYLINES),
    "unique_lines": len(set(c.PAYLINES)),
    "horizontal_lines": sum(len(set(line)) == 1 for line in c.PAYLINES),
    "non_horizontal_lines": sum(len(set(line)) > 1 for line in c.PAYLINES),
    "current_exact_hit": exact_hit(c.PAYLINES),
    "three_horizontal_exact_hit": exact_hit(tuple((r,)*5 for r in range(3))),
    "single_line_positive_probability": float(p_one_line_hit),
    "expected_count_of_winning_lines_per_paid_spin": float(len(c.PAYLINES)*p_one_line_hit),
    "target_96_with_current_base": {
        "required_bonus_rtp": bonus_needed,
        "required_mean_bonus_given_trigger": bonus_needed/q,
        "required_free_spin_ev_before_cap": bonus_needed/expected_fs,
        "bonus_scaling_before_cap": bonus_needed/theory["bonus_rtp"],
        "rtp_at_100_percent_expansion": theoretical_metrics(1.0)["total_rtp"],
    },
    "unit_warning": "PAYTABLE values already multiply TOTAL BET, not bet per line.",
    "geometry_invariance": "At fixed line count, identical marginal symbol probabilities per row and the same paytable imply equal uncapped mean line payout. Joint hit probability and variance depend on the geometry and strip order. Caps can break total RTP invariance.",
    "simulation_1m": {
        "positive_payout_rate": simulation["hit_frequency"],
        "positive_below_total_bet_rate": simulation["win_buckets"][">0x-1x"]/simulation["spins"],
        "rtp_estimate": simulation["rtp"],
        "rtp_95_percent_normal_half_width": 1.96 * simulation["std_dev"] / math.sqrt(simulation["spins"]),
        "note": "Normal interval is an empirical Monte Carlo diagnostic, not a guarantee about rare tails or production accuracy.",
    },
}
variants_path = OUTPUT.parent / "paylines_variants" / "comparison_results.json"
if variants_path.exists():
    candidate = json.loads(variants_path.read_text())["nine_prefixes_with_v_twenty"]
    lines = tuple(tuple(x) for x in candidate["lines"])
    assert len(lines) == len(set(lines)) == 20
    assert all(len(line) == 5 and all(r in range(3) for r in line) for line in lines)
    assert all(abs(a-b) <= 1 for line in lines for a, b in zip(line, line[1:]))
    assert all((r,)*5 in lines for r in range(3))
    assert (0,1,2,1,0) in lines and (2,1,0,1,2) in lines
    hit_check = exact_hit(lines)
    assert math.isclose(hit_check["paid_round_positive_payout_probability"], candidate["hit_probability"], abs_tol=1e-15)
    assert 0.25 <= hit_check["paid_round_positive_payout_probability"] <= 0.30
    results["research_candidate_with_v"] = {
        "lines": lines,
        "independently_recomputed_hit": hit_check,
        "same_uncapped_mean_as_current": True,
        "production_ready": False,
        "remaining_validation": ["full payout distribution", "variance", "attainable max and cap loss", "net profit frequency", "bonus tuning", "visual readability"],
    }
results["original_files_unchanged"] = before == snapshot()
baseline = json.loads((OUTPUT.parent / "original_hashes.json").read_text())
results["matches_prior_audit_hashes"] = before == baseline
(OUTPUT / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(results, indent=2, ensure_ascii=False))
