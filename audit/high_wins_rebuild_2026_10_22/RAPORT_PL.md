# Odbiór przebudowy wysokich wygranych — 22.10.2026

Wersja: **0.6.0-high-wins**. Punkt odniesienia: **0.5.0-any-start**.

**Wynik: lokalna przebudowa banku i wag wykonana, pięć warunków decyzji spełnionych.** Wszystkie wyniki poniżej pochodzą z pełnego przeliczenia opublikowanych wag i zdarzeń. Weryfikacja nie jest akceptacją zewnętrznej platformy. Uruchomiony wcześniej serwer należy uruchomić ponownie, aby wczytał nową wersję.

Zachowano bębny, tabelę wypłat, linie od dowolnego bębna, kaskady, koszt 1×, krok 0,1×, bonusy 8/10/12 FS, mnożnik linii 4× i ekspansję Wildów. W konfiguracji zmieniono wyłącznie numer matematyki. Nowe receptury wskazują legalne losowania; nie poprawiają kwot ani zdarzeń po ocenie planszy. Prawdopodobieństwa końcowe wynikają z wag pełnych rund.

## Porównanie pełnych rozkładów

| Parametr | 0.5.0-any-start | 0.6.0-high-wins |
|---|---:|---:|
| Pełne rundy z dodatnią wagą | 100049 | 100343 |
| Dokładne RTP | 24/25 | 24/25 |
| Limit całej rundy | 5000× | 5000× |
| Łączna częstość maksimum | 1:8 000 000 | 1:8 000 000 |
| Rundy ≥500× | 25 | 319 |
| Różne kwoty ≥500× | 19 | 297 |
| Największa luka 500×–5000×, łącznie z brzegami | 1 016,5× | 98,6× |
| Częstość ≥500× | 1:27 958,53 | 1:47 374,04 |
| Wkład ≥500× do RTP [p.p.] | 2,44355542032 | 2,44355542032 |
| Wkład maksimum do RTP [p.p.] | 0,0625 | 0,0625 |
| Wkład wypłat <500× do RTP [p.p.] | 93,55644457968 | 93,55644457968 |
| Wkład bazy do RTP [p.p.] | 45,60774144 | 44,71875350 |
| Wkład FS do RTP [p.p.] | 50,39225856 | 51,28124650 |
| Wariancja wypłaty [stawka²] | 99,023619919 | 111,432972492 |
| Odchylenie standardowe [stawka] | 9,951061246 | 10,556181719 |
| Hit rate: wypłata >0 [%] | 15,62269192 | 15,63839395 |
| Częstość zysku: wypłata >1× [%] | 9,80640007 | 9,81536902 |
| Udział największego rekordu we wkładzie ≥500× [%] | 21,407451 | 6,278995 |
| Udział 5 największych rekordów we wkładzie ≥500× [%] | 62,728388 | 18,825609 |

**Istotny kompromis:** przy tym samym budżecie RTP częstotliwość ≥500× maleje o 40,9835%, ponieważ większa część tego budżetu trafia do wyższych pasm. Zwiększa się różnorodność, ale ta wersja nie obiecuje częstszych wysokich wygranych ani poprawy krótkich sesji. Przesunięcie RTP z wypłat <500× do ≥500× wynosi dokładnie **0 p.p.**. Podział zwrotu między bazą i FS zmienia się jawnie zgodnie z tabelą.

## Docelowe pasma zapisane przed doborem wag

Przyjęto 18 pasm po 250× oraz osobne maksimum. Udziały RTP pasm bez maksimum maleją w stosunku 4/5, a cel częstości obliczono z budżetu i środka pasma. Każde pasmo ma dokładną docelową masę biletów, dopuszczalne odchylenie wkładu RTP wynosi 1%. W każdym paśmie podział masy to 40% baza, 30% 8 FS, 20% 10 FS, 10% 12 FS, z resztami całkowitoliczbowymi w 12 FS. Końcowy sumaryczny wkład ≥500× jest zachowany dokładnie, bez tolerancji.

| Pasmo × stawki | Bilety: cel = wynik | Częstość 1:N | Docelowe RTP [p.p.] | Wynik RTP [p.p.] |
|---|---:|---:|---:|---:|
| [500; 750) | 7 759 154 | 128 880,03 | 0,4849471146 | 0,4849470753 |
| [750; 1000) | 4 433 802 | 225 540,07 | 0,3879576917 | 0,3879576826 |
| [1000; 1250) | 2 758 810 | 362 475,13 | 0,3103661534 | 0,3103661464 |
| [1250; 1500) | 1 805 767 | 553 781,30 | 0,2482929227 | 0,2482929180 |
| [1500; 1750) | 1 222 365 | 818 086,25 | 0,1986343382 | 0,1986343472 |
| [1750; 2000) | 847 507 | 1 179 931,26 | 0,1589074705 | 0,1589074839 |
| [2000; 2250) | 598 240 | 1 671 569,94 | 0,1271259764 | 0,1271259825 |
| [2250; 2500) | 428 214 | 2 335 280,96 | 0,1017007811 | 0,1017007900 |
| [2500; 2750) | 309 945 | 3 226 378,87 | 0,0813606249 | 0,0813606193 |
| [2750; 3000) | 226 395 | 4 417 058,68 | 0,0650884999 | 0,0650884906 |
| [3000; 3250) | 166 627 | 6 001 428,34 | 0,0520707999 | 0,0520708003 |
| [3250; 3500) | 123 427 | 8 101 955,00 | 0,0416566400 | 0,0416566334 |
| [3500; 3750) | 91 932 | 10 877 605,19 | 0,0333253120 | 0,0333253241 |
| [3750; 4000) | 68 801 | 14 534 672,46 | 0,0266602496 | 0,0266602574 |
| [4000; 4250) | 51 705 | 19 340 489,31 | 0,0213281997 | 0,0213282059 |
| [4250; 4500) | 39 000 | 25 641 025,64 | 0,0170625597 | 0,0170625758 |
| [4500; 4750) | 29 514 | 33 882 225,38 | 0,0136500478 | 0,0136500527 |
| [4750; 5000) | 22 400 | 44 642 857,14 | 0,0109200382 | 0,0109200347 |
| 5000 | 125000 | 8 000 000 | 0,0625 | 0,0625 |

Szczegółowy, dokładny plan: [tuning_targets.json](tuning_targets.json). Receptury są dobierane do pasm, a dodatnie wagi realizują powyższe częstości i wkłady. Najrzadsze pasmo bez maksimum ma nadal określoną masę 22 400 biletów i wkład około 0,01092 p.p.; nie dodano samych śladowych wag w celu formalnego zapełnienia luk.

## Maksimum i wejścia do bonusu

| Rodzina | Masa wejść do bonusu, bez zmian | Bilety maksimum | Udział w całej masie maksimum |
|---|---:|---:|---:|
| Baza | — | 62 500 | 50% |
| 8 FS | 4 679 041 094 | 31 250 | 25% |
| 10 FS | 286 875 670 | 18 750 | 15% |
| 12 FS | 4 018 776 | 12 500 | 10% |

Wszystkie trzy warianty mają rzeczywiste osiągnięcie 5000× w trakcie FS. Nowe wysokie bonusy wykorzystują część istniejącej masy swojego wariantu; nie zwiększono częstości wejść. Maksimum bonusowe przejęło połowę istniejących 125 000 biletów maksimum.

## Odbiór i zakres weryfikacji

1. Pełny bank ma dodatnie wagi, krok 0,1× i największą lukę 98,6×, poniżej celu 250× z uwzględnieniem obu brzegów.
2. Niezależna kontrola potwierdziła wszystkie 18 częstości i wkładów względem planu zapisanego przed doborem wag.
3. Potwierdzono dodatnią masę maksimum w bazie i osobno w 8/10/12 FS, przy łącznych 125 000 biletów.
4. Każdą eksportowaną rundę odtworzono i niezależnie oceniono legalność początkowych okien bębnów, linii, ekspansji, Scatterów, usuwania, opadania, uzupełnień i wszystkich wypłat. Sprawdzono częściowe uznanie ostatniej kaskady, saldo limitu i zakończenie niewykonanych FS. Kontrola obejmuje też 100 000 możliwych ciągów symboli jednej linii i próby celowego uszkodzenia zdarzeń.
5. Przeliczono pełny bank, wariancję, hit rate, zysk, koncentrację, luki i wkłady bazy/FS. Regresje: **18/18 zestawów zaliczonych**. Obejmują selektor na obu granicach każdego przedziału biletów, rozliczenia HTTP i ponowienia, rzeczywiste bonusowe maksimum w prezentacji PL/EN/DE, różne prędkości, replay i wznowienie RGS. Testy prezentacji badają logikę interfejsu; nie zastępują odbioru wizualnego ani zatwierdzenia platformy.

Dodatkowo starszy interfejs przeszedł **45/45** testów komunikatów limitu, 13 scenariuszy AUTO oraz regresję efektów. Po wypakowaniu obu ZIP sprawdzono zgodność plików, wersję 0.6.0 i działanie HTTP, zwykłych rund, kaskad oraz rozliczeń. Ostatni test w rzeczywistej przeglądarce pokazał bonusowe maksimum z banku: stawka 0,50 USD, przyznane 2500,00 USD, licznik 1/8 i informacja o zakończeniu 7 niewykonanych FS. Był to wyłącznie lokalny symulator z wirtualnym saldem.

![Rzeczywisty ekran maksimum w bonusie](bonus_cap_browser.png)

Dwa kolejne zbudowania dały identyczne bajtowo books, LUT, index i selection. Podsumowanie mathematics zawiera zmienny czas wykonania. Oba lokalne warianty gry otrzymały ten sam silnik selekcji i bank. Materiały sources/ i historyczne dowody pozostały bez zmian. Publikacja na serwerze platformy nie była częścią tego lokalnego wdrożenia.

## Dowody i odtworzenie

- [Pełna niezależna weryfikacja nowego eksportu](final_verification.json)
- [Pełna niezależna weryfikacja kopii odniesienia](baseline_verification.json)
- [Porównanie i dokładne ułamki](COMPARISON.json)
- [Wyniki regresji](regression_summary.json)
- [Powtarzalność eksportu](reproducibility.json)
- [Niezależna kontrola wag](independent_high_weights_review.json)
- [Testy maksimum starszego interfejsu](legacy_cap_regressions.json)
- [Test paczki głównej](portable/portable_check.json) i [drugiego interfejsu](legacy_portable/portable_check.json)
- [Kontrola w przeglądarce](browser_smoke.json)
- [Końcowa zgodność plików i paczek](DELIVERY.json)
- [Nowy eksport matematyki ZIP](POLSKA_GUROM_MATH_v0_6_0_HIGH_WINS.zip)
- [Gotowa gra demo ZIP](../../test-interface-any-start/POLSKA_GUROM_TESTER.zip)

Odtworzenie banku: `python test-interface-any-start/build_math.py`. Weryfikacja: `python audit/high_wins_rebuild_2026_10_22/verify_events.py --game test-interface-any-start --bank test-interface-any-start/stake_math --output audit/high_wins_rebuild_2026_10_22/final_verification.json --acceptance`. Regresje: `python audit/high_wins_rebuild_2026_10_22/run_regressions.py`. Kompilator wymaga Pythona 3.12+, zstandard oraz wcześniejszych naturalnych świadków 12 FS wskazanych w kodzie. Nie wymaga scipy ani optymalizatora zmiennoprzecinkowego. Demo nie wymaga zstandard.
