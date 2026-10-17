from .symbols import WILD

ALLOWED_CHARGE_REELS = (1, 2, 3)  # human reels 2,3,4

def expand_reel(board, reel_index):
    if reel_index not in ALLOWED_CHARGE_REELS:
        raise ValueError("Hussar Charge only allows human reels 2,3,4")
    return tuple((WILD,WILD,WILD) if i == reel_index else tuple(reel) for i,reel in enumerate(board))

def draw_charge(cfg, rng):
    probability = cfg.charge_probability
    if rng.randrange(probability.denominator) >= probability.numerator:
        return None
    draw = rng.randrange(sum(cfg.charge_weights))
    for reel, weight in zip(ALLOWED_CHARGE_REELS, cfg.charge_weights):
        if draw < weight:
            return reel
        draw -= weight
    raise AssertionError("Invalid Charge weights")
