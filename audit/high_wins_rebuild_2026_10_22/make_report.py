"""Produce the Polish acceptance report from independently verified exports."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def num(value, digits=6):
    if isinstance(value, dict):
        value = value["value"]
    return f"{value:,.{digits}f}".replace(",", " ").replace(".", ",")


def main():
    baseline, final = load("baseline_verification.json"), load("final_verification.json")
    regressions, repeat = load("regression_summary.json"), load("reproducibility.json")
    legacy = load("legacy_cap_regressions.json")
    portable = load("portable/portable_check.json")
    legacy_portable = load("legacy_portable/portable_check.json")
    browser = load("browser_smoke.json")
    assert baseline["success"] and final["success"] and regressions["passed"] and repeat["passed"]
    assert legacy["passed"] == legacy["tests_run"] == 45
    assert portable["success"] and legacy_portable["success"] and browser["passed"]
    before, after = baseline["metrics"], final["metrics"]
    summary = json.loads((ROOT / "test-interface-any-start/stake_math/mathematics.json").read_text(encoding="utf-8"))
    design = summary["high_win_design"]
    comparison = {"baseline_version": before["math_version"], "new_version": after["math_version"],
                  "baseline": before, "new": after,
                  "ordinary_to_high_rtp_transfer_units": 0,
                  "high_frequency_relative_change": after["high_weight"]/before["high_weight"]-1,
                  "base_rtp_change_percentage_points":
                      (after["base_rtp"]["value"]-before["base_rtp"]["value"])*100,
                  "reproducibility": repeat, "regressions": regressions,
                  "independent_event_verification": {"passed": final["success"], "counts": final["counts"]},
                  "high_band_design": design, "legacy_cap_tests": legacy,
                  "portable_packages": [portable, legacy_portable], "browser_check": browser}
    (HERE / "COMPARISON.json").write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    text = [
        "# Odbiór przebudowy wysokich wygranych — 22.10.2026",
        "",
        "Wersja: **0.6.0-high-wins**. Punkt odniesienia: **0.5.0-any-start**.",
        "",
        "**Wynik: lokalna przebudowa banku i wag wykonana, pięć warunków decyzji spełnionych.** "
        "Wszystkie wyniki poniżej pochodzą z pełnego przeliczenia opublikowanych wag i zdarzeń. "
        "Weryfikacja nie jest akceptacją zewnętrznej platformy. Uruchomiony wcześniej serwer należy uruchomić ponownie, aby wczytał nową wersję.",
        "",
        "Zachowano bębny, tabelę wypłat, linie od dowolnego bębna, kaskady, koszt 1×, krok 0,1×, "
        "bonusy 8/10/12 FS, mnożnik linii 4× i ekspansję Wildów. W konfiguracji zmieniono wyłącznie numer matematyki. "
        "Nowe receptury wskazują legalne losowania; nie poprawiają kwot ani zdarzeń po ocenie planszy. "
        "Prawdopodobieństwa końcowe wynikają z wag pełnych rund.",
        "",
        "## Porównanie pełnych rozkładów", "",
        "| Parametr | 0.5.0-any-start | 0.6.0-high-wins |", "|---|---:|---:|",
    ]
    rows = [
        ("Pełne rundy z dodatnią wagą", str(before["book_count"]), str(after["book_count"])),
        ("Dokładne RTP", before["rtp"]["fraction"], after["rtp"]["fraction"]),
        ("Limit całej rundy", "5000×", "5000×"),
        ("Łączna częstość maksimum", "1:8 000 000", "1:8 000 000"),
        ("Rundy ≥500×", str(before["high_records"]), str(after["high_records"])),
        ("Różne kwoty ≥500×", str(before["high_distinct_payouts"]), str(after["high_distinct_payouts"])),
        ("Największa luka 500×–5000×, łącznie z brzegami", num(before["high_largest_gap_x"], 1)+"×", num(after["high_largest_gap_x"], 1)+"×"),
        ("Częstość ≥500×", "1:"+num(10**12/before["high_weight"], 2), "1:"+num(10**12/after["high_weight"], 2)),
        ("Wkład ≥500× do RTP [p.p.]", num(before["high_rtp_percentage_points"], 11), num(after["high_rtp_percentage_points"], 11)),
        ("Wkład maksimum do RTP [p.p.]", "0,0625", "0,0625"),
        ("Wkład wypłat <500× do RTP [p.p.]", num(before["ordinary_rtp"]["value"]*100, 11), num(after["ordinary_rtp"]["value"]*100, 11)),
        ("Wkład bazy do RTP [p.p.]", num(before["base_rtp"]["value"]*100, 8), num(after["base_rtp"]["value"]*100, 8)),
        ("Wkład FS do RTP [p.p.]", num(before["bonus_rtp"]["value"]*100, 8), num(after["bonus_rtp"]["value"]*100, 8)),
        ("Wariancja wypłaty [stawka²]", num(before["variance"], 9), num(after["variance"], 9)),
        ("Odchylenie standardowe [stawka]", num(before["standard_deviation"], 9), num(after["standard_deviation"], 9)),
        ("Hit rate: wypłata >0 [%]", num(before["hit_frequency"]["value"]*100, 8), num(after["hit_frequency"]["value"]*100, 8)),
        ("Częstość zysku: wypłata >1× [%]", num(before["net_profit_frequency"]["value"]*100, 8), num(after["net_profit_frequency"]["value"]*100, 8)),
        ("Udział największego rekordu we wkładzie ≥500× [%]", num(before["high_top_record_rtp_shares"]["1"]["value"]*100, 6), num(after["high_top_record_rtp_shares"]["1"]["value"]*100, 6)),
        ("Udział 5 największych rekordów we wkładzie ≥500× [%]", num(before["high_top_record_rtp_shares"]["5"]["value"]*100, 6), num(after["high_top_record_rtp_shares"]["5"]["value"]*100, 6)),
    ]
    text.extend(f"| {label} | {a} | {b} |" for label, a, b in rows)
    text += ["", "**Istotny kompromis:** przy tym samym budżecie RTP częstotliwość ≥500× maleje o "
             + num((1-after["high_weight"]/before["high_weight"])*100, 4)
             + "%, ponieważ większa część tego budżetu trafia do wyższych pasm. Zwiększa się różnorodność, "
             "ale ta wersja nie obiecuje częstszych wysokich wygranych ani poprawy krótkich sesji. "
             "Przesunięcie RTP z wypłat <500× do ≥500× wynosi dokładnie **0 p.p.**. "
             "Podział zwrotu między bazą i FS zmienia się jawnie zgodnie z tabelą.",
             "", "## Docelowe pasma zapisane przed doborem wag", "",
             "Przyjęto 18 pasm po 250× oraz osobne maksimum. Udziały RTP pasm bez maksimum maleją w stosunku 4/5, "
             "a cel częstości obliczono z budżetu i środka pasma. Każde pasmo ma dokładną docelową masę biletów, "
             "dopuszczalne odchylenie wkładu RTP wynosi 1%. W każdym paśmie podział masy to 40% baza, 30% 8 FS, "
             "20% 10 FS, 10% 12 FS, z resztami całkowitoliczbowymi w 12 FS. "
             "Końcowy sumaryczny wkład ≥500× jest zachowany dokładnie, bez tolerancji.",
             "", "| Pasmo × stawki | Bilety: cel = wynik | Częstość 1:N | Docelowe RTP [p.p.] | Wynik RTP [p.p.] |",
             "|---|---:|---:|---:|---:|"]
    for band in design["bands"]:
        text.append(f'| [{band["lower_units"]/100:g}; {band["upper_units_exclusive"]/100:g}) | '
                    f'{num(band["actual_weight"], 0)} | {num(10**12/band["actual_weight"], 2)} | '
                    f'{num(band["target_rtp_percentage_points"], 10)} | {num(band["actual_rtp_percentage_points"], 10)} |')
    text += ["| 5000 | 125000 | 8 000 000 | 0,0625 | 0,0625 |", "",
             "Szczegółowy, dokładny plan: [tuning_targets.json](tuning_targets.json). "
             "Receptury są dobierane do pasm, a dodatnie wagi realizują powyższe częstości i wkłady. "
             "Najrzadsze pasmo bez maksimum ma nadal określoną masę 22 400 biletów i wkład około 0,01092 p.p.; "
             "nie dodano samych śladowych wag w celu formalnego zapełnienia luk.",
             "", "## Maksimum i wejścia do bonusu", "",
             "| Rodzina | Masa wejść do bonusu, bez zmian | Bilety maksimum | Udział w całej masie maksimum |",
             "|---|---:|---:|---:|", "| Baza | — | 62 500 | 50% |",
             "| 8 FS | 4 679 041 094 | 31 250 | 25% |",
             "| 10 FS | 286 875 670 | 18 750 | 15% |",
             "| 12 FS | 4 018 776 | 12 500 | 10% |", "",
             "Wszystkie trzy warianty mają rzeczywiste osiągnięcie 5000× w trakcie FS. "
             "Nowe wysokie bonusy wykorzystują część istniejącej masy swojego wariantu; nie zwiększono częstości wejść. "
             "Maksimum bonusowe przejęło połowę istniejących 125 000 biletów maksimum.",
             "", "## Odbiór i zakres weryfikacji", "",
             "1. Pełny bank ma dodatnie wagi, krok 0,1× i największą lukę " + num(after["high_largest_gap_x"], 1) + "×, poniżej celu 250× z uwzględnieniem obu brzegów.",
             "2. Niezależna kontrola potwierdziła wszystkie 18 częstości i wkładów względem planu zapisanego przed doborem wag.",
             "3. Potwierdzono dodatnią masę maksimum w bazie i osobno w 8/10/12 FS, przy łącznych 125 000 biletów.",
             "4. Każdą eksportowaną rundę odtworzono i niezależnie oceniono legalność początkowych okien bębnów, "
             "linii, ekspansji, Scatterów, usuwania, opadania, uzupełnień i wszystkich wypłat. Sprawdzono "
             "częściowe uznanie ostatniej kaskady, saldo limitu i zakończenie niewykonanych FS. Kontrola obejmuje też 100 000 możliwych ciągów symboli jednej linii i próby celowego uszkodzenia zdarzeń.",
             "5. Przeliczono pełny bank, wariancję, hit rate, zysk, koncentrację, luki i wkłady bazy/FS. "
             f'Regresje: **{regressions["suites_passed"]}/{regressions["suites_run"]} zestawów zaliczonych**. '
             "Obejmują selektor na obu granicach każdego przedziału biletów, rozliczenia HTTP i ponowienia, "
             "rzeczywiste bonusowe maksimum w prezentacji PL/EN/DE, różne prędkości, replay i wznowienie RGS. "
             "Testy prezentacji badają logikę interfejsu; nie zastępują odbioru wizualnego ani zatwierdzenia platformy.",
             "", "Dodatkowo starszy interfejs przeszedł **45/45** testów komunikatów limitu, "
             "13 scenariuszy AUTO oraz regresję efektów. Po wypakowaniu obu ZIP sprawdzono zgodność plików, "
             "wersję 0.6.0 i działanie HTTP, zwykłych rund, kaskad oraz rozliczeń. "
             "Ostatni test w rzeczywistej przeglądarce pokazał bonusowe maksimum z banku: stawka 0,50 USD, "
             "przyznane 2500,00 USD, licznik 1/8 i informacja o zakończeniu 7 niewykonanych FS. "
             "Był to wyłącznie lokalny symulator z wirtualnym saldem.",
             "", "![Rzeczywisty ekran maksimum w bonusie](bonus_cap_browser.png)",
             "", "Dwa kolejne zbudowania dały identyczne bajtowo books, LUT, index i selection. "
             "Podsumowanie mathematics zawiera zmienny czas wykonania. "
             "Oba lokalne warianty gry otrzymały ten sam silnik selekcji i bank. "
             "Materiały sources/ i historyczne dowody pozostały bez zmian. Publikacja na serwerze platformy nie była częścią tego lokalnego wdrożenia.",
             "", "## Dowody i odtworzenie", "",
             "- [Pełna niezależna weryfikacja nowego eksportu](final_verification.json)",
             "- [Pełna niezależna weryfikacja kopii odniesienia](baseline_verification.json)",
             "- [Porównanie i dokładne ułamki](COMPARISON.json)",
             "- [Wyniki regresji](regression_summary.json)",
             "- [Powtarzalność eksportu](reproducibility.json)",
             "- [Niezależna kontrola wag](independent_high_weights_review.json)",
             "- [Testy maksimum starszego interfejsu](legacy_cap_regressions.json)",
             "- [Test paczki głównej](portable/portable_check.json) i [drugiego interfejsu](legacy_portable/portable_check.json)",
             "- [Kontrola w przeglądarce](browser_smoke.json)",
             "- [Końcowa zgodność plików i paczek](DELIVERY.json)",
             "- [Nowy eksport matematyki ZIP](POLSKA_GUROM_MATH_v0_6_0_HIGH_WINS.zip)",
             "- [Gotowa gra demo ZIP](../../test-interface-any-start/POLSKA_GUROM_TESTER.zip)",
             "", "Odtworzenie banku: `python test-interface-any-start/build_math.py`. "
             "Weryfikacja: `python audit/high_wins_rebuild_2026_10_22/verify_events.py "
             "--game test-interface-any-start --bank test-interface-any-start/stake_math "
             "--output audit/high_wins_rebuild_2026_10_22/final_verification.json --acceptance`. "
             "Regresje: `python audit/high_wins_rebuild_2026_10_22/run_regressions.py`. "
             "Kompilator wymaga Pythona 3.12+, zstandard oraz wcześniejszych naturalnych świadków 12 FS wskazanych w kodzie. "
             "Nie wymaga scipy ani optymalizatora zmiennoprzecinkowego. Demo nie wymaga zstandard.", ""]
    (HERE / "RAPORT_PL.md").write_text("\n".join(text), encoding="utf-8")
    print(json.dumps({"report": str(HERE / "RAPORT_PL.md"), "book_count": after["book_count"],
                      "largest_gap_x": after["high_largest_gap_x"], "regressions_passed": regressions["passed"]}))


if __name__ == "__main__":
    main()
