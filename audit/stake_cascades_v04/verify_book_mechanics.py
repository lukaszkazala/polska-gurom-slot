"""Independently evaluate every exported book and compare local replay byte-for-byte."""
from dataclasses import asdict
import hashlib
import io
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE / "dependencies"), str(ROOT / "test-interface" / "engine"),
               str(ROOT / "test-interface" / "qa")]
import zstandard
import check_cascade_math as oracle
from polska_gurom import selection


def main():
    start = time.perf_counter()
    manifest, cdf, payouts = selection.load_distribution()
    folder = ROOT / "test-interface" / "stake_math"
    original = oracle.original_manifest()
    oracle.check_forced_cases()
    events_hashes = set()
    cap_books = bonus_books = 0
    with (folder / "books_base.jsonl.zst").open("rb") as source:
        with zstandard.ZstdDecompressor().stream_reader(source) as reader:
            for i, line in enumerate(io.TextIOWrapper(reader, encoding="utf-8")):
                book = json.loads(line)
                assert book["id"] == i and book["payoutMultiplier"] == payouts[i]
                result = selection.replay_spec(manifest["books"][i])
                expected = [{"index": 0, "type": "roundResult", "data": asdict(result)}]
                canonical = json.dumps(expected, separators=(",", ":"), ensure_ascii=False)
                assert json.loads(canonical) == book["events"], f"Full event mismatch at {i}"
                # This oracle enumerates payable prefixes independently of the
                # game evaluator, then verifies gravity and whole-round credit.
                oracle.validate_round(result)
                assert result.payout_units == payouts[i]
                assert not any(s.cascade_limit_reached for s in (result.base, *result.free_spins))
                events_hashes.add(hashlib.sha256(canonical.encode()).digest())
                cap_books += result.payout_units == 500000
                bonus_books += bool(result.free_spins)
                if (i+1) % 20000 == 0:
                    print(f"Independently verified {i+1} exported complete rounds", flush=True)
    assert i+1 == len(payouts) == len(events_hashes)
    assert sum(w*p for w,p in zip([b-a for a,b in zip([0]+cdf[:-1],cdf)],payouts)) == 96*cdf[-1]
    report = {"status": "PASS", "exported_books_checked": i+1,
              "full_local_replay_matches_export": True, "unique_complete_events": len(events_hashes),
              "max_win_books_checked": cap_books, "bonus_books_checked": bonus_books,
              "independent_oracle": dict(oracle.COUNTS), "original_v02": original,
              "source_fingerprint": selection.source_fingerprint(),
              "lut_sha256": manifest["lut_sha256"], "elapsed_seconds": time.perf_counter()-start}
    (HERE / "book_mechanics_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
