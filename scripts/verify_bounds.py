"""Exact max-win proof for one hash-pinned reconstruction, using the scalar core.

Run from any working directory. This is not a general-purpose max-win solver,
an SDK exporter, a simulation or a parameter-tuning program.
"""
from collections import Counter
from fractions import Fraction
from itertools import product
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from polska_gurom import __version__
from polska_gurom.bonus import ALLOWED_CHARGE_REELS
from polska_gurom.config import load_config
from polska_gurom.engine import assemble_round, evaluate_spin, round_to_dict
from polska_gurom.symbols import REGULAR, SCATTER, WILD

EXPECTED_CONFIG_HASH = "31c72aa957b4cc761c6e68864ba40e720a436c967c0c7700b1bf1fb385cf8d99"
EXPECTED_COUNTS = {
    "L1": 7, "L2": 5, "L3": 5, "L4": 4,
    "P1": 4, "P2": 3, "P3": 3, "P4": 2, WILD: 2, SCATTER: 1,
}


def require(condition, message):
    # Deliberately keep guards active even if Python is invoked with -O.
    if not condition:
        raise AssertionError(message)


def fraction_record(value):
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "fraction": str(value),
        "decimal_approximation": float(value),
    }


def main():
    cfg = load_config()
    require(cfg.config_hash == EXPECTED_CONFIG_HASH,
            "Proof applies only to EXPECTED_CONFIG_HASH; review the mathematics before changing it")
    require(cfg.scale == 100 and cfg.cap_units == 500000, "Unexpected scale or cap")
    require(len(cfg.reels) == 5 and all(len(reel) == 36 for reel in cfg.reels),
            "Proof requires five strips of length 36")
    expected_strip = tuple(symbol for symbol, count in EXPECTED_COUNTS.items() for _ in range(count))
    require(all(reel == expected_strip for reel in cfg.reels), "Grouped strip order differs")
    require(all(Counter(reel) == EXPECTED_COUNTS for reel in cfg.reels), "Symbol counts differ")
    require(len(cfg.paylines) == len(set(cfg.paylines)) == 20, "Twenty distinct lines required")
    require(all((row,) * 5 in cfg.paylines for row in range(3)),
            "The proof needs all three horizontal lines")
    require(set(cfg.paytable) == set(REGULAR) and WILD not in cfg.paytable,
            "Only eight regular symbols may pay; no Wild-only paytable")
    max_line = max(amount for table in cfg.paytable.values() for amount in table.values())
    max_three = max(table[3] for table in cfg.paytable.values())
    max_scatter = max(cfg.scatter_pays.values())
    require(max_line == 5000 and cfg.paytable["P4"][5] == 5000,
            "Maximum line payout must be exactly 50 TOTAL BET")
    require(max_three == cfg.paytable["P4"][3] == 200,
            "Any prefix of at most three matches must pay at most 2 TOTAL BET")
    require(all(table[3] <= table[4] <= table[5] for table in cfg.paytable.values()),
            "Nondecreasing paytable required")
    require(cfg.scatter_pays == {3: 100, 4: 500, 5: 2000} and max_scatter == 2000,
            "Unexpected Scatter payouts")
    require(cfg.fs_awards == {3: 8, 4: 10, 5: 12}, "Unexpected Free Spin awards")
    require(cfg.charge_probability == Fraction(1, 4) and cfg.charge_weights == (1, 1, 1),
            "Witness probability is pinned to Charge 25%, uniformly over reels 2/3/4")
    require(ALLOWED_CHARGE_REELS == (1, 2, 3), "Unexpected set of allowed Charge reels")

    scatter_stops = []
    for reel in cfg.reels:
        window_counts = [sum(reel[(stop + row) % len(reel)] == SCATTER for row in range(3))
                         for stop in range(len(reel))]
        require(max(window_counts) == 1, "At most one visible Scatter per reel required")
        options = tuple(stop for stop, count in enumerate(window_counts) if count == 1)
        require(options == (33, 34, 35), "Unexpected stops exposing Scatter")
        scatter_stops.append(options)

    # A Free Spin with <3 natural Scatters has no Scatter payout: <=20*50.
    # For >=3 natural Scatters, one Charge covers at most one Scatter-bearing
    # reel, leaving >=2 exposed Scatters. At least one is on reel 1..4.
    # The horizontal line through that cell matches at most three prefix
    # symbols and pays <=2. Thus the spin is <=19*50+2+20=972 <1000.
    no_scatter_pay_upper = len(cfg.paylines) * max_line
    positive_scatter_pay_upper = (len(cfg.paylines) - 1) * max_line + max_three + max_scatter
    require(positive_scatter_pay_upper == 97200 < no_scatter_pay_upper == 100000,
            "Free Spin bound assumptions no longer imply 1000 TOTAL BET")
    fs_upper = no_scatter_pay_upper

    free_witness = evaluate_spin(cfg, (31,) * 5, is_free=True, charge_reel=None)
    require(free_witness.total_units == fs_upper, "Witness must attain the Free Spin upper bound")
    require(free_witness.scatter_count == 0 and free_witness.awarded_free_spins == 0,
            "Witness must not retrigger or pay Scatters")
    require(len(free_witness.line_wins) == 20 and
            all(win.payout_units == max_line for win in free_witness.line_wins),
            "All twenty witness lines must pay 50 TOTAL BET")
    require(evaluate_spin(cfg, (33,) * 5, is_free=True).awarded_free_spins == 0,
            "No retriggers are allowed, including on five Scatters")

    # Five visible Scatters require one of three stops on every reel.
    # Enumerate every one of these 3**5=243 boards with the actual evaluator.
    enumerated = 0
    max_base = -1
    maximizing_stops = []
    for stops in product(*scatter_stops):
        base = evaluate_spin(cfg, stops)
        require(base.scatter_count == 5 and base.awarded_free_spins == 12,
                "Five-Scatter enumeration did not yield twelve Free Spins")
        enumerated += 1
        if base.total_units > max_base:
            max_base, maximizing_stops = base.total_units, [stops]
        elif base.total_units == max_base:
            maximizing_stops.append(stops)
    require(enumerated == 243 and max_base == 32400 and maximizing_stops == [(33,) * 5],
            "Five-Scatter maximum changed; this proof must be reviewed")

    crude_base_upper = len(cfg.paylines) * max_line + max_scatter
    round_bounds = {
        "0_1_2_scatters": fs_upper,
        "3_scatters": crude_base_upper + cfg.fs_awards[3] * fs_upper,
        "4_scatters": crude_base_upper + cfg.fs_awards[4] * fs_upper,
        "5_scatters": max_base + cfg.fs_awards[5] * fs_upper,
    }
    raw_upper = max(round_bounds.values())
    require(raw_upper == 1232400 and round_bounds["5_scatters"] == raw_upper,
            "Five-Scatter witness must dominate the other round bounds")
    base_witness = evaluate_spin(cfg, (33,) * 5)
    result = assemble_round(cfg, base_witness, [free_witness] * base_witness.awarded_free_spins)
    require(result.raw_total_units == raw_upper, "Complete witness must attain the raw upper bound")
    require(result.paid_total_units == cfg.cap_units and result.cap_reached,
            "Complete witness must attain the paid cap")
    require(result.cap_reduction_units == raw_upper - cfg.cap_units == 732400,
            "Incorrect cap reduction")
    require(result.paid_base_units + result.paid_bonus_units == result.paid_total_units,
            "Paid components must sum to the paid round")

    # Stops are uniform and independent, as are the twelve Free Spin charges.
    one_exact_board_probability = Fraction(1, 36 ** 5)
    path_probability = (one_exact_board_probability *
                        (one_exact_board_probability * (1 - cfg.charge_probability)) ** 12)
    require(path_probability > 0, "Witness must have positive natural probability")
    core_names = ("config.py", "evaluator.py", "engine.py", "bonus.py", "cap.py", "scatter.py", "reels.py")
    source_hashes = {f"polska_gurom/{name}": hashlib.sha256((ROOT / "polska_gurom" / name).read_bytes()).hexdigest()
                     for name in core_names}
    metadata = {
        "engine_version": __version__, "config_version": cfg.version,
        "config_hash": cfg.config_hash, "status": "PROTOTYPE / NOT MATH-FROZEN",
    }
    witness = {
        **metadata, "kind": "positive-probability-exact-raw-maximum-witness",
        "seed": None, "probability": fraction_record(path_probability),
        "probability_note": "Dokladna sciezka, nie suma prawdopodobienstw wszystkich osiagniec maksimum.",
        "round": round_to_dict(result),
    }
    proof = {
        **metadata, "result_status": "EXACT", "units": "100 units = 1 TOTAL BET",
        "method": "Analityczne ograniczenie wszystkich FS oraz pelna enumeracja 243 plansz base z 5 Scatterami, z rzeczywistym core.",
        "specific_configuration_only": True,
        "source_sha256": source_hashes,
        "assumptions_checked": {
            "identical_grouped_36_symbol_strips": True,
            "twenty_unique_lines_including_three_horizontals": True,
            "one_visible_scatter_per_reel_at_most": True,
            "line_maximum_units": max_line,
            "three_match_maximum_units": max_three,
            "scatter_maximum_units": max_scatter,
            "charge_probability": str(cfg.charge_probability),
            "charge_weights": list(cfg.charge_weights),
            "allowed_charge_reels_zero_based": [1, 2, 3],
            "charge_covers_at_most_one_reel": True,
            "free_spin_retriggers": False,
            "all_awarded_spins_played_after_cap": True,
        },
        "free_spin_upper_units": fs_upper,
        "free_spin_upper_with_positive_scatter_pay_units": positive_scatter_pay_upper,
        "free_spin_bound_argument": "Przy >=3 naturalnych SC po co najwyzej jednym Charge pozostaja >=2 odkryte SC; przynajmniej jeden na bebnie 1-4. Pozioma linia przez niego placi <=2x. Pozostale 19 linii <=50x kazda, Scatter payout <=20x; suma <=972x. Przy <3SC suma <=1000x. Stops31/noCharge osiaga1000x.",
        "five_scatter_boards_enumerated": enumerated,
        "five_scatter_base_maximum_units": max_base,
        "five_scatter_maximizing_stops": maximizing_stops,
        "round_upper_bounds_units": round_bounds,
        "raw_round_maximum_units": raw_upper,
        "raw_round_maximum_total_bet": raw_upper // cfg.scale,
        "paid_round_maximum_units": cfg.cap_units,
        "paid_round_maximum_total_bet": cfg.cap_units // cfg.scale,
        "maximum_cap_reduction_units": result.cap_reduction_units,
        "witness_probability": fraction_record(path_probability),
        "witness_path": "reports/max_win_witness.json",
        "probability_scope": "Jedna konkretna sciezka; nie obliczono tutaj dokladnej czestosci cap.",
        "bounds_scope": "Nie obliczono tutaj dokladnego RTP po cap ani optymalizacji; oddzielny modul analityczny raportuje ich ograniczenia.",
    }
    paths = [(ROOT / "reports/results/max_win_proof.json", proof),
             (ROOT / "reports/max_win_witness.json", witness)]
    for path, data in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result_status": "EXACT", "config_hash": cfg.config_hash,
                      "five_scatter_boards_enumerated": enumerated,
                      "raw_maximum_total_bet": raw_upper // cfg.scale,
                      "paid_maximum_total_bet": cfg.cap_units // cfg.scale,
                      "cap_reduction_total_bet": result.cap_reduction_units // cfg.scale,
                      "witness_probability_approximation": float(path_probability)}, indent=2))


if __name__ == "__main__":
    main()
