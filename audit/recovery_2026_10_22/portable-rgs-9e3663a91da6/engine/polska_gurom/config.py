from __future__ import annotations

MATH_VERSION = "0.5.0-any-start"
TARGET_RTP = 0.96
CASCADES_ENABLED = True
SYMBOLS = ("L1","L2","L3","L4","P1","P2","P3","P4","WILD","SCATTER")
REGULAR_SYMBOLS = SYMBOLS[:8]
WILD = "WILD"
SCATTER = "SCATTER"
ROWS = 3
REELS = 5
MAX_WIN = 5000.0
PAYOUT_SCALE = 100  # Integer hundredths of TOTAL BET.
MAX_WIN_UNITS = 5000 * PAYOUT_SCALE
MAX_CASCADES = 1000  # Emergency bound on evaluated stages in one spin.
FS_LINE_MULTIPLIER = 4  # Line awards only; Scatter is never multiplied.
EXPANDING_WILD_NUMERATOR = 250000000
EXPANDING_WILD_DENOMINATOR = 1000000000
EXPANDING_WILD_PROBABILITY = EXPANDING_WILD_NUMERATOR / EXPANDING_WILD_DENOMINATOR
EXPANDING_REELS = (1, 2, 3)  # zero-based: reels 2, 3, 4
GENERATOR_ASSUMPTIONS = {
    "uniform_independent_reel_stops": True,
    "expansion_independent_of_grid": True,
    "uniform_expanding_reel_choice": True,
    "free_spins_independent": True,
    "retriggers_enabled": False,
    "scatter_evaluated_before_expansion": True,
    "falling_cascades_enabled": True,
    "scatter_refills_enabled": False,
}
# Reel probabilities describe candidate generation. Published weights, including
# complete bonus rounds, determine the final RGS distribution and its RTP.
MATH_ASSUMPTIONS = {"selection": "integer_weighted_complete_round_books", "target_rtp": TARGET_RTP,
                    "payline_start": "any_reel", "award_per_line": "highest_only",
                    "falling_cascades_enabled": True, "retriggers_enabled": False}
FREE_SPINS = {3: 8, 4: 10, 5: 12}
SCATTER_PAYTABLE = {3: 1.0, 4: 5.0, 5: 20.0}

# Display multiples of TOTAL BET. Integer values below drive settlement.
PAYTABLE = {
    "L1": {3: 0.10, 4: 0.60, 5: 2.00},
    "L2": {3: 0.20, 4: 0.80, 5: 2.80},
    "L3": {3: 0.20, 4: 1.00, 5: 3.60},
    "L4": {3: 0.30, 4: 1.30, 5: 4.80},
    "P1": {3: 0.50, 4: 2.00, 5: 8.00},
    "P2": {3: 0.60, 4: 2.80, 5: 12.00},
    "P3": {3: 1.00, 4: 4.40, 5: 20.00},
    "P4": {3: 1.60, 4: 8.00, 5: 40.00},
}

PAYTABLE_UNITS = {
    symbol: {n: round(value * PAYOUT_SCALE) for n, value in row.items()}
    for symbol, row in PAYTABLE.items()
}
SCATTER_PAYTABLE_UNITS = {k: round(v * PAYOUT_SCALE) for k, v in SCATTER_PAYTABLE.items()}

# 20 fixed paylines, nine shared three-reel beginnings. Row indices 0..2.
PAYLINES = (
    (1,1,1,1,1), (1,1,1,0,0), (1,1,1,2,2),
    (0,0,0,0,0), (2,2,2,2,2),
    (0,0,0,1,1), (2,2,2,1,1),
    (0,1,1,1,0), (2,1,1,1,2),
    (0,1,1,2,2), (2,1,1,0,0),
    (1,1,0,0,1), (1,1,2,2,1),
    (1,1,0,1,2), (1,1,2,1,0),
    (0,0,0,1,2),
    (0,1,2,1,0), (2,1,0,1,2),
    (0,1,2,2,1), (2,1,0,0,1),
)

# Every strip has 36 stops with the same composition but a different ordering.
# Composition per reel: L1 7, L2 5, L3 5, L4 4, P1 4, P2 3, P3 3,
# P4 2, WILD 2, SCATTER 1.
_BASE = [
    "L1","P1","L2","L3","WILD","L1","P2","L4","L2","P3","L1","P1",
    "L3","P4","L2","L1","P2","L4","L3","P1","L1","P3","L2","WILD",
    "L4","L1","P4","L3","P1","L2","P2","L4","L3","P3","L1","SCATTER",
]

def _rotate(seq, n):
    n %= len(seq)
    return tuple(seq[n:] + seq[:n])

REEL_STRIPS = (
    tuple(_BASE),
    _rotate(_BASE, 7),
    _rotate(_BASE, 13),
    _rotate(_BASE, 19),
    _rotate(_BASE, 27),
)

# Retain each reel's regular/Wild weights; Scatter only comes from the
# original reel window, so a cascade cannot award another trigger.
REFILL_STRIPS = tuple(tuple(symbol for symbol in strip if symbol != SCATTER)
                      for strip in REEL_STRIPS)
