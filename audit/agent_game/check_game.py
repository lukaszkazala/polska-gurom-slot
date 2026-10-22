import sys
sys.dont_write_bytecode = True
sys.path.insert(0, r'D:\Kazaluka_slots\polska_gurom_phase2_v0.1')
import itertools
import json
from unittest.mock import patch

from polska_gurom import game
from polska_gurom.config import PAYTABLE, REGULAR_SYMBOLS, SYMBOLS


def independent_line_oracle(symbols):
    candidates = set(REGULAR_SYMBOLS)
    best = 0.0
    for length, symbol in enumerate(symbols, 1):
        if symbol != 'WILD':
            candidates.intersection_update((symbol,))
        if not candidates:
            break
        if length >= 3:
            best = max(best, *(PAYTABLE[s][length] for s in candidates))
    return best


mismatches = []
for symbols in itertools.product(SYMBOLS, repeat=5):
    actual = game._line_best_win(list(symbols))
    expected = independent_line_oracle(symbols)
    if actual != expected:
        mismatches.append((symbols, actual, expected))


class FixedExpansion:
    def __init__(self, reel):
        self.reel = reel
    def random(self):
        return 0.0
    def choice(self, _):
        return self.reel


scatter_grid = [
    ['SCATTER', 'SCATTER', 'SCATTER', 'L4', 'P1'],
    ['L1', 'L2', 'L3', 'L4', 'P1'],
    ['L2', 'L3', 'L4', 'P1', 'P2'],
]
before = [r[:] for r in scatter_grid]
fs_result = game.evaluate_free_spin(scatter_grid, FixedExpansion(1), 1.0)
assert fs_result.scatter_count == 3
assert fs_result.scatter_payout == 1.0
assert fs_result.free_spins_awarded == 0 and not fs_result.bonus_triggered
assert scatter_grid == before


def round_with_reel(reel):
    uniform = [['L1'] * 5 for _ in range(3)]
    with patch.object(game, 'generate_grid', side_effect=[scatter_grid] + [uniform] * 8):
        return game.play_round(FixedExpansion(reel), 1.0)


round_reel_2 = round_with_reel(1)
round_reel_3 = round_with_reel(2)
assert round_reel_2 == round_reel_3

cap_base = [['SCATTER'] * 5, ['WILD'] * 5, ['WILD'] * 5]
cap_fs = [['WILD'] * 5 for _ in range(3)]
with patch.object(game, 'generate_grid', side_effect=[cap_base] + [cap_fs] * 12):
    capped_base, capped_bonus, _ = game.play_round(FixedExpansion(1), 1.0)
assert capped_base.payout + capped_bonus == 5000.0

print(json.dumps({
    'exhaustive_line_cases': len(SYMBOLS) ** 5,
    'line_mismatches': mismatches,
    'uniform_l1_grid_payout': game.evaluate_lines([['L1'] * 5 for _ in range(3)]),
    'all_wild_line_payout': game._line_best_win(['WILD'] * 5),
    'scatter_preserved_through_expansion': fs_result.__dict__,
    'different_expansion_events_have_equal_round_output': {
        'reel_2': [round_reel_2[0].__dict__, *round_reel_2[1:]],
        'reel_3': [round_reel_3[0].__dict__, *round_reel_3[1:]],
    },
    'round_cap_crossed_and_applied': {
        'base': capped_base.__dict__,
        'credited_bonus': capped_bonus,
        'round_total': capped_base.payout + capped_bonus,
    },
}, indent=2))
