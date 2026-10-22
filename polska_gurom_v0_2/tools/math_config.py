"""Stable identity for authoritative mathematical values and rule assumptions."""
from __future__ import annotations

import hashlib
import json

MATH_FIELDS = (
    "SYMBOLS", "REGULAR_SYMBOLS", "WILD", "SCATTER", "ROWS", "REELS",
    "PAYOUT_SCALE", "MAX_WIN_UNITS", "PAYTABLE_UNITS",
    "SCATTER_PAYTABLE_UNITS", "PAYLINES", "REEL_STRIPS", "FREE_SPINS",
    "FS_LINE_MULTIPLIER", "EXPANDING_REELS", "EXPANDING_WILD_NUMERATOR",
    "EXPANDING_WILD_DENOMINATOR",
    "MATH_ASSUMPTIONS",
)
ASSUMPTIONS = {
    "stops": "uniform_independent",
    "scatter_count": "original_grid_before_expansion",
    "retrigger": False,
    "line_direction": "left_to_right",
    "line_award": "best_single_interpretation",
    "expansion_selection": "uniform_among_expanding_reels",
    "round_cap": "base_plus_all_free_spins",
}


def math_config_payload(config=None):
    if config is None:
        from polska_gurom import config
    return {
        "format_version": 1,
        "configuration": {name: getattr(config, name) for name in MATH_FIELDS},
        "assumptions": ASSUMPTIONS,
    }


def compute_config_fingerprint(config=None):
    payload = math_config_payload(config)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


math_config_sha256 = compute_config_fingerprint
