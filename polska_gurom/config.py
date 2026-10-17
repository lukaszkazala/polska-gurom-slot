"""Versioned data in TOTAL BET integer units. No presentation dependency."""
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
import hashlib
import json
from .symbols import REGULAR, SYMBOLS, SCATTER

ROOT = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class Config:
    version: str
    reels: tuple
    paylines: tuple
    paytable: dict
    scatter_pays: dict
    fs_awards: dict
    charge_probability: Fraction
    charge_weights: tuple
    scale: int = 100
    cap_units: int = 500000

    @property
    def config_hash(self):
        data = dict(version=self.version, reels=self.reels, paylines=self.paylines,
                    paytable=self.paytable, scatter_pays=self.scatter_pays,
                    fs_awards=self.fs_awards,
                    charge_probability=[self.charge_probability.numerator,
                                        self.charge_probability.denominator],
                    charge_weights=self.charge_weights, scale=self.scale,
                    cap_units=self.cap_units)
        return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def validate_config(cfg):
    if len(cfg.reels) != 5 or any(len(r) < 3 for r in cfg.reels):
        raise ValueError("Exactly five cyclic strips of length >=3 required")
    if any(s not in SYMBOLS for r in cfg.reels for s in r):
        raise ValueError("Unknown mathematical symbol")
    if len(cfg.paylines) != 20 or len(set(cfg.paylines)) != 20:
        raise ValueError("Exactly twenty unique paylines required")
    if any(len(line) != 5 or any(type(row) is not int or row not in (0,1,2) for row in line) for line in cfg.paylines):
        raise ValueError("Invalid payline coordinates")
    if set(cfg.paytable) != set(REGULAR):
        raise ValueError("Only all eight regular symbols may have paytable entries")
    for table in cfg.paytable.values():
        if set(table) != {3,4,5} or any(type(v) is not int or v < 0 for v in table.values()):
            raise ValueError("Nonnegative integer payouts for 3/4/5 required")
        if not table[3] <= table[4] <= table[5]:
            raise ValueError("Payouts must be nondecreasing in match length")
    if set(cfg.fs_awards) != {3,4,5} or cfg.fs_awards != {3:8,4:10,5:12}:
        raise ValueError("Approved Free Spin awards are 8/10/12")
    if set(cfg.scatter_pays) != {3,4,5} or any(type(v) is not int or v < 0 for v in cfg.scatter_pays.values()):
        raise ValueError("Scatter payouts must be nonnegative integer units")
    if not 0 <= cfg.charge_probability <= 1 or len(cfg.charge_weights) != 3:
        raise ValueError("Invalid Charge probabilities")
    if any(type(w) is not int or w < 0 for w in cfg.charge_weights) or sum(cfg.charge_weights) <= 0:
        raise ValueError("Charge weights must be nonnegative integer weights")
    if type(cfg.scale) is not int or cfg.scale <= 0 or cfg.cap_units != 5000 * cfg.scale:
        raise ValueError("Full round cap must be exactly 5000 TOTAL BET")
    # This implementation intentionally excludes >5 visible scatters.
    for reel in cfg.reels:
        if any(sum(reel[(stop + row) % len(reel)] == SCATTER for row in range(3)) > 1 for stop in range(len(reel))):
            raise ValueError("At most one visible Scatter per reel is required")
    return cfg

def load_config(path=None):
    with open(path or ROOT / "configs/reconstruction_v0_1.json", encoding="utf-8") as stream:
        data = json.load(stream)
    cfg = Config(version=data["version"], reels=tuple(tuple(r) for r in data["reels"]),
                 paylines=tuple(tuple(p) for p in data["paylines"]),
                 paytable={s:{int(k):v for k,v in p.items()} for s,p in data["paytable"].items()},
                 scatter_pays={int(k):v for k,v in data["scatter_pays"].items()},
                 fs_awards={int(k):v for k,v in data["fs_awards"].items()},
                 charge_probability=Fraction(*data["charge_probability"]),
                 charge_weights=tuple(data["charge_weights"]), scale=data["scale"], cap_units=data["cap_units"])
    return validate_config(cfg)
