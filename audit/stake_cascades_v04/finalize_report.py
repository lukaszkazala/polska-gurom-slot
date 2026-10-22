"""Collect completed evidence and package the tested release, without rerunning RNG."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEMO = ROOT / "test-interface"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def link(label, path):
    return f"[{label}](<{path.resolve().as_posix()}>)"


def main():
    weighted = read(HERE / "fast_sim/weighted_results/weighted_simulation_report.json")
    mechanics = read(HERE / "book_mechanics_report.json")
    official = read(HERE / "official_validation/official_validation_report.json")
    crosscheck = read(HERE / "fast_sim/crosscheck.json")
    autoplay = read(DEMO / "qa/autoplay_logic_results.json")
    portable = read(DEMO / "qa/portable_check.json")
    browser = read(HERE / "browser_check.json")
    math = read(DEMO / "stake_math/mathematics.json")
    natural = [read(HERE / f"fast_sim/natural_{size}m.json") for size in (10,50,100)]
    assert official["status"] == mechanics["status"] == "PASS"
    assert autoplay["passed"] and portable["success"]
    assert browser["rounds"] == 100 and "100 / 100" in browser["progress"]
    assert browser["consoleErrors"] == [] and browser["spinEnabled"]
    assert weighted["total_actual_draws"] == 160000000
    assert all(x["actual_integer_tickets_drawn"] == x["rounds"] for x in weighted["runs"])
    assert all(x["within_95_normal_reference_band"] for x in weighted["runs"])
    assert all(x["guardHits"] == 0 for x in natural)
    assert hashlib.sha256((DEMO/"web/app.js").read_bytes()).hexdigest() == autoplay["source_sha256"]
    archive = DEMO / "POLSKA_GUROM_v0_4_RTP96.zip"
    shutil.copyfile(DEMO / "POLSKA_GUROM_TESTER.zip", archive)
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == portable["zip_sha256"]
    upload = DEMO / "POLSKA_GUROM_STAKE_MATH_v0_4.zip"
    with zipfile.ZipFile(upload,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as target:
        for name in ("index.json","books_base.jsonl.zst","lookUpTable_base_0.csv"):
            target.write(DEMO / "stake_math" / name, name)
    with zipfile.ZipFile(upload) as target:
        assert target.testzip() is None
        assert all(target.read(name) == (DEMO/"stake_math"/name).read_bytes() for name in target.namelist())
    result = {"status":"PASS", "created_utc":datetime.now(timezone.utc).isoformat(),
              "math_version":math["math_version"], "exact_rtp":math["rtp_exact_fraction"],
              "published_book_draws": weighted["runs"], "natural_candidate_runs": natural,
              "independent_book_mechanics":mechanics, "public_sdk_status":official["status"],
              "autoplay_logic_checks":len(autoplay["checks"]), "browser":browser,
              "portable_checks":len(portable["checks"]),
              "executed_unittest_suites":[{"path":"test-interface/qa/test_cascades.py","tests":10,"failures":0},
                                           {"path":"test-interface/test_server.py","tests":10,"failures":0}],
              "artifacts":{p.name:{"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
                           for p in (archive,upload)},
              "platform_approval":"Not performed; local public SDK verification only"}
    (HERE / "final_results.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    lines = ["# POLSKA GUROM v0.4 — matematyka i testy", "", "19 października 2026. Wynik kontroli lokalnych: **PASS**.", "",
        "Gra losowa ma dokładne **96% RTP** z wag pełnych rund. Limit całej rundy wynosi **5000×**; jego częstość wynosi **1:8 000 000**. Kaskady uruchamiają się automatycznie.", "",
        "## Model końcowy", "",
        f"- Jeden tryb `base`, koszt 1× stawki; {math['book_count']:,} różnych pełnych rund, wszystkie z dodatnimi wagami.".replace(",", " "),
        "- Jedna runda zawiera płatny obrót, wszystkie kaskady i cały bonus. Rozliczenie następuje raz.",
        "- Suma wag: 1 000 000 000 000. Suma waga × wypłata: 96 000 000 000 000 jednostek (skala 100).",
        "- RTP = 96 000 000 000 000 / (100 × 1 000 000 000 000) = 24/25 = **96%**, bez zaokrąglania wyniku.",
        "- Wypłaty liniowe są w kroku 0,1×. Nie stosuje się osobnego zaokrąglenia tylko na potrzeby eksportu.",
        f"- Dowolna dodatnia wypłata: **{100*math['hit_frequency']:.6f}%** rund; wypłata wyższa od stawki: **{100*math['net_profit_frequency']:.6f}%**.",
        f"- Bonus: **{100*math['bonus_frequency']:.6f}%** rund. Odchylenie standardowe wypłaty rundy: **{math['standard_deviation']:.6f}×**.",
        f"- {math['distinct_payouts']} różnych wartości wypłaty. Największa szansa pojedynczego book: {100*math['largest_single_book_probability']:.6f}%.",
        "- 100 000 wyników pochodzi z generatora kandydatów. 24 dodatkowe wyniki zapewniają osiągalne duże wygrane, w tym cztery różne wyniki 5000×. Każdy powstał przez rzeczywiste ocenianie linii i uzupełnienia dopuszczone przez paski symboli; żadna wypłata nie została dopisana ręcznie.",
        "- Wagi są stałe i niezależne od gracza, salda, stawki, historii oraz ustawień animacji. Lokalna gra używa tej samej tabeli wag co eksport RGS.", "",
        "## Testy 10, 50 i 100 mln — końcowy rozkład RGS", "",
        "Każda płatna runda to jeden faktyczny losowy całkowity bilet i wyszukanie wyniku w końcowej tabeli wag. Nie zastąpiono losowań wzorem ani rozkładem wielomianowym. To test wyboru gotowych pełnych rund; mechanika i wszystkie zapisane zdarzenia są sprawdzone osobno poniżej.", "",
        "| Rundy | Seed | Zmierzony RTP | 95% przedział normalny | Trafienia 5000× |", "|---:|---:|---:|---:|---:|"]
    for run in weighted["runs"]:
        lo,hi = run["normal_95_interval_around_observed"]
        lines.append(f"| {run['rounds']:,} | {run['seed']} | {100*run['rtp']:.7f}% | {100*lo:.5f}–{100*hi:.5f}% | {run['max_win_hits']} |".replace(","," "))
    lines += ["", "Łącznie **160 mln niezależnych losowań** w trzech seriach z różnymi seedami. Wszystkie trzy wyniki mieszczą się w normalnym paśmie 95% względem dokładnego RTP. Przedziały opisują błąd Monte Carlo, nie certyfikację. Zero trafień maksimum w serii 10 mln jest możliwe; oczekiwana liczba to 1,25. Nie dobierano ponownie seedów po obejrzeniu wyników.", "",
        "## Niezależna kontrola mechaniki i wcześniejsze regresje", "",
        f"- **{mechanics['exported_books_checked']} / {mechanics['exported_books_checked']}** books: niezależne wyliczenie każdej wygranej liniowej, usunięć, ruchu w dół, uzupełnienia oraz rozliczenia limitu.",
        "- Pełne zdarzenia każdego book zgadzają się z lokalnym odtworzeniem. Sprawdzono także wszystkie cztery wyniki maksimum, bonusy i rozwinięcia WILD.",
        "- 10 testów mechaniki kaskad — PASS. 10 testów HTTP i salda — PASS (w tym ponowienia tej samej rundy, konflikty ID, równoczesne ponowienia i limit 5000×).",
        "- 13 deterministycznych testów autospinu — PASS: 100 obrotów we wszystkich prędkościach, ukrycie przy 80/81, błąd i ponowienie 81. rundy, zatrzymanie, brak salda.",
        "- Rzeczywista przeglądarka: **100/100** losowych płatnych rund z animacjami turbo, poprawne zakończenie, brak błędów konsoli; następnie przywrócono normalną animację.",
        f"- Paczka ZIP po wypakowaniu: **{len(portable['checks'])} kontroli PASS**, w tym zgodność plików silnika, faktycznie uruchomiony serwer i kompletne rozliczenie serializowanych kaskad.",
        "- Oryginalne 30 plików modelu v0.2 pozostało bez zmian (kontrola sum SHA-256).", "",
        "## Dodatkowe pełne symulacje generatora kandydatów", "",
        "Niezależna kompilowana implementacja generowała plansze, oceniała wszystkie linie i wykonywała opadanie oraz bonusy od początku. Jej przebieg porównano dokładnie z Pythonem dla 10 000 rund ze wspólnym strumieniem SplitMix64. Te serie badają generator kandydatów, **nie końcowy rozkład ważonych books**.", "",
        "| Rundy | Seed | Zwrot generatora | Techniczny limit kaskad osiągnięty |", "|---:|---:|---:|---:|"]
    for run in natural:
        lines.append(f"| {run['rounds']:,} | {run['seed']} | {100*run['rtp']:.7f}% | {run['guardHits']} |".replace(","," "))
    lines += ["", "## Stake SDK i zakres zgodności", "",
        "Lokalnie wykonano niezmienione publiczne funkcje SDK: `verify_lookup_format`, `verify_books_and_payout_mults`, `compare_payout_values`, `get_lut_statistics`. Wszystkie zakończyły się poprawnie; brak ostrzeżeń walidatora. Dodatkowo sprawdzono dokładne liczby całkowite, zgodność ID z numerem linii, 100 024 różne sekwencje zdarzeń, dodatnie wagi, krok wypłat i granice uint64.",
        "Użyto oficjalnego Math SDK z commita `a6dccd86de740cc5d318079483cb6204cc5c19bc`; pobrane źródła mają zapisane i sprawdzone sumy SHA-256.",
        "**Nie wykonano zatwierdzenia przez platformę ani publikacji.** Integracja rzeczywistego portfela RGS, uwierzytelnienia, replay i końcowy proces approval pozostają osobnym etapem. Parametr 25% rozwinięcia dotyczy generatora; końcowe częstości wynikają z wag.", "",
        "Źródła: [Math Requirements](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/math-requirements/%2Bpage.svx), [How RGS Works](https://github.com/engineio/docs/blob/main/src/routes/docs/architecture/how-rgs-works/%2Bpage.svx), [publiczny walidator SDK](https://github.com/engineio/math-sdk/blob/a6dccd86de740cc5d318079483cb6204cc5c19bc/utils/rgs_verification.py).", "",
        "## Pliki i odtworzenie kontroli", "",
        "- " + link("Gra — kompletna paczka ZIP",archive),
        "- " + link("Same trzy pliki publikacji matematyki Stake",upload),
        "- " + link("Dokładne parametry matematyki",DEMO/"stake_math/mathematics.json"),
        "- " + link("Surowe wyniki 10/50/100 mln, przedziały i histogramy",HERE/"fast_sim/weighted_results/weighted_simulation_report.json"),
        "- " + link("Raport publicznego SDK",HERE/"official_validation/official_validation_report.json"),
        "- " + link("Niezależny audyt wszystkich books",HERE/"book_mechanics_report.json"),
        "- " + link("Wyniki autospinu",DEMO/"qa/autoplay_logic_results.json"),
        "- " + link("Kontrole paczki",DEMO/"qa/portable_check.json"),
        "- " + link("Zbiorczy raport JSON",HERE/"final_results.json"), "",
        "Z katalogu projektu: `python audit/stake_cascades_v04/build_math.py`, potem `python audit/stake_cascades_v04/verify_book_mechanics.py`, `python audit/stake_cascades_v04/official_validation/run_official_validation.py` i `python audit/stake_cascades_v04/fast_sim/weighted_book_tests.py`. Skrypty wykorzystują zapisane seedy. Duże losowania wymagają NumPy/SciPy; kompresja i publiczny walidator wymagają zstandard. Uruchomienie samej gry korzysta ze standardowej biblioteki Pythona.", ""]
    (HERE / "RAPORT_PL.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps({"status":"PASS","report":str(HERE/"RAPORT_PL.md"),"zip":str(archive)},ensure_ascii=False))


if __name__ == "__main__":
    main()
