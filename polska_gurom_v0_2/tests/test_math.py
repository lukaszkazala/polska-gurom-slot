"""Frozen acceptance targets from independent exact enumeration, not simulation."""
from decimal import Decimal
from fractions import Fraction as F
import json
import math
from pathlib import Path
from unittest.mock import patch
from polska_gurom import config as c
from polska_gurom.theory import exact_first_moments, scatter_distribution_fraction
from tools.math_config import compute_config_fingerprint

ROOT = Path(__file__).resolve().parents[1]


def test_exact_first_moments_match_independent_frozen_results():
    result = exact_first_moments()
    assert result["base_line_rtp"] == F(110231291, 151165440)
    assert result["base_rtp"] == F(222291157, 302330880)
    assert result["bonus_rtp_uncapped"] == F(117411530827874911981, 522427760640000000000)
    assert result["total_rtp_uncapped"] == F(501530650123874911981, 522427760640000000000)
    assert result["base_rtp"] + result["bonus_rtp_uncapped"] == result["total_rtp_uncapped"]
    assert abs(result["total_rtp_uncapped"]-F(96, 100)) < F(1, 10**9)
    assert result["bonus_frequency"] == F(211, 41472)


def test_scatter_distribution_is_exact_binomial_window_probability():
    distribution = scatter_distribution_fraction()
    assert distribution == {k: F(math.comb(5,k)*11**(5-k),12**5) for k in range(6)}
    assert sum(distribution.values()) == 1


def test_model_assumptions_cannot_be_changed_silently():
    changed = {**c.MATH_ASSUMPTIONS, "retriggers_enabled": True}
    old_fingerprint = compute_config_fingerprint(c)
    with patch.object(c, "MATH_ASSUMPTIONS", changed):
        assert compute_config_fingerprint(c) != old_fingerprint
        try:
            exact_first_moments()
        except ValueError:
            pass
        else:
            raise AssertionError("Retriggers cannot use the no-retrigger formula")


def test_full_distribution_report_is_current_and_meets_targets():
    report = json.loads((ROOT/"verification"/"math_validation.json").read_text())
    assert report["math_config_sha256"] == compute_config_fingerprint(c)
    assert abs(report["rtp_uncapped"]-.96) < 1e-9
    assert .25 <= report["positive_return_probability"] <= .30
    assert 150 <= report["rounds_per_bonus"] <= 250
    assert abs(report["positive_return_probability"]-31187/104976) < 1e-15
    assert abs(report["positive_return_probability"]-sum(report[key] for key in (
        "positive_below_bet_probability", "net_profit_probability", "break_even_probability"))) < 1e-15
    assert Decimal(report["cap_bound"]["cap_rtp_loss_upper_bound_decimal"]) < Decimal("1e-40")
    assert report["max_free_spin"] == 714
    assert report["max_round_before_cap"] == 8618.22


def test_invalid_inputs_fail_before_settlement():
    from polska_gurom import game
    import random
    for grid in ([], [["L1"]*5]*2, [["L1"]*4]*3, [["unknown"]*5]*3):
        try:
            game.evaluate_paid_spin(grid)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid grid was accepted")
    valid = [["L1"]*5]*3
    for p in (-.1, 1.1, float("nan")):
        try:
            game.evaluate_free_spin(valid, random.Random(1), p)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid expansion probability was accepted")
    for amount in (-1, .5, True):
        try:
            game.cap_payout_units(amount)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid integer award was accepted")
