"""Unit bridge only; not an SDK integration or publication pipeline."""
from fractions import Fraction

def to_line_bet_paytable(cfg):
    """If an external interface requires B/20 multipliers, multiply by 20."""
    return {s:{n:Fraction(value * 20,cfg.scale) for n,value in table.items()} for s,table in cfg.paytable.items()}

def current_sdk_payout_compatible(paid_units, scale=100):
    exact_sdk_units = Fraction(paid_units * 100, scale)
    return exact_sdk_units.denominator == 1 and exact_sdk_units >= 0 and exact_sdk_units.numerator % 10 == 0
