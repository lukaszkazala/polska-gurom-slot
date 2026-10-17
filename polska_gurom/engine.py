"""Scalar source of truth. Inject random.Random; no cross-round state."""
from dataclasses import dataclass, asdict
from .reels import board_from_stops
from .evaluator import evaluate_line, evaluate_board, LineWin
from .scatter import count_scatters, scatter_award
from .bonus import expand_reel, draw_charge
from .cap import settle_cap

@dataclass(frozen=True)
class SpinResult:
    natural_board: tuple
    board: tuple
    stops: tuple
    line_wins: tuple
    scatter_count: int
    scatter_units: int
    line_units: int
    total_units: int
    charge_reel: object
    is_free: bool
    awarded_free_spins: int

@dataclass(frozen=True)
class RoundResult:
    base: SpinResult
    free_spins: tuple
    raw_base_units: int
    raw_bonus_units: int
    raw_total_units: int
    paid_base_units: int
    paid_bonus_units: int
    paid_total_units: int
    cap_reduction_units: int
    cap_reached: bool

def evaluate_spin(cfg, stops, is_free=False, charge_reel=None):
    if charge_reel is not None and not is_free:
        raise ValueError("Charge is only allowed in Free Spins")
    natural = board_from_stops(cfg, stops)
    scatters = count_scatters(natural)
    scatter_units, awarded = scatter_award(scatters, cfg, is_free)
    board = natural if charge_reel is None else expand_reel(natural,charge_reel)
    wins = evaluate_board(board,cfg)
    line_units = sum(win.payout_units for win in wins)
    return SpinResult(natural,board,tuple(stops),wins,scatters,scatter_units,
                      line_units,line_units+scatter_units,charge_reel,is_free,awarded)

def play_spin(cfg, rng, is_free=False):
    stops = tuple(rng.randrange(len(reel)) for reel in cfg.reels)
    charge = draw_charge(cfg,rng) if is_free else None
    return evaluate_spin(cfg,stops,is_free,charge)

def assemble_round(cfg, base, free_spins):
    free_spins = tuple(free_spins)
    if base.is_free or len(free_spins) != base.awarded_free_spins or any(not s.is_free or s.awarded_free_spins for s in free_spins):
        raise ValueError("Round trace must contain exactly the awarded Free Spins, without retriggers")
    raw_base = base.total_units
    raw_bonus = sum(spin.total_units for spin in free_spins)
    return RoundResult(base,free_spins,raw_base,raw_bonus,raw_base+raw_bonus,
                       **settle_cap(raw_base,raw_bonus,cfg.cap_units))

def play_round(cfg, rng):
    base = play_spin(cfg,rng)
    # Continue all awarded spins even after cap to retain a complete raw trace.
    return assemble_round(cfg,base,(play_spin(cfg,rng,True) for _ in range(base.awarded_free_spins)))

def round_to_dict(result):
    data = asdict(result)
    # Resolve every credit here so a frontend can replay the completed round.
    cap = result.paid_total_units
    paid = raw = 0
    settlement = []
    for index, spin in enumerate((result.base,) + result.free_spins):
        line_credit = min(spin.line_units, max(cap-paid, 0))
        paid += line_credit
        scatter_credit = min(spin.scatter_units, max(cap-paid, 0))
        paid += scatter_credit
        raw += spin.total_units
        settlement.append(dict(spin_index=index, is_free=spin.is_free,
                               raw_line_units=spin.line_units, raw_scatter_units=spin.scatter_units,
                               raw_total_units=spin.total_units, paid_line_units=line_credit,
                               paid_scatter_units=scatter_credit,
                               paid_total_units=line_credit+scatter_credit,
                               cumulative_raw_units=raw, cumulative_paid_units=paid))
    data["settlement_trace"] = settlement
    return data
