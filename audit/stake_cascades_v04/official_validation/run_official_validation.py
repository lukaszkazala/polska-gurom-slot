"""Run unmodified official SDK functions, with separate exact local checks.

This runs public SDK code locally. It does not contact the private uploader and
does not confer platform approval. Downloaded SDK modules are never rewritten.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import redirect_stdout
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import importlib
import io
import json
from pathlib import Path
import sys
import time
import traceback
import warnings

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]
VENDOR = HERE / "vendor"
DEPENDENCIES = HERE.parent / "dependencies"
UINT64_MAX = (1 << 64) - 1
sys.dont_write_bytecode = True


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rational(value: Fraction) -> dict:
    with localcontext() as context:
        context.prec = 50
        decimal = Decimal(value.numerator) / Decimal(value.denominator)
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": str(decimal),
        "float": float(value),
    }


def json_default(value):
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_official():
    check(sys.flags.optimize == 0, "Official assertions require Python without -O")
    manifest = json.loads((HERE / "source_manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        path = HERE / entry["path"]
        check(path.is_file(), f"Missing official source: {path}")
        check(sha256(path) == entry["sha256"], f"Official source modified: {path}")
    if DEPENDENCIES.is_dir():
        sys.path.insert(0, str(DEPENDENCIES))
    sys.path.insert(0, str(VENDOR))
    sdk = importlib.import_module("utils.rgs_verification")
    check(Path(sdk.__file__).resolve() == VENDOR / "utils" / "rgs_verification.py",
          "Unexpected official module location")
    numpy = importlib.import_module("numpy")
    zstandard = importlib.import_module("zstandard")
    environment = {
        "python": sys.version,
        "executable": sys.executable,
        "numpy_version": numpy.__version__,
        "zstandard_version": zstandard.__version__,
        "dependency_directory": str(DEPENDENCIES),
        "official_module": str(Path(sdk.__file__).resolve()),
        "official_sources_verified_sha256": True,
        "official_code_modified_or_stubbed": False,
    }
    return sdk, zstandard, manifest, environment


def inspect_csv(path: Path, cost: Fraction, expected_rtp: Fraction,
                tolerance: Fraction, expected_cap: int, minimum_books: int,
                max_win_frequency_limit: int) -> tuple[list, dict]:
    rows = []
    weighted_sum = total_weight = positive_weight_count = positive_payout_count = 0
    nonzero_weight_payout_count = hit_weight = max_individual_weight = 0
    weight_by_payout = Counter()
    with path.open("r", encoding="utf-8") as source:
        for line_index, line in enumerate(source):
            fields = line.rstrip("\r\n").split(",")
            check(len(fields) == 3, f"CSV line {line_index}: expected three fields")
            check(all(field.isascii() and field.isdigit() for field in fields),
                  f"CSV line {line_index}: uint64 integer syntax required")
            sim_id, weight, payout = map(int, fields)
            check(all(value <= UINT64_MAX for value in (sim_id, weight, payout)),
                  f"CSV line {line_index}: uint64 overflow")
            check(sim_id == line_index, f"CSV line {line_index}: ID must match zero-based index")
            check(payout % 10 == 0, f"CSV line {line_index}: payout not in SDK increments of 10")
            check(payout <= expected_cap, f"CSV line {line_index}: payout exceeds declared round cap")
            rows.append((sim_id, weight, payout))
            total_weight += weight
            weighted_sum += weight * payout
            positive_weight_count += weight > 0
            positive_payout_count += payout > 0
            nonzero_weight_payout_count += weight > 0 and payout > 0
            hit_weight += weight if payout > 0 else 0
            max_individual_weight = max(max_individual_weight, weight)
            weight_by_payout[payout] += weight
    check(len(rows) >= minimum_books, f"Only {len(rows)} books; requested at least {minimum_books}")
    check(0 < total_weight <= UINT64_MAX, "Weight total must be positive and fit uint64")
    exact_rtp = Fraction(weighted_sum, 100 * total_weight) / cost
    max_weight = weight_by_payout[expected_cap]
    check(max_weight > 0, "Declared max win has no positive-weight outcome")
    max_frequency = Fraction(total_weight, max_weight)
    check(max_frequency < max_win_frequency_limit,
          f"Max win frequency is {float(max_frequency)}; expected stricter than 1:{max_win_frequency_limit}")
    check(Fraction(9, 10) <= exact_rtp <= Fraction(98, 100), "RTP outside 90-98% range")
    check(abs(exact_rtp - expected_rtp) <= tolerance, "RTP differs from the declared target")
    details = {
        "status": "PASS",
        "book_count": len(rows),
        "total_weight": total_weight,
        "weight_sum_uint64": True,
        "weights_within_float_exact_integer_range": total_weight <= 2**53,
        "weighted_payout_units_sum": weighted_sum,
        "rtp_fraction": rational(exact_rtp),
        "target_rtp_fraction": rational(expected_rtp),
        "rtp_target_absolute_tolerance": str(tolerance),
        "cost": rational(cost),
        "payout_scale": 100,
        "payout_step_units": 10,
        "min_payout_units": min(row[2] for row in rows),
        "max_payout_units": max(row[2] for row in rows),
        "declared_max_payout_units": expected_cap,
        "nonzero_weight_books": positive_weight_count,
        "zero_weight_books": len(rows) - positive_weight_count,
        "nonzero_payout_books": positive_payout_count,
        "positive_weight_and_positive_payout_books": nonzero_weight_payout_count,
        "unique_payouts": len(weight_by_payout),
        "positive_probability_payouts": sum(weight > 0 for weight in weight_by_payout.values()),
        "win_probability": rational(Fraction(hit_weight, total_weight)),
        "max_win_weight": max_weight,
        "max_win_probability": rational(Fraction(max_weight, total_weight)),
        "max_win_one_in": rational(max_frequency),
        "max_win_one_in_strict_upper_limit": max_win_frequency_limit,
        "dominant_single_book_probability": rational(Fraction(max_individual_weight, total_weight)),
    }
    return rows, details


def inspect_books(path: Path, rows: list, zstandard) -> dict:
    unique_events = set()
    weighted_unique_events = set()
    event_types = Counter()
    max_win_ids = []
    count = total_events = 0
    with path.open("rb") as source:
        with zstandard.ZstdDecompressor().stream_reader(source) as reader:
            for line_index, line in enumerate(io.TextIOWrapper(reader, encoding="utf-8")):
                check(bool(line.strip()), f"Blank book line {line_index}")
                book = json.loads(line)
                check(type(book) is dict, f"Book {line_index}: object required")
                check(type(book.get("id")) is int and book["id"] == line_index,
                      f"Book {line_index}: zero-based integer ID mismatch")
                check(line_index < len(rows), "More books than CSV rows")
                sim_id, weight, payout = rows[line_index]
                check(type(book.get("payoutMultiplier")) is int,
                      f"Book {line_index}: integer payout required")
                check(book["payoutMultiplier"] == payout, f"Book {line_index}: payout mismatch")
                events = book.get("events")
                check(type(events) is list and bool(events), f"Book {line_index}: non-empty event list required")
                check(all(type(event) is dict for event in events), f"Book {line_index}: event must be object")
                for event in events:
                    event_types[str(event.get("type", "<missing>"))] += 1
                total_events += len(events)
                event_fingerprint = hashlib.sha256(json.dumps(
                    events, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                ).encode("utf-8")).digest()
                unique_events.add(event_fingerprint)
                if weight:
                    weighted_unique_events.add(event_fingerprint)
                if payout == 500000 and weight:
                    max_win_ids.append(sim_id)
                count += 1
    check(count == len(rows), "Book count differs from CSV row count")
    return {
        "status": "PASS",
        "book_count": count,
        "total_event_count": total_events,
        "unique_canonical_event_sequences": len(unique_events),
        "positive_weight_unique_event_sequences": len(weighted_unique_events),
        "event_type_counts": dict(event_types),
        "positive_weight_max_win_ids": max_win_ids,
        "scope": "ID/type/count/payout/event-sequence-diversity checks; not a cascade pay evaluator",
    }


def validate(args) -> dict:
    started = time.perf_counter()
    report = {
        "status": "RUNNING",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform_approval": "NOT_PERFORMED; local execution of public SDK functions only",
        "runner": str(Path(__file__).resolve()),
        "runner_sha256": sha256(Path(__file__).resolve()),
        "publish_directory": str(args.publish_dir.resolve()),
        "warnings_are_not_silenced": True,
        "modes": [],
    }
    try:
        sdk, zstandard, provenance, environment = load_official()
        report["official_source"] = provenance
        report["environment"] = environment
        index = args.publish_dir / "index.json"
        if not index.is_file():
            raise FileNotFoundError(f"Pending generated export: {index}")
        manifest = json.loads(index.read_text(encoding="utf-8"))
        modes = manifest["modes"]
        check(type(modes) is list and bool(modes), "Manifest modes must be a non-empty list")
        check(len({mode["name"] for mode in modes}) == len(modes), "Duplicate mode names")
        report["index_sha256"] = sha256(index)
        exact_rtps = []
        for mode in modes:
            for key in ("name", "cost", "events", "weights"):
                check(key in mode, f"Missing manifest mode key: {key}")
            check(type(mode["cost"]) in (int, float) and mode["cost"] > 0,
                  "Mode cost must be a positive JSON number")
            cost = Fraction(Decimal(str(mode["cost"])))
            books_path = (args.publish_dir / mode["events"]).resolve()
            lut_path = (args.publish_dir / mode["weights"]).resolve()
            check(books_path.is_relative_to(args.publish_dir.resolve()), "Events path escapes publish directory")
            check(lut_path.is_relative_to(args.publish_dir.resolve()), "LUT path escapes publish directory")
            for path in (books_path, lut_path):
                if not path.is_file():
                    raise FileNotFoundError(f"Pending generated export: {path}")
            mode_report = {"name": mode["name"], "cost": mode["cost"], "official_functions": {}}
            report["modes"].append(mode_report)
            mode_report["files"] = {
                "books": {"path": str(books_path), "sha256": sha256(books_path), "bytes": books_path.stat().st_size},
                "weights": {"path": str(lut_path), "sha256": sha256(lut_path), "bytes": lut_path.stat().st_size},
            }
            function_results = mode_report["official_functions"]
            distribution, lut_payouts, weight_total, minimum, maximum = sdk.verify_lookup_format(str(lut_path))
            function_results["verify_lookup_format"] = "PASS"
            book_payouts, event_count = sdk.verify_books_and_payout_mults(str(books_path))
            function_results["verify_books_and_payout_mults"] = "PASS"
            sdk.compare_payout_values(book_payouts, lut_payouts)
            function_results["compare_payout_values"] = "PASS"
            output = io.StringIO()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                with redirect_stdout(output):
                    statistics = sdk.get_lut_statistics(
                        mode["name"], distribution, float(cost), lut_payouts,
                        weight_total, minimum, maximum, event_count,
                    )
            function_results["get_lut_statistics"] = "PASS"
            mode_report["official_warnings"] = [
                {"category": item.category.__name__, "message": str(item.message)} for item in caught
            ]
            mode_report["official_stdout"] = output.getvalue()
            mode_report["official_statistics_unrounded"] = {
                key: value for key, value in vars(statistics).items()
                if key not in ("win_distribution", "unique_wins")
            }
            rows, exact = inspect_csv(
                lut_path, cost, Fraction(Decimal(args.expected_rtp)),
                Fraction(Decimal(args.rtp_tolerance)), args.max_payout_units,
                args.minimum_books, args.max_win_frequency_limit,
            )
            mode_report["additional_exact_integer_checks"] = exact
            mode_report["additional_book_checks"] = inspect_books(books_path, rows, zstandard)
            exact_rtp = Fraction(exact["rtp_fraction"]["numerator"], exact["rtp_fraction"]["denominator"])
            check(abs(float(exact_rtp) - float(statistics.rtp)) <= 1e-10,
                  "Official floating RTP differs from exact integer RTP")
            exact_rtps.append(exact_rtp)
            mode_report["status"] = "PASS"
        check(max(exact_rtps) - min(exact_rtps) <= Fraction(5, 1000),
              "Mode RTP spread exceeds documentation 0.5 percentage points")
        report["mode_rtp_difference_requirement_fraction"] = "0.005"
        report["status"] = "PASS"
    except (ModuleNotFoundError, FileNotFoundError) as error:
        report["status"] = "BLOCKED"
        report["blocker"] = {"type": type(error).__name__, "message": str(error)}
    except Exception as error:
        report["status"] = "FAIL"
        report["error"] = {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
    report["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["elapsed_seconds"] = time.perf_counter() - started
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish-dir", type=Path, default=WORKSPACE / "test-interface" / "stake_math")
    parser.add_argument("--report", type=Path, default=HERE / "official_validation_report.json")
    parser.add_argument("--expected-rtp", default="0.96")
    parser.add_argument("--rtp-tolerance", default="0.000001")
    parser.add_argument("--max-payout-units", type=int, default=500000)
    parser.add_argument("--minimum-books", type=int, default=100000)
    parser.add_argument("--max-win-frequency-limit", type=int, default=10000000)
    args = parser.parse_args()
    report = validate(args)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=json_default) + "\n", encoding="utf-8")
    summary = {"status": report["status"], "report": str(args.report.resolve()),
               "elapsed_seconds": report["elapsed_seconds"]}
    for key in ("blocker", "error"):
        if key in report:
            summary[key] = {name: value for name, value in report[key].items() if name != "traceback"}
    print(json.dumps(summary, ensure_ascii=False))
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
