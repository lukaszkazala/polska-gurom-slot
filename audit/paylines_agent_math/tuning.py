"""Read-only exact expectation and illustrative tuning calculations."""
from collections import Counter
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import json
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, r"D:\Kazaluka_slots\polska_gurom_phase2_v0.1")
from polska_gurom import config as c

pay = {s: {n: F(str(v)) for n, v in row.items()} for s, row in c.PAYTABLE.items()}
counts = [Counter(strip) for strip in c.REEL_STRIPS]

def line_ev(forced=None):
    numerator = 0
    denom = 20 * 36 ** (5 - (forced is not None))
    for seq in product(*[([c.WILD] if r == forced else c.SYMBOLS) for r in range(5)]):
        multiplicity = 1
        for r, sym in enumerate(seq):
            if r != forced:
                multiplicity *= counts[r][sym]
        prize = 0
        for target in c.REGULAR_SYMBOLS:
            length = 0
            for sym in seq:
                if sym not in (target, c.WILD):
                    break
                length += 1
            if length >= 3:
                prize = max(prize, int(pay[target][length] * 20))
        numerator += multiplicity * prize
    return F(numerator, denom)

L = len(c.PAYLINES) * line_ev()
E = sum(len(c.PAYLINES) * line_ev(r) for r in (1, 2, 3)) / 3
# Only one Scatter per strip, hence at most one per visible column.
import math
sd = {k: F(math.comb(5, k) * 11 ** (5-k), 12**5) for k in range(6)}
S = sum(prob * F(str(c.SCATTER_PAYTABLE.get(k, 0))) for k, prob in sd.items())
q = sum(prob for k, prob in sd.items() if k >= 3)
N = sum(prob * c.FREE_SPINS.get(k, 0) for k, prob in sd.items())
B = L + S
p = F(1, 4)
fs_ev = B + p * (E-L)
bonus = N * fs_ev
R = B + bonus
target = F(96, 100)
desired_bonus = target-B
desired_fs_ev = desired_bonus/N
desired_conditional_bonus = desired_bonus/q
m = desired_bonus/bonus
p_needed = (desired_fs_ev-B)/(E-L)
m_at_one = desired_bonus/(N*(E+S))
max_base_trigger5 = F(475, 10)
max_free = F(24915, 100)
max_bonus_scale_without_cap = (5000-max_base_trigger5)/(12*max_free)
p_with_safe_bonus_scale = (desired_fs_ev/max_bonus_scale_without_cap-B)/(E-L)
scatter_component = S*(1+N)
line_component = R-scatter_component
global_line_scale = (target-scatter_component)/line_component
out = {
    "current": {"base_line_rtp": L, "scatter_rtp": S, "base_rtp": B,
        "expanded_line_rtp": E, "bonus_frequency": q,
        "mean_free_spins_per_trigger": N/q, "mean_free_spins_per_paid_round": N,
        "free_spin_ev": fs_ev, "bonus_ev_conditional": bonus/q,
        "bonus_rtp": bonus, "total_rtp": R},
    "preserve_base_target_96pct": {"required_bonus_rtp": desired_bonus,
        "required_mean_free_spin_payout": desired_fs_ev,
        "required_bonus_payout_conditional": desired_conditional_bonus,
        "bonus_multiplier_before_cap": m,
        "required_expansion_probability_without_other_changes": p_needed,
        "rtp_at_expansion_probability_1": B+N*(E+S),
        "bonus_multiplier_at_expansion_probability_1": m_at_one,
        "round_max_at_expansion_1_and_bonus_multiplier": max_base_trigger5+12*m_at_one*max_free,
        "largest_bonus_multiplier_before_cap_can_bind": max_bonus_scale_without_cap,
        "minimum_expansion_probability_for_cap_inactive_96pct_scale": p_with_safe_bonus_scale},
    "illustrative_nonrecommended_global_line_scale": {
        "regular_paytable_multiplier": global_line_scale,
        "base_rtp_after": L*global_line_scale+S,
        "bonus_rtp_after": target-(L*global_line_scale+S),
        "rtp_after": target,
        "conservative_round_payout_bound": F(30373, 10)*global_line_scale},
    "adding_lines_unchanged_per_line_pay": {
        "required_line_count": 20*(target-scatter_component)/line_component,
        "rtp_24_lines": line_component*F(24,20)+scatter_component},
    "notes": [
        "All expectations are exact until payout cap or paytable rounding is changed.",
        "Scaling the whole current bonus by the 25% multiplier can make the 5000 cap bind; solve capped expectation again.",
        "100% expansion plus the exact multiplier is an illustrative exact algebraic solution with cap inactive, not a design recommendation.",
        "Global line scaling leaves probability of a strictly positive win unchanged and misses target allocation."
    ]
}

def convert(obj):
    if isinstance(obj, F):
        return {"value": float(obj), "fraction": str(obj)}
    if isinstance(obj, dict):
        return {k: convert(v) for k,v in obj.items()}
    if isinstance(obj, list):
        return [convert(v) for v in obj]
    return obj

output = convert(out)
Path(__file__).with_name("tuning_results.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
print(json.dumps(output, indent=2))
