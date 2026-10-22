"""Build the 0.4.1 dashboard while preserving every 0.4.0 source byte.

Run only after the new game validation has finished. Missing evidence or a stale
LUT is a build error; historical reports are never substituted for current tests.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

from build_data import display, case, suite, HTTP_LABELS, LOGIC_LABELS, AUTOPLAY_LABELS, PORTABLE_LABELS, UNIT_LABELS

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "dist"
FIX = "audit/bonus12_fix_2026_10_20/"
BASE = FIX + "before/results-dashboard/dist/data.json"
PREFIX = "baseline-v040/"
VERSION = "0.4.1-weighted-12fs"
MATH = "test-interface/stake_math/mathematics.json"
COVERAGE_LABELS = [
    "Każdy skonfigurowany bonus ma dodatnią masę w eksporcie",
    "Naturalny świadek pięciu Scatterów wykonuje 12 darmowych obrotów",
    "Bonusy wynikają z legalnych początkowych okien bębnów",
    "Wszystkie bonusy odtwarzają się i przechodzą niezależny audyt mechaniki",
    "12FS można wylosować na obu brzegach przedziałów biletów",
    "Dokładny RTP i kontrakt maksymalnej wygranej zachowane",
    "Dodanie 12FS zachowuje całkowitą częstość bonusów",
    "Odrzucenie fałszywej nagrody 8FS przy pięciu Scatterach",
    "Usunięcie wszystkich wyników 12FS jest wykrywane",
    "Zerowe wagi wyników 12FS są odrzucane",
    "Fałszywa deklaracja pokrycia 12FS jest odrzucana",
]
API12_LABELS = [
    "Pięć Scatterów prowadzi do 12 legalnych darmowych obrotów",
    "Produkcyjny selektor odtwarza pełny wynik bonusowy",
    "Wszystkie 12 obrotów jest rozliczane za jedną stawkę",
    "Ponowienie po zgubionej odpowiedzi zachowuje ID i jedną opłatę",
    "Równoczesne ponowienia tego samego ID rozliczają rundę raz",
    "Stan sesji odtwarza pełny bonus 12FS",
    "Sprzeczne ponowienie nie pobiera nowej stawki",
    "Wspólny limit obejmuje bonus i ponowienie odpowiedzi",
    "Stara sesja nie przenosi bonusu do wyzerowanego portfela",
    "Opublikowany rozkład zawiera wynik 12FS z dodatnią wagą",
]
FRONTEND12_LABELS = [
    "Pełny bonus 12/12 w zwykłym tempie",
    "Pełny bonus 12/12 w szybkim tempie",
    "Pełny bonus 12/12 w trybie turbo",
    "Pełny bonus 12/12 w trybie natychmiastowym",
    "100 płatnych rund z bonusami — 1200 darmowych obrotów",
    "Zgubiona odpowiedź 12FS — 100 rund bez podwójnego obciążenia",
    "STOP podczas piątego FS kończy wszystkie 12 bez nowej płatnej rundy",
]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def remap(value, mapping):
    if isinstance(value, dict):
        return {key: remap(item, mapping) for key, item in value.items()}
    if isinstance(value, list):
        return [remap(item, mapping) for item in value]
    return mapping.get(value, value) if isinstance(value, str) else value


def archived_data():
    original = read(BASE)
    mapping = {r["path"]: PREFIX + r["path"] for r in original["reports"]}
    data = remap(deepcopy(original), mapping)
    registry = []
    for old in original["reports"]:
        path = PREFIX + old["path"]
        destination = OUT / "reports" / path
        if not destination.exists():
            source = OUT / old["href"]
            assert sha(source) == old["sha256"], f"Historical evidence has changed: {source}"
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        assert sha(destination) == old["sha256"], f"Invalid preserved evidence: {path}"
        registry.append({**old, "id": path, "path": path, "href": "reports/" + path,
                         "category": "historia", "displayTitle": old.get("displayTitle", old["title"]) + " · archiwum 0.4.0"})
    for item in data["suites"]:
        item.update(id="history-v040-" + item["id"], current=False, historical=True,
                    scope="Historia / stan przed poprawką 12FS", countedInRegressionTotal=False)
    for item in data["simulations"]:
        if item["kind"] in {"weighted", "diagnostic"}:
            item.update(id="history-v040-" + item["id"], kind="historical", status="historical",
                        scope="Archiwalny eksport 0.4.0 sprzed poprawki 12FS. " + item["scope"])
    return data, registry


def report_cases(raw, previous=None, labels=None):
    """Use actual case records when present, suite-level unittest evidence otherwise."""
    items = raw.get("checks", raw.get("tests"))
    if isinstance(items, list) and all(isinstance(x, dict) for x in items):
        items = [item for item in items if any(key in item for key in ("name", "scenario", "test"))]
        result = []
        for index, item in enumerate(items):
            name = item.get("name", item.get("scenario", item.get("test", f"Kontrola {index + 1}")))
            passed = item.get("passed", item.get("success"))
            if passed is None:
                passed = str(item.get("status", raw.get("status", ""))).lower() in {"pass", "passed", "ok", "success"}
            label = labels[index] if labels and len(labels) == len(items) else UNIT_LABELS.get(str(name).split(".")[-1], name)
            result.append(case(label, bool(passed), item, originalName=name))
        return result
    count = raw.get("tests_run", raw.get("testsRun", raw.get("tests_count", raw.get("total"))))
    assert isinstance(count, int) and count > 0, f"Unknown test-report schema: {raw.keys()}"
    failures = raw.get("failures", [])
    errors = raw.get("errors", [])
    passed = str(raw.get("status", "")).lower() in {"pass", "passed", "ok", "success"} and not failures and not errors
    names = raw.get("test_names", raw.get("names", []))
    if labels and len(labels) == count:
        names = labels
    if previous and len(previous.get("tests", [])) == count:
        names = [t.get("label_pl", t["name"]) for t in previous["tests"]]
    return [case(names[index] if index < len(names) else f"Kontrola {index + 1}", passed,
                 {"evidenceBasis": "Wynik aktualnie wykonanej serii unittest; szczegóły w raporcie źródłowym.",
                  "suiteStatus": raw.get("status"), "testsRun": count}) for index in range(count)]


def current_suites(old):
    previous = {s["id"].removeprefix("history-v040-"): s for s in old}
    specifications = [
        ("network-http", "Awarie połączenia — HTTP i TCP", "network_faults_results.json", HTTP_LABELS),
        ("network-logic", "Awarie połączenia — logika gry", "network_logic_results.json", LOGIC_LABELS),
        ("autoplay", "Autospin — 100 obrotów i zatrzymywanie", "autoplay_logic_results.json", AUTOPLAY_LABELS),
        ("portable", "Paczka przenośna — aktualna matematyka", "portable_check.json", PORTABLE_LABELS),
        ("cascade-engine", "Mechanika kaskad — testy silnika", "cascade_engine_results.json", None),
        ("server-api", "Serwer — regresja API", "server_api_results.json", None),
        ("bonus12-coverage", "12 darmowych obrotów — pokrycie eksportu i mutacje", "coverage_results.json", COVERAGE_LABELS),
        ("bonus12-api", "12 darmowych obrotów — rozliczenie i API", "api_12fs_results.json", API12_LABELS),
        ("bonus12-frontend", "12 darmowych obrotów — interfejs i autospin", "frontend_12fs_results.json", FRONTEND12_LABELS),
    ]
    result = []
    for identifier, title, filename, labels in specifications:
        path = FIX + filename
        raw = read(path)
        if "math_version" in raw:
            assert raw["math_version"] == VERSION, path
        tests = report_cases(raw, previous.get(identifier), labels)
        if "tests_run" in raw:
            assert len(tests) == raw["tests_run"], path
        result.append(suite(identifier, title, tests, [path], version=VERSION, details=raw))
    book = read(FIX + "book_mechanics_report.json")
    tests = [case("Odtworzenie wszystkich wyników zgadza się z eksportem", book["full_local_replay_matches_export"]),
             case("Wszystkie sekwencje są unikalne", book["unique_complete_events"] == book["exported_books_checked"]),
             case("Niezależne wypłaty, ruchy i kaskady", book["status"] == "PASS", book["independent_oracle"]),
             case("Zachowane cztery wyniki maksymalnej wygranej", book["max_win_books_checked"] == 4),
             case("Audyt obejmuje wszystkie wyniki bonusowe", book["bonus_books_checked"] == 526),
             case("Oryginalne materiały v0.2 bez zmian", book["original_v02"]["unchanged"])]
    result.append(suite("books", f"Niezależny audyt {book['exported_books_checked']:,} pełnych wyników".replace(",", " "), tests,
                        [FIX + "book_mechanics_report.json"], version=VERSION, details=book, counted=False))
    sdk = read(FIX + "official_validation_report.json")
    mode = sdk["modes"][0]
    tests = [case(name, status == "PASS") for name, status in mode["official_functions"].items()]
    for field, label in [("additional_exact_integer_checks", "Dokładne wagi, RTP i kwantyzacja"),
                         ("additional_book_checks", "Zgodność identyfikatorów i wyników")]:
        tests.append(case(label, mode[field]["status"] == "PASS", mode[field]))
    result.append(suite("public-sdk", "Publiczny walidator Stake SDK — lokalnie", tests,
                        [FIX + "official_validation_report.json"], version=VERSION, details=sdk, counted=False))
    return result


def main():
    data, registry = archived_data()
    math = read(MATH)
    bonus = read(FIX + "bonus_frequency.json")
    weighted = read(FIX + "weighted_results/weighted_simulation_report.json")
    coverage = read(FIX + "coverage_results.json")
    book = read(FIX + "book_mechanics_report.json")
    lut_hash = sha(ROOT / "test-interface/stake_math/lookUpTable_base_0.csv")
    assert math["math_version"] == bonus["math_version"] == VERSION
    for raw in (bonus, weighted, coverage, book):
        assert raw["lut_sha256"] == lut_hash, "An active report refers to a different LUT"
    assert math["files"]["lookUpTable_base_0.csv"]["sha256"] == lut_hash
    assert math["book_count"] == 100048 and math["rtp_exact_fraction"] == "24/25"
    assert math["max_win"] == 5000 and math["max_win_weight"] == 125000
    assert math["total_weight"] == 10**12 and math["weighted_payout_units_sum"] == 96 * 10**12
    types = {t["free_spins"]: t for t in bonus["bonus_types"]}
    assert set(types) == {8, 10, 12} and all(t["books"] > 0 and t["weight"] > 0 for t in types.values())
    assert types[12]["books"] == 24 and types[12]["weight"] == 4018776
    assert sum(t["weight"] for t in types.values()) == bonus["bonus_weight"] == 4969935540
    assert coverage["status"] == "PASS" and not coverage["failures"] and not coverage["errors"]
    assert not bonus.get("missing_declared_bonus_types", [])
    current = current_suites(data["suites"])
    regression = [s for s in current if s["countedInRegressionTotal"]]
    assert sum(s["testsCount"] for s in regression) == 135
    assert all(s["failedCount"] == 0 for s in current)
    data["suites"] = current + data["suites"]
    bonus_runs = {r["rounds"]: r for r in bonus["previous_simulations_aggregated"]}
    simulations = []
    for run in weighted["runs"]:
        b = bonus_runs[run["rounds"]]
        simulations.append({"id": "weighted-" + str(run["rounds"]), "kind": "weighted", "title": "Końcowa tabela po naprawie 12FS",
            "version": VERSION, "rounds": run["rounds"], "rtp": run["rtp"], "referenceRtp": .96,
            "interval95": run["normal_95_interval_around_observed"], "status": "pass" if run["within_95_normal_reference_band"] else "review",
            "hitFrequency": run["hit_frequency"], "bonusFrequency": b["bonus_frequency"], "bonuses": b["bonuses"],
            "bonus12Count": b.get("by_free_spins", {}).get("12", 0), "maxWinHits": run["max_win_hits"],
            "maxWinExpectedHits": run["max_win_expected_hits"], "seed": run["seed"],
            "evidence": [FIX + "weighted_results/weighted_simulation_report.json", FIX + "bonus_frequency.json"],
            "details": display(run), "scope": "Rzeczywiste losowania aktualnej tabeli 0.4.1 z dodatnią masą 12FS. Pełna mechanika sprawdzona osobnym audytem."})
    assert weighted["total_actual_draws"] == sum(x["rounds"] for x in simulations) == 160000000
    data["simulations"] = simulations + data["simulations"]
    for filename in [MATH, *sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / FIX).rglob("*")
                                 if p.is_file() and "before" not in p.relative_to(ROOT / FIX).parts
                                 and p.name != "dashboard_update_results.json"
                                 and p.suffix.lower() in {".json", ".md", ".csv"})]:
        source = ROOT / filename
        destination = OUT / "reports" / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        assert sha(source) == sha(destination)
        registry.append({"id": filename, "path": filename, "href": "reports/" + filename,
            "title": source.stem.replace("_", " "), "sha256": sha(source), "bytes": source.stat().st_size,
            "category": "aktualne", "format": source.suffix[1:].lower()})
    data["reports"] = registry
    data["meta"].update(generatedAt=datetime.now(timezone.utc).isoformat(), mathVersion=VERSION,
        snapshotDate="2026-10-20", status="verified-local", statusLabel="12FS naprawione i sprawdzone lokalnie",
        bonusReportPath=FIX + "bonus_frequency.json", coverageReportPath=FIX + "coverage_results.json",
        bookReportPath=FIX + "book_mechanics_report.json", sdkReportPath=FIX + "official_validation_report.json",
        networkReportPath=FIX + "network_faults_results.json")
    data["summary"].update(exactRtp=math["rtp"], exactRtpFraction=math["rtp_exact_fraction"],
        maxWin=math["max_win"], maxWinOneIn=math["max_win_one_in"], hitFrequency=math["hit_frequency"],
        netProfitFrequency=math["net_profit_frequency"], bonusFrequency=bonus["bonus_probability"],
        meanRoundsToBonus=bonus["mean_paid_rounds_to_bonus"], bookCount=math["book_count"],
        weightedDraws=weighted["total_actual_draws"], regressionChecks=sum(s["testsCount"] for s in regression),
        regressionPassed=sum(s["passedCount"] for s in regression), criticalOpen=0,
        reportCount=len(registry), networkFaultChecks=sum(s["testsCount"] for s in regression if s["id"] in {"network-http", "network-logic"}),
        bonus12Verified=True, bonus12Books=types[12]["books"], bonus12Weight=types[12]["weight"],
        currentSuiteCount=len(regression), currentTestCounts={s["id"]: s["testsCount"] for s in regression})
    data["math"] = display(math)
    data["bonus"] = display(bonus)
    data["findings"] = [f for f in data["findings"] if f["id"] != "missing-12fs"]
    data["findings"].insert(0, {"id": "resolved-12fs", "severity": "info", "status": "verified",
        "title": "Bonus 12 darmowych obrotów jest dostępny", "detail": "Dodano 24 legalne, pełne rundy z pięcioma Scatterami. Łączna dodatnia masa wynosi 4 018 776 / 10¹². Poprawka zachowuje RTP 96%, całkowitą częstość bonusu i prawdopodobieństwo maksymalnej wygranej.",
        "evidence": [FIX + "coverage_results.json", FIX + "bonus_frequency.json"]})
    data["history"]["phases"].append({"id": "bonus12-fix", "name": "Usunięcie luki wariantu 12 darmowych obrotów",
        "version": VERSION, "date": "2026-10-20", "status": "verified", "scope": "Kontrolowane pokrycie wszystkich wariantów bonusu i ponowna kalibracja wag.",
        "results": {"rtp": math["rtp"], "book_count": math["book_count"], "tests_total": data["summary"]["regressionChecks"],
                    "bonus12_books": 24, "bonus12_weight": 4018776},
        "limitations": ["Końcowa częstotliwość 12FS została jawnie dobrana na podstawie pasków; bank pozostaje skończonym modelem ważonym.", "Walidacja lokalna; bez zatwierdzenia produkcyjnego Stake."],
        "sourcepaths": [FIX + "math_review.md", FIX + "coverage_results.json", FIX + "bonus_frequency.json"]})
    fingerprints = [{"path": "test-interface/engine/polska_gurom/" + name, "sha256": value,
                     "matchesEvidence": sha(ROOT / "test-interface/engine/polska_gurom" / name) == value}
                    for name, value in math["source_fingerprint"].items()]
    assert all(f["matchesEvidence"] for f in fingerprints)
    data["integrity"] = {"status": "pass", "lutSha256": lut_hash, "fingerprints": fingerprints,
        "checks": [{"name": "Aktualne raporty dotyczą tego samego LUT", "passed": True},
                   {"name": "Warianty 8/10/12FS mają dodatnie wagi", "passed": True},
                   {"name": "Archiwum 0.4.0 zachowane bajt w bajt", "passed": True}],
        "reportCopiesByteIdentical": True, "reportCopiesVerified": len(registry),
        "deduplication": "135 bieżących kontroli to 107 ponownie wykonanych regresji i 28 nowych kontroli 12FS. SDK, audyt całego banku i stare wersje nie zwiększają tej sumy."}
    known = {r["path"] for r in registry}
    for obj in data["simulations"] + data["suites"] + data["findings"]:
        assert all(p in known for p in obj.get("evidence", [])), obj.get("id")
    assert len(known) == len(registry)
    assert all(path in known for phase in data["history"]["phases"] for path in phase.get("sourcepaths", []))
    (OUT / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "data-embed.js").write_text("window.DASHBOARD_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    result = {"status": "PASS", "mathVersion": VERSION, "regressionChecks": data["summary"]["regressionChecks"],
        "reports": len(registry), "historicalReports": len(read(BASE)["reports"]), "simulations": len(data["simulations"]),
        "weightedDraws": data["summary"]["weightedDraws"], "bonus12Books": 24, "bonus12Weight": 4018776,
        "lutSha256": lut_hash, "preservedBaselineHashes": True}
    (ROOT / FIX / "dashboard_update_results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
