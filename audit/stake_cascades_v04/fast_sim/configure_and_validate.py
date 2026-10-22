"""Snapshot the live engine's numeric rules and independently validate C# traces."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'test-interface' / 'engine'))
from polska_gurom import config as c
from polska_gurom.game import play_round

MASK = (1 << 64) - 1

class SplitMix64:
    def __init__(self, seed): self.state = seed & MASK
    def next(self):
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return z ^ (z >> 31)
    def randrange(self, stop):
        threshold = (1 << 64) % stop
        while True:
            r = self.next()
            if r >= threshold: return r % stop
    def choice(self, values): return values[self.randrange(len(values))]

def mix(h, v):
    return ((h ^ ((v + 1) & MASK)) * 1099511628211) & MASK

def grid_hash(h, grid):
    for reel in range(5):
        for row in range(3): h = mix(h, c.SYMBOLS.index(grid[row][reel]))
    return h

def spin_hash(spin):
    h = grid_hash(14695981039346656037, spin.grid)
    h = mix(h, spin.scatter_count)
    h = mix(h, -1 if spin.expanding_reel is None else spin.expanding_reel)
    for stage in spin.cascades:
        h = grid_hash(h, stage.evaluation_grid)
        h = mix(h, stage.line_payout_units)
        h = mix(h, stage.payout_units)
        mask = sum(1 << (reel * 3 + row) for row, reel in stage.removed_positions)
        h = mix(h, mask)
    return h

def signed32(v): return v if v < 2**31 else v - 2**32

def validate(path):
    data = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    rng = SplitMix64(data['seed'])
    checked = 0
    for actual in data['traces']:
        r = play_round(rng)
        h = spin_hash(r.base)
        for spin in r.free_spins:
            sh = spin_hash(spin)
            h = mix(h, signed32(sh & 0xffffffff))
            h = mix(h, signed32(sh >> 32))
            h = mix(h, spin.payout_units)
        expected = dict(round=checked, payout=r.payout_units,
                        basePayout=r.base.payout_units, bonusPayout=r.bonus_payout_units,
                        scatter=r.base.scatter_count, freeSpins=len(r.free_spins),
                        expansions=r.expansions,
                        stages=len(r.base.cascades) + sum(len(s.cascades) for s in r.free_spins),
                        hash=f'{h:016x}')
        if actual != expected:
            raise AssertionError({'round': checked, 'C#': actual, 'Python': expected})
        checked += 1
    summary = {'checked_rounds': checked, 'exact_trace_comparison': 'passed',
               'fields': 'Every generated/evaluation grid, scatter count, expanding reel, cascade line payout/credit/removal mask, spin totals and round totals',
               'rng': 'SplitMix64; identical unbiased bounded rejection draws',
               'source_sha256': hashlib.sha256((HERE / 'CascadeFast.cs').read_bytes()).hexdigest()}
    (HERE / 'crosscheck.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))

def configure():
    ids = {s: i for i, s in enumerate(c.SYMBOLS)}
    pay = [[c.PAYTABLE_UNITS[s].get(n, 0) for n in range(6)] for s in c.REGULAR_SYMBOLS]
    data = dict(strips=[[ids[s] for s in strip] for strip in c.REEL_STRIPS],
                refill=[[ids[s] for s in strip] for strip in c.REFILL_STRIPS],
                lines=c.PAYLINES, pay=pay,
                scatter=[c.SCATTER_PAYTABLE_UNITS.get(i, 0) for i in range(6)],
                free=[c.FREE_SPINS.get(i, 0) for i in range(6)], scale=c.PAYOUT_SCALE,
                cap=c.MAX_WIN_UNITS, fsMultiplier=c.FS_LINE_MULTIPLIER,
                expansionNumerator=c.EXPANDING_WILD_NUMERATOR,
                expansionDenominator=c.EXPANDING_WILD_DENOMINATOR, maxCascades=c.MAX_CASCADES)
    (HERE / 'config.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
    print('Saved current natural-engine configuration')

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--validate', type=Path);args=p.parse_args()
    validate(args.validate) if args.validate else configure()
