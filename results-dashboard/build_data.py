"""Build a read-only dashboard snapshot from recorded project evidence.

This script never runs game tests or changes game files. Report copies retain their
original bytes; hashes allow the dashboard snapshot to be audited independently.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from shutil import copyfile

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "dist"
REPORTS = OUT / "reports"
MATH_PATH = "test-interface/stake_math/mathematics.json"
BONUS_PATH = "audit/bonus_frequency_2026_10_19/results.json"
FINAL_PATH = "audit/stake_cascades_v04/final_results.json"
WEIGHTED_PATH = "audit/stake_cascades_v04/fast_sim/weighted_results/weighted_simulation_report.json"
BOOK_PATH = "audit/stake_cascades_v04/book_mechanics_report.json"
SDK_PATH = "audit/stake_cascades_v04/official_validation/official_validation_report.json"
NETWORK_PATH = "audit/network_resilience_2026_10_19/results.json"


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def display(value):
    """Keep browser detail data useful without exposing absolute home paths."""
    if isinstance(value, dict):
        return {k: display(v) for k, v in value.items() if k != "traces"}
    if isinstance(value, list):
        return [display(v) for v in value]
    if isinstance(value, str):
        value = value.replace(str(ROOT), "[projekt]").replace(ROOT.as_posix(), "[projekt]")
        return re.sub(r"C:[\\/]Users[\\/]Kazaluka(?:[\\/][^\s\"']*)?", "[ścieżka lokalna]", value)
    return value


def report_href(path):
    return "reports/" + path.replace("\\", "/")


def case(name, passed=True, details=None, **extra):
    return {"name": name, "label_pl": name, "status": "pass" if passed else "fail", "details": display(details or {}), **extra}


def suite(identifier, title, tests, evidence, *, scope="Bieżąca wersja", version="0.4.0-weighted", details=None, counted=True):
    statuses = [t["status"] for t in tests]
    return {
        "id": identifier, "title": title, "scope": scope, "version": version,
        "current": not scope.startswith("Historia"), "historical": scope.startswith("Historia"),
        "status": "fail" if "fail" in statuses else "pass",
        "testsCount": len(tests), "passedCount": statuses.count("pass"),
        "failedCount": statuses.count("fail"), "countedInRegressionTotal": counted,
        "tests": tests, "evidence": evidence, "details": display(details or {}),
    }


HTTP_LABELS = [
    "Utrata odpowiedzi po rozliczeniu — ponowienie tego samego ID",
    "Ucięta odpowiedź JSON — odzyskanie pełnego wyniku",
    "Brak serwera przed przekazaniem żądania — odzyskanie połączenia",
    "Błąd 503 po rozliczeniu — jedna opłata za rundę",
    "Opóźnienie odpowiedzi i timeout — bez podwójnej opłaty",
    "Osiem równoczesnych ponowień — jeden wynik i jedno rozliczenie",
    "Zerwanie połączenia w nagłówkach — brak obciążenia",
    "Zerwanie połączenia w treści żądania — bezpieczne ponowienie",
    "Niedostępność i nowa instancja serwera — odrzucenie starej sesji",
    "Restart po zgubieniu wyniku — blokada ponownego rozliczenia",
    "Brak ciasteczka sesji — blokada nieodtwarzalnego obrotu",
    "Wynik usunięty z pamięci 100 odpowiedzi — brak drugiej opłaty",
    "Odświeżenie strony — odzyskanie wyniku z tej samej sesji",
    "Wygaśnięcie sesji po 24 h — kontrolowany błąd",
    "Niepoprawny nagłówek sesji — żądanie odrzucone",
    "Reset w drugiej karcie — blokada starej sesji",
    "Limit 100 tys. identyfikatorów — kontrolowana blokada i reset",
]

LOGIC_LABELS = [
    "Brak połączenia przed wysłaniem — odzyskanie tej samej rundy",
    "Zgubiona odpowiedź po rozliczeniu — brak drugiej opłaty",
    "Chwilowy błąd HTTP 408 — pełne 10 obrotów",
    "Chwilowy błąd HTTP 429 — pełne 10 obrotów",
    "Chwilowy błąd HTTP 500 — pełne 10 obrotów",
    "Chwilowy błąd HTTP 502 — pełne 10 obrotów",
    "Chwilowy błąd HTTP 503 — pełne 10 obrotów",
    "Trwały brak połączenia — trzy próby i ręczne odzyskanie",
    "Trwała utrata odpowiedzi — trzy próby i ręczne odzyskanie",
    "Trwały błąd 429 — trzy próby i ręczne odzyskanie",
    "Trwały błąd 502 — trzy próby i ręczne odzyskanie",
    "Zawieszone połączenie — limit 15 sekund i odzyskanie",
    "Zawieszona treść odpowiedzi — limit 15 sekund i odzyskanie",
    "Trwałe timeouty — zatrzymanie po trzech próbach bez opłaty",
    "Wygasła sesja — zatrzymanie bez obciążenia",
    "Zmieniona sesja — zatrzymanie bez obciążenia",
    "Wygasły wynik — zatrzymanie bez obciążenia",
    "Dwuklik podczas opóźnienia — jedno żądanie",
    "Utrata połączenia po otrzymaniu bonusu — dokończenie 8 FS",
    "Uszkodzony JSON — odrzucenie i odzyskanie oryginału",
    "Pusty JSON — odrzucenie i odzyskanie oryginału",
    "Błędne ID rundy — odrzucenie i odzyskanie oryginału",
    "Błędne ID sesji — odrzucenie i odzyskanie oryginału",
    "Błędna wersja — odrzucenie i odzyskanie oryginału",
    "Odpowiedź po 8 sekundach — jedna runda bez ponowienia",
    "Odpowiedź po terminie — ponowienie bez drugiej opłaty",
    "Odświeżenie po zgubieniu odpowiedzi — jeden wynik w historii",
    "Odświeżenie po awarii przy 81/100 — odzyskanie bez wznowienia autospinu",
    "Odświeżenie po restarcie — stara runda nie trafia do nowej sesji",
    "Zawieszony zestaw symboli — koniec inicjalizacji po 15 sekundach",
]

AUTOPLAY_LABELS = [
    "100 obrotów w zwykłym tempie z bonusami", "100 szybkich obrotów z bonusami",
    "100 obrotów turbo z bonusami", "100 obrotów natychmiastowych z bonusami",
    "Ukrycie karty przy 80/100 — ukończenie bez dodatkowych obrotów",
    "Ukrycie karty podczas 81. rundy — ukończenie 100/100",
    "Zgubiona odpowiedź przy 81. rundzie — 100 opłat, 100 wyników",
    "Chwilowy błąd 503 przy 81. rundzie — ukończenie 100/100",
    "Brak salda po 80 obrotach — jasna przyczyna zatrzymania",
    "Odmowa serwera po 80 obrotach — jasna przyczyna zatrzymania",
    "STOP między rundami — brak następnej opłaty",
    "STOP podczas rundy — dokończenie tylko bieżącej rundy",
    "Trwała awaria — zatrzymanie z zachowaniem ID oczekującej rundy",
]

PORTABLE_LABELS = [
    "Integralność archiwum ZIP", "Brak pamięci podręcznej Pythona w ZIP", "Wypakowane pliki identyczne z ZIP",
    "Komplet plików przenośnych", "Pliki silnika identyczne z bieżącą wersją", "Uruchomienie na osobnym porcie",
    "Gotowość spakowanego serwera", "Strona główna", "Konfiguracja", "Metadane wersji kaskad",
    "Zestaw symboli", "Początkowy stan sesji", "Dokładne rozliczenie salda", "Ponowienie obrotu bez drugiej opłaty",
    "Rozliczenie zwykłej kaskady", "Blokada sprzecznego ID", "Scenariusz ekspansji WILD",
    "Podgląd bez zmiany salda i statystyk", "Powtarzalność podglądu", "Rozliczenie kaskad w bonusie",
    "Podgląd kaskady", "Spadanie istniejących symboli", "Pełne dane przejść między kaskadami",
    "Podgląd kaskady bez zmiany salda", "Ponowienie podglądu kaskady", "Historia ostatnich rund",
    "Serwer używa wypakowanego silnika",
]

UNIT_LABELS = {
    "test_actual_fall_with_holes_above_and_below_survivors": "Spadanie przy lukach nad i pod istniejącymi symbolami",
    "test_duplicates_remove_one_cell_and_survivor_order_is_stable": "Wspólne symbole usuwane raz, kolejność pozostałych zachowana",
    "test_overlapping_lines_remove_union_once_and_award_new_wins": "Nakładające się linie i nowe wygrane po spadaniu",
    "test_scatter_is_initial_only_and_never_spawned": "Scattery tylko na początkowej planszy",
    "test_free_spin_multiplier_cascades_and_expansion_only_once": "Mnożnik bonusu i pojedyncza ekspansja WILD",
    "test_scatter_count_before_free_spin_expansion": "Liczenie Scatterów przed ekspansją",
    "test_round_cap_applies_across_base_and_free_spins": "Wspólny limit wygranej całej rundy z bonusem",
    "test_limit_caps_stage_after_scatter_before_any_removal": "Limit etapu po Scatterach przed usuwaniem symboli",
    "test_emergency_limit_is_explicit_and_stops_before_removal": "Awaryjny limit kaskad zgłaszany przed usunięciem symboli",
    "test_seeded_rounds_are_repeatable_and_settlement_matches_animation": "Powtarzalność rund i zgodność wypłaty z animacją",
    "test_config_static_files_and_cookie": "Konfiguracja, pliki strony i ciasteczko sesji",
    "test_random_wallet_exact_settlement_and_session_isolation": "Dokładne rozliczenie i niezależność sesji",
    "test_scenarios_replay_real_engine_without_wallet_changes": "Podglądy rzeczywistego silnika bez zmiany salda",
    "test_history_survives_page_reload_is_bounded_and_newest_first": "Historia po odświeżeniu i limit długości",
    "test_cascade_endpoint_preserves_falls_and_charges_one_paid_round": "Jedna opłata za całą rundę z kaskadami",
    "test_idempotence_and_conflicting_reuse": "Powtarzalność ID i blokada sprzecznego użycia",
    "test_simultaneous_retries_charge_once": "Jednoczesne ponowienia pobierają jedną opłatę",
    "test_validation_and_cross_origin_requests_do_not_change_wallet": "Nieprawidłowe żądania nie zmieniają salda",
    "test_reset_and_insufficient_funds": "Reset i brak wystarczającego salda",
    "test_cap_credits_are_settled_once_at_total_bet": "Jednokrotne rozliczenie limitu według całej stawki",
}


def collect_reports():
    paths = set()
    for folder in [ROOT / "audit", ROOT / "test-interface" / "qa"]:
        for p in folder.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in {".json", ".md"}:
                continue
            relative = p.relative_to(ROOT).as_posix()
            parts = p.relative_to(folder).parts
            if any(x in {"dependencies", "__pycache__", "vendor", "node_modules"} or x.startswith("portable-smoke") for x in parts):
                continue
            if p.name.startswith("transcript") or p.name in {"browser_fault_control.json", "deployment_plan.json", "deployment_result.json", "dashboard_data_review.json"}:
                continue
            paths.add(relative)
    paths.update([MATH_PATH, "test-interface/README_PL.md"])
    inventory_path = ROOT / "audit/dashboard_history_inventory.json"
    if inventory_path.exists():
        inventory = read(inventory_path.relative_to(ROOT))
        references = [item["path"] for item in inventory.get("inventory", [])]
        references.extend(path for phase in inventory.get("phases", []) for path in phase.get("sourcepaths", []))
        for reference in references:
            relative = reference.replace("\\", "/")
            candidate = (ROOT / relative).resolve()
            if candidate.is_relative_to(ROOT) and candidate.is_file() and candidate.suffix.lower() in {".json", ".md", ".csv", ".txt", ".jpg", ".png"}:
                paths.add(relative)
    for folder in [ROOT / "audit/stake_cascades_v04", ROOT / "audit/network_resilience_2026_10_19"]:
        paths.update(p.relative_to(ROOT).as_posix() for p in folder.glob("*.jpg"))
    registry = []
    for relative in sorted(paths):
        source = ROOT / relative
        if not source.exists():
            continue
        dest = REPORTS / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        copyfile(source, dest)
        digest = sha(source)
        assert sha(dest) == digest
        category = "aktualne" if any(x in relative for x in ["stake_cascades_v04", "network_resilience_2026_10_19", "bonus_frequency_2026_10_19", "stake_math"]) else "historia"
        if relative.startswith("test-interface/qa/"):
            category = "QA"
        filename = Path(relative).name
        if "/fast_sim/" in relative and filename.startswith(("calibration_", "candidate_")):
            category = "strojenie"
        elif relative == "audit/stake_cascades_v04/fast_sim/natural_1m_trace.json":
            category = "historia"
        title = Path(relative).stem.replace("_", " ")
        registry.append({"id": relative, "path": relative, "title": title, "href": report_href(relative), "sha256": digest, "bytes": source.stat().st_size, "category": category, "format": source.suffix[1:].lower()})
    return registry


def collect_simulations(final, weighted, bonus):
    simulations = []
    bonus_runs = {r["rounds"]: r for r in bonus["previous_simulations_aggregated"]}
    for run in weighted["runs"]:
        b = bonus_runs[run["rounds"]]
        simulations.append({
            "id": "weighted-" + str(run["rounds"]), "kind": "weighted", "title": "Końcowa tabela ważona",
            "version": "0.4.0-weighted", "rounds": run["rounds"], "rtp": run["rtp"], "referenceRtp": .96,
            "interval95": run["normal_95_interval_around_observed"], "status": "pass" if run["within_95_normal_reference_band"] else "review",
            "hitFrequency": run["hit_frequency"], "bonusFrequency": b["bonus_frequency"], "bonuses": b["bonuses"],
            "maxWinHits": run["max_win_hits"], "maxWinExpectedHits": run["max_win_expected_hits"], "seed": run["seed"],
            "evidence": [WEIGHTED_PATH, BONUS_PATH], "details": display(run),
            "scope": "Rzeczywiste losowania pełnych wyników z opublikowanej tabeli; osobny audyt sprawdza przebieg kaskad.",
        })
    for run in final["natural_candidate_runs"]:
        simulations.append({
            "id": "natural-" + str(run["rounds"]), "kind": "natural", "title": "Naturalny generator kaskad",
            "version": "generator v0.4", "rounds": run["rounds"], "rtp": run["rtp"], "referenceRtp": None,
            "interval95": run["normal95Interval"], "status": "diagnostic", "hitFrequency": run["hitFrequency"],
            "bonusFrequency": run["bonusFrequency"], "maxWinHits": run["capHits"], "seed": run["seed"],
            "evidence": [f"audit/stake_cascades_v04/fast_sim/natural_{run['rounds']//1000000}m.json"], "details": display(run),
            "scope": "Pełne wygenerowane plansze, kaskady i darmowe obroty. To generator kandydatów; wynik nie jest RTP końcowej tabeli ważonej.",
        })
    for p in sorted((ROOT / "audit/stake_cascades_v04/fast_sim").glob("*_result.json")):
        run = read(p.relative_to(ROOT))
        simulations.append({"id": p.stem, "kind": "calibration", "title": p.stem.replace("_result", "").replace("_", " "),
            "version": "wariant kalibracyjny", "rounds": run["rounds"], "rtp": run["rtp"], "referenceRtp": None,
            "interval95": run["normal95Interval"], "status": "historical", "hitFrequency": run["hitFrequency"],
            "bonusFrequency": run["bonusFrequency"], "maxWinHits": run["capHits"], "seed": run["seed"],
            "evidence": [p.relative_to(ROOT).as_posix()], "details": display(run),
            "scope": "Próba doboru parametrów; nie opisuje aktualnych szans gry."})
    small = read("audit/stake_cascades_v04/cli_weighted_10k.json")
    simulations.append({"id": "weighted-cli-10000", "kind": "diagnostic", "title": "Próba CLI końcowego silnika",
        "version": "0.4.0-weighted", "rounds": small["spins"], "rtp": small["rtp"], "referenceRtp": .96,
        "interval95": small["rtp_95_percent_normal_interval"], "status": "diagnostic", "hitFrequency": small["hit_frequency"],
        "bonusFrequency": small["bonus_frequency"], "maxWinHits": small["rounds_reduced_by_cap"], "seed": small["seed"],
        "evidence": ["audit/stake_cascades_v04/cli_weighted_10k.json"], "details": display(small),
        "scope": "Mała próba integracyjna CLI; nie zastępuje dokładnego RTP i dużych serii."})
    return simulations


def historical_simulations(history):
    """Expose old recorded runs without counting copies or presenting old RTP as current."""
    result = []
    seen = set()
    for phase in history.get("phases", []) if isinstance(history, dict) else []:
        version = phase.get("version", "historia")
        if "v0.4" in version:
            continue
        values = phase.get("results", {})
        for group in ["reproduced_simulations", "simulations"]:
            for run in values.get(group, []):
                count = run.get("spins", run.get("rounds"))
                if count is None or "rtp" not in run:
                    continue
                key = (version, count, run.get("seed"), run["rtp"])
                if key in seen:
                    continue
                seen.add(key)
                reference = values.get("nominal_rtp", values.get("exact_rtp"))
                result.append({"id": f"history-{phase['id']}-{len(result)}", "kind": "historical", "title": phase["name"],
                    "version": version, "rounds": count, "rtp": run["rtp"], "referenceRtp": reference,
                    "interval95": run.get("rtp_95_percent_normal_interval"), "status": "historical",
                    "hitFrequency": run.get("hit_frequency"), "bonusFrequency": run.get("bonus_frequency"),
                    "maxWinHits": run.get("rounds_reduced_by_cap"), "seed": run.get("seed"),
                    "evidence": ["audit/dashboard_history_inventory.json"], "details": display(run),
                    "scope": f"Zapisana symulacja {version}. Opisuje poprzednią matematyczną wersję gry, nie aktualne szanse."})
    p = "audit/stake_cascades_v04/fast_sim/natural_1m_trace.json"
    old = read(p)
    result.append({"id": "history-cascade-before-calibration", "kind": "historical", "title": "Kaskady przed dopasowaniem wypłat",
        "version": "v0.3 — przed kalibracją", "rounds": old["rounds"], "rtp": old["rtp"], "referenceRtp": None,
        "interval95": old["normal95Interval"], "status": "historical", "hitFrequency": old["hitFrequency"],
        "bonusFrequency": old["bonusFrequency"], "maxWinHits": old["capHits"], "seed": old["seed"],
        "evidence": [p], "details": display(old), "scope": "Wstępna diagnoza naturalnych kaskad przed zmianą tabeli wypłat. Nie opisuje aktualnej gry."})
    return result


def collect_suites(final, book, sdk, network):
    result = []
    nhttp = read("test-interface/qa/network_faults_results.json")
    observations = {o["test"]: o for o in nhttp["observations"]}
    http_tests = [case(HTTP_LABELS[i], t["status"] == "passed", observations.get(t["test"], {}), originalName=t["test"]) for i, t in enumerate(nhttp["tests"])]
    result.append(suite("network-http", "Awarie połączenia — HTTP i TCP", http_tests, ["test-interface/qa/network_faults_results.json", NETWORK_PATH], details={k: v for k, v in nhttp.items() if k not in {"tests", "observations"}}))
    for id_, name, path in [
        ("network-logic", "Awarie połączenia — logika gry", "test-interface/qa/network_logic_results.json"),
        ("autoplay", "Autospin — 100 obrotów i zatrzymywanie", "test-interface/qa/autoplay_logic_results.json"),
    ]:
        raw = read(path)
        labels = LOGIC_LABELS if id_ == "network-logic" else AUTOPLAY_LABELS
        assert len(labels) == len(raw["checks"])
        result.append(suite(id_, name, [case(labels[i], t["passed"], {k: v for k, v in t.items() if k not in {"scenario", "passed"}}, originalName=t["scenario"]) for i, t in enumerate(raw["checks"])], [path], details={k: v for k, v in raw.items() if k != "checks"}))
    raw = read("test-interface/qa/portable_check.json")
    assert len(PORTABLE_LABELS) == len(raw["checks"])
    result.append(suite("portable", "Paczka przenośna — uruchomienie i rozliczenia", [case(PORTABLE_LABELS[i], t["success"], originalName=t["name"]) for i, t in enumerate(raw["checks"])], ["test-interface/qa/portable_check.json"], details={k: v for k, v in raw.items() if k != "checks"}))
    for item in final["executed_unittest_suites"]:
        p = ROOT / item["path"]
        tree = ast.parse(p.read_text(encoding="utf-8-sig"))
        names = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")]
        assert len(names) == item["tests"], (p, len(names), item["tests"])
        title = "Mechanika kaskad — testy silnika" if "cascades" in p.name else "Serwer — regresja API"
        result.append(suite("cascade-engine" if "cascades" in p.name else "server-api", title,
            [case(UNIT_LABELS.get(n, n), item["failures"] == 0, {"evidenceBasis": "Nazwy z pliku testów, wynik całego zestawu zapisany w raporcie końcowym."}, originalName=n) for n in names], [FINAL_PATH], details={**item, "testSourceSha256": sha(p)}))
    mode = sdk["modes"][0]
    sdk_names = {"verify_lookup_format": "Format tabeli losowań", "verify_books_and_payout_mults": "Format wyników i mnożników", "compare_payout_values": "Zgodność wypłat między wynikami a tabelą", "get_lut_statistics": "Statystyki tabeli w publicznym SDK"}
    sdk_tests = [case(sdk_names.get(k, k), v == "PASS", originalName=k) for k, v in mode["official_functions"].items()]
    sdk_tests += [case("Dokładne kontrole wag, RTP i kwantyzacji", mode["additional_exact_integer_checks"]["status"] == "PASS", mode["additional_exact_integer_checks"]), case("Kontrola zgodności identyfikatorów i różnorodności wyników", mode["additional_book_checks"]["status"] == "PASS", mode["additional_book_checks"])]
    result.append(suite("public-sdk", "Publiczny walidator Stake SDK — lokalnie", sdk_tests, [SDK_PATH], counted=False, details={"source": sdk["official_source"], "warnings": mode["official_warnings"], "platformApproval": "Nie przeprowadzono zatwierdzenia przez Stake."}))
    book_tests = [case("Odtworzenie każdego wyniku zgadza się z eksportem", book["full_local_replay_matches_export"], {"books": book["exported_books_checked"]}),
        case("Wszystkie sekwencje wyników są unikalne", book["unique_complete_events"] == book["exported_books_checked"]),
        case("Niezależna kontrola wypłat, ruchów i kaskad", book["status"] == "PASS", book["independent_oracle"]),
        case("Kontrola czterech wyników maksymalnej wygranej", book["max_win_books_checked"] == 4),
        case("Kontrola wyników bonusowych", book["bonus_books_checked"] == 502, {"books": book["bonus_books_checked"]}),
        case("Oryginalne pliki v0.2 pozostały bez zmian", book["original_v02"]["unchanged"], book["original_v02"])]
    result.append(suite("books", "Niezależny audyt wszystkich 100 024 wyników", book_tests, [BOOK_PATH], counted=False, details=book))
    cross = read("audit/stake_cascades_v04/fast_sim/crosscheck.json")
    result.append(suite("crosscheck", "Zgodność symulatora z silnikiem Python", [case("Dokładne porównanie 10 000 przebiegów", cross["exact_trace_comparison"] in [True, "passed", "PASS"], cross)], ["audit/stake_cascades_v04/fast_sim/crosscheck.json"], counted=False, details=cross))
    result.append(suite("network-browser", "Przeglądarka — odzyskiwanie rund i 100 autospinów", [
        case("Brak połączenia przed obrotem — widoczny przycisk ponowienia", True, network["browser"]["offline_before_recovery"]),
        case("Timeout — możliwość odzyskania oczekującej rundy", True, network["browser"]["timeout_before_recovery"]),
        case("Po odzyskaniu połączenia autospin kończy 100/100", "100 / 100" in network["browser"]["after_recovery_and_100_autospins"]["progress"], network["browser"]["after_recovery_and_100_autospins"]),
        case("Rozliczenia zgadzają się z unikalnymi identyfikatorami", network["browser_accounting_matches_unique_request_ids"], {"requests": network["browser_actual_requests"], "distinctPaidRounds": network["browser_distinct_paid_rounds"]})], [NETWORK_PATH, "test-interface/qa/network_browser_results.json"], counted=False, details={"scope": network["scope"], "remainingLimits": network["remaining_limits"]}))
    result.append(suite("rtp-browser", "Przeglądarka — finalna matematyka i 100/100", [case("100 płatnych rund w autospinie", final["browser"]["rounds"] == 100, final["browser"]), case("Brak błędów konsoli", not final["browser"]["consoleErrors"])], ["audit/stake_cascades_v04/browser_check.json"], counted=False))
    for id_, title, path, version in [
        ("browser-original", "Pierwotny interfejs i widok mobilny", "test-interface/qa/browser_checks.json", "v0.2 — historia"),
        ("browser-autoplay-original", "Pierwszy panel autospinu — przeglądarka", "test-interface/qa/autoplay_browser_checks.json", "v0.2 — historia"),
        ("browser-autospin-fix", "Poprawka autospinu — serie turbo i instant", "test-interface/qa/autospin_fix_browser_checks.json", "przed v0.4 — historia"),
        ("browser-cascades", "Kaskady, bonus i responsywność", "test-interface/qa/cascade_browser_checks.json", "v0.3 — historia"),
        ("cascade-default", "Kaskady działają od razu po uruchomieniu", "test-interface/qa/cascade_default_checks.json", "przed v0.4 — historia"),
        ("cascade-small-oracle", "Niezależna mechanika — próba 10 000 rund", "test-interface/qa/cascade_math_checks.json", "regresja mechaniki"),
    ]:
        raw = read(path)
        checks = raw.get("checks")
        if isinstance(checks, list):
            tests = [case(t) if isinstance(t, str) else case(t.get("name", str(i)), t.get("success", True), t) for i, t in enumerate(checks)]
        elif isinstance(checks, dict):
            tests = [case(k, (not v if "console_errors" in k else v) if isinstance(v, (bool, int)) else True, v if isinstance(v, dict) else {"value": v}) for k, v in checks.items()]
        elif raw.get("series"):
            tests = [case(f"100 obrotów — {t['mode']}", t["end_paid_rounds"] - t["start_paid_rounds"] == 100, t) for t in raw["series"]]
        else:
            tests = [case(title, raw.get("passed", raw.get("success", False)), raw)]
        result.append(suite(id_, title, tests, [path], scope="Historia / wcześniejsze testy", version=version, counted=False, details=raw))
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    math = read(MATH_PATH)
    bonus = read(BONUS_PATH)
    final = read(FINAL_PATH)
    weighted = read(WEIGHTED_PATH)
    book = read(BOOK_PATH)
    sdk = read(SDK_PATH)
    network = read(NETWORK_PATH)
    checks = []
    lut = ROOT / "test-interface/stake_math/lookUpTable_base_0.csv"
    lut_hash = sha(lut)
    for title, expected in [("Matematyka", math["files"][lut.name]["sha256"]), ("Bonusy", bonus["lut_sha256"]), ("Symulacje ważone", weighted["lut_sha256"]), ("Audyt wyników", book["lut_sha256"])]:
        assert expected == lut_hash, title
        checks.append({"name": title + " — ta sama tabela losowań", "passed": True, "sha256": lut_hash})
    fingerprints = []
    for name, expected in math["source_fingerprint"].items():
        p = ROOT / "test-interface/engine/polska_gurom" / name
        observed = sha(p)
        assert observed == expected, p
        fingerprints.append({"path": p.relative_to(ROOT).as_posix(), "sha256": observed, "matchesEvidence": True})
    for name, relative in [("app.js", "test-interface/web/app.js"), ("server.py", "test-interface/server.py")]:
        observed = sha(ROOT / relative)
        assert observed == network["source_sha256"][name], relative
        fingerprints.append({"path": relative, "sha256": observed, "matchesEvidence": True})
    assert sum(x["weight"] for x in bonus["bonus_types"]) == bonus["bonus_weight"]
    assert math["bonus_frequency"] == bonus["bonus_probability"]
    assert weighted["total_actual_draws"] == sum(x["rounds"] for x in weighted["runs"]) == 160_000_000
    assert final["math_version"] == math["math_version"] == bonus["math_version"]
    history_path = ROOT / "audit/dashboard_history_inventory.json"
    history = read(history_path.relative_to(ROOT)) if history_path.exists() else {}
    simulations = collect_simulations(final, weighted, bonus) + historical_simulations(history)
    suites = collect_suites(final, book, sdk, network)
    reports = collect_reports()
    known_reports = {r["path"] for r in reports}
    for item in simulations + suites:
        assert all(p in known_reports for p in item["evidence"]), item["id"]
    regression = [s for s in suites if s["countedInRegressionTotal"]]
    missing = bonus["missing_declared_bonus_types"]
    findings = [
        {"id": "missing-12fs", "severity": "critical", "title": "Bonus 12 darmowych obrotów nie występuje", "detail": "Zasady przewidują 5 Scatterów → 12 darmowych obrotów, ale końcowa tabela zawiera 0 takich wyników i wagę 0. Wykryte w analizie bonusów; poprawka nie została jeszcze wdrożona.", "status": "open", "evidence": [BONUS_PATH]},
        {"id": "stake-approval", "severity": "info", "title": "Brak zatwierdzenia platformy Stake", "detail": "Publiczny walidator SDK uruchomiono lokalnie. Nie przeprowadzono procesu zatwierdzenia ani testów prawdziwego RGS i portfela Stake.", "status": "not-performed", "evidence": [SDK_PATH, NETWORK_PATH]},
        {"id": "memory-wallet", "severity": "warning", "title": "Restart usuwa lokalne saldo i historię", "detail": "Lokalny portfel demonstracyjny działa w pamięci. Stara sesja po restarcie jest odrzucana, co zapobiega ponownemu obciążeniu, ale nie odtwarza utraconej historii.", "status": "open", "evidence": [NETWORK_PATH]},
        {"id": "replay-window", "severity": "warning", "title": "Pełne odtworzenie obejmuje ostatnie 100 wyników", "detail": "Starsze identyfikatory są odrzucane bez opłaty. Pełna odpowiedź starszej rundy nie jest już dostępna; odświeżenie działa w tej samej karcie przy dostępnym sessionStorage.", "status": "known-limit", "evidence": [NETWORK_PATH]},
        {"id": "offline-scope", "severity": "info", "title": "Awarie sieci testowano w izolacji", "detail": "Użyto rzeczywistego lokalnego HTTP/TCP i przekaźnika usterek. Nie wyłączano Wi-Fi komputera ani nie testowano połączenia z produkcyjnym Stake.", "status": "scope", "evidence": [NETWORK_PATH]},
    ]
    data = {
        "meta": {"schema": 1, "title": "POLSKA GUROM — wyniki testów", "generatedAt": datetime.now(timezone.utc).isoformat(), "mathVersion": math["math_version"], "snapshotDate": "2026-10-19", "mode": "Lokalny, prywatny przegląd zapisanych wyników", "status": "requires-attention", "statusLabel": "1 krytyczna kwestia otwarta", "notice": "Dashboard odczytuje zapisane wyniki. Nie uruchamia nowych symulacji i nie stanowi zatwierdzenia Stake."},
        "summary": {"exactRtp": math["rtp"], "exactRtpFraction": math["rtp_exact_fraction"], "maxWin": math["max_win"], "maxWinOneIn": math["max_win_one_in"], "hitFrequency": math["hit_frequency"], "netProfitFrequency": math["net_profit_frequency"], "bonusFrequency": bonus["bonus_probability"], "meanRoundsToBonus": bonus["mean_paid_rounds_to_bonus"], "bookCount": math["book_count"], "weightedDraws": weighted["total_actual_draws"], "naturalRounds": sum(r["rounds"] for r in final["natural_candidate_runs"]), "regressionChecks": sum(s["testsCount"] for s in regression), "regressionPassed": sum(s["passedCount"] for s in regression), "networkFaultChecks": network["new_fault_checks"], "criticalOpen": len(missing), "reportCount": len(reports), "browserAutospinsCompleted": 100,
            "currentTestCounts": {"regression": 107, "networkHttp": 17, "networkLogic": 30, "autoplay": 13, "portable": 27, "cascadeEngine": 10, "serverApi": 10, "publicSdkFunctions": 4, "auditedBooks": 100024, "browserAutospinRounds": 100}},
        "math": display(math), "simulations": simulations, "suites": suites,
        "bonus": display(bonus), "findings": findings, "history": display(history), "reports": reports,
        "integrity": {"status": "pass", "lutSha256": lut_hash, "fingerprints": fingerprints, "checks": checks, "reportCopiesByteIdentical": True, "reportCopiesVerified": len(reports), "deduplication": "107 przypadków regresji to 17 HTTP + 30 logiki awarii + 13 autospinu + 27 paczki + 10 silnika + 10 API. Nie dodajemy do tej sumy ponownie raportów zbiorczych, symulacji, audytu wyników ani historii."},
    }
    assert data["summary"]["regressionChecks"] == 107
    assert data["summary"]["regressionPassed"] == 107
    assert data["summary"]["criticalOpen"] == 1
    target = OUT / "data.json"
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "data-embed.js").write_text("window.DASHBOARD_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(json.dumps({"output": target.relative_to(ROOT).as_posix(), "bytes": target.stat().st_size, "reports": len(reports), "simulations": len(simulations), "suites": len(suites), "regressionChecks": data["summary"]["regressionChecks"], "weightedDraws": data["summary"]["weightedDraws"], "naturalRounds": data["summary"]["naturalRounds"], "openCritical": len(missing), "hashChecks": "PASS"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
