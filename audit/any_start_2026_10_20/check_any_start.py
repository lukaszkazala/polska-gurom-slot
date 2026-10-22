"""Independent contiguous-run oracle, full exported-book and settlement audit."""
from collections import Counter
from fractions import Fraction
from functools import lru_cache
from itertools import product
from pathlib import Path
import csv
import hashlib
import io
import json
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "test-interface-any-start"
sys.path[:0] = [str(STAGE / "engine"), str(ROOT / "audit/stake_cascades_v04/dependencies")]
from polska_gurom import config, game, selection
import zstandard

started = time.perf_counter()
counts = Counter()

@lru_cache(maxsize=100000)
def oracle(sequence):
    # Enumerate all intervals and target symbols; no production evaluator call.
    candidates = []
    for start in range(3):
        for stop in range(start + 3, 6):
            actual = set(sequence[start:stop]) - {config.WILD}
            for order, symbol in enumerate(config.REGULAR_SYMBOLS):
                if actual <= {symbol}:
                    candidates.append((config.PAYTABLE_UNITS[symbol][stop-start], -start, -order, stop-start, symbol))
    if not candidates:
        return None, 0, 0, 0
    units, neg_start, _, length, symbol = max(candidates)
    return symbol, length, units, -neg_start

for sequence in product(config.SYMBOLS, repeat=5):
    assert game._line_award_with_start(sequence) == oracle(sequence), sequence
    counts["line_sequences_exhaustively_checked"] += 1
print("Exhaustive 100000 line sequences passed", flush=True)

expected_screenshot = (("P1","L1","L1","L1","P3"),
                       ("L3","P2","P4","P1","L1"),
                       ("P4","L4","L3","L2","SCATTER"))
spec = {"recipe":{"name":"middle_run_regression","stops":[11,8,12,17,6],
                  "wild_refill_limit":0,"fallback_seed":20261020}}
reproduced = selection.replay_spec(spec)
assert reproduced.base.grid == expected_screenshot
wins = reproduced.base.line_wins
assert [w.line_id for w in wins] == [4,12,20]
assert wins[0].start_reel == 1 and wins[0].count == 3 and wins[0].payout_units == 10
assert wins[0].positions == ((0,1),(0,2),(0,3))
assert set(reproduced.base.cascades[0].removed_positions) == {p for w in wins for p in w.positions}

def check_spin(spin, available):
    credited = min(spin["scatter_payout_units"], available)
    raw_lines = 0
    assert spin["cascades"][0]["evaluation_grid"] == spin["evaluation_grid"]
    assert spin["cascades"][0]["line_wins"] == spin["line_wins"]
    assert not spin["cascade_limit_reached"]
    for index, step in enumerate(spin["cascades"]):
        grid = step["evaluation_grid"]
        expected = []
        for line_id, rows in enumerate(config.PAYLINES, 1):
            symbol, length, units, start = oracle(tuple(grid[rows[r]][r] for r in range(5)))
            if units:
                expected.append((line_id, symbol, length, units * spin["line_multiplier"], start))
        actual = [(w["line_id"],w["symbol"],w["count"],w["payout_units"],w["start_reel"])
                  for w in step["line_wins"]]
        assert actual == expected
        raw = sum(w[3] for w in expected)
        assert step["line_payout_units"] == raw
        assert step["payout_units"] == min(raw, available - credited)
        credited += step["payout_units"]
        raw_lines += raw
        counts["cascade_stages_checked"] += 1
        counts["line_awards_checked"] += len(actual)
        if index + 1 == len(spin["cascades"]):
            assert not step["removed_positions"] and not step["movements"]
            assert not actual or credited == available
        else:
            removed = {(w["rows"][r],r) for w in step["line_wins"]
                       for r in range(w["start_reel"],w["start_reel"]+w["count"])}
            assert removed == {tuple(p) for p in step["removed_positions"]}
            after = spin["cascades"][index+1]["evaluation_grid"]
            for reel in range(5):
                survivors = [grid[row][reel] for row in range(3) if (row,reel) not in removed]
                assert not survivors or [row[reel] for row in after][-len(survivors):] == survivors
            spawned = [m for m in step["movements"] if m["from_row"] < 0]
            assert len(spawned) == len(removed)
            assert all(m["symbol"] != config.SCATTER for m in spawned)
            for move in step["movements"]:
                assert after[move["to_row"]][move["reel"]] == move["symbol"]
    assert spin["line_payout_units"] == raw_lines
    assert spin["raw_payout_units"] == raw_lines + spin["scatter_payout_units"]
    assert spin["payout_units"] == credited

bank = STAGE / "stake_math"
manifest = json.loads((bank/"selection.json").read_text())
assert manifest["math_version"] == config.MATH_VERSION
assert manifest["source_fingerprint"] == selection.source_fingerprint()
lut = [tuple(map(int,row)) for row in csv.reader((bank/"lookUpTable_base_0.csv").open())]
total_weight = sum(w for _,w,_ in lut)
rtp = Fraction(sum(w*p for _,w,p in lut),total_weight * config.PAYOUT_SCALE)
assert total_weight == 10**12 and rtp == Fraction(96,100)
assert min(w for _,w,_ in lut) > 0
assert hashlib.sha256((bank/"lookUpTable_base_0.csv").read_bytes()).hexdigest() == manifest["lut_sha256"]
max_mass = sum(w for _,w,p in lut if p == config.MAX_WIN_UNITS)
assert Fraction(total_weight,max_mass) == 8_000_000
fs_coverage = Counter()
offset_books = 0
with (bank/"books_base.jsonl.zst").open("rb") as compressed:
    stream = zstandard.ZstdDecompressor().stream_reader(compressed)
    for index, line in enumerate(io.TextIOWrapper(stream,encoding="utf-8")):
        book = json.loads(line)
        assert book["id"] == lut[index][0] == index
        result = book["events"][0]["data"]
        available = config.MAX_WIN_UNITS
        for spin in [result["base"],*result["free_spins"]]:
            check_spin(spin,available)
            available -= spin["payout_units"]
            if any(w["start_reel"] > 0 for step in spin["cascades"] for w in step["line_wins"]):
                offset_books += 1
        assert result["payout_units"] == book["payoutMultiplier"] == lut[index][2]
        assert result["payout_units"] == config.MAX_WIN_UNITS - available
        assert result["payout_units"] == result["base"]["payout_units"] + sum(result["free_spin_credits"])
        assert result["free_spin_credits"] == [s["payout_units"] for s in result["free_spins"]]
        if result["base"]["bonus_triggered"]:
            fs = config.FREE_SPINS[min(5,result["base"]["scatter_count"])]
            assert len(result["free_spins"]) == fs or result["payout_units"] == config.MAX_WIN_UNITS
            fs_coverage[fs] += lut[index][1]
        counts["complete_books_checked"] += 1
        if (index+1) % 20000 == 0:
            print(f"Independent audit: {index+1} complete books",flush=True)
assert counts["complete_books_checked"] == len(lut) == len(manifest["books"])
assert set(fs_coverage) == {8,10,12} and min(fs_coverage.values()) > 0
mid_id = manifest["regression_book_ids"]["middle_run"]
assert lut[mid_id][2] == reproduced.payout_units and lut[mid_id][1] > 0
selection.load_distribution()

report = {"passed":True,"math_version":config.MATH_VERSION,**counts,
          "rtp_exact_fraction":str(rtp),"total_weight":total_weight,
          "max_win_one_in":str(Fraction(total_weight,max_mass)),
          "bonus_weight_by_free_spins":dict(fs_coverage),"offset_winning_spins_in_bank":offset_books,
          "screenshot":{"first_grid":expected_screenshot,"line_id":4,"start_reel":1,
                        "count":3,"line_payout_units":10,"round_payout_units":reproduced.payout_units,
                        "all_winning_lines":[w.line_id for w in wins],
                        "removed_positions":reproduced.base.cascades[0].removed_positions,"published_book_id":mid_id},
          "elapsed_seconds":round(time.perf_counter()-started,2)}
(Path(__file__).resolve().parent/"independent_audit.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2),flush=True)
