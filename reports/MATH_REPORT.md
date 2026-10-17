# POLSKA GUROM — raport matematyczny

**PROTOTYPE / NOT MATH-FROZEN**. Audyt i uruchomienia: 17.10.2026. Nowa implementacja / rekonstrukcja z jawnymi założeniami. Wszystkie kwoty brutto w × TOTAL BET, B = 1.

## Wynik i zakres

Model działa i pozwala odtworzyć pełną rundę. **Nie spełnia celu RTP ani hit frequency.** Dokładne RTP przed cap wynosi **80,5416641942%**, a hit base z 1M to **13,8555%**. Parametry nie zostały dostrojone. Nie wykonano Math Freeze, frontendu, SDK/RGS run, wag books, płatności ani publikacji.

Katalog zastano pusty; nie było AGENTS.md, oryginalnego kodu/pasków, testów ani dokumentacji. Nie istniał katalog sources/. Historyczne liczności, kwoty i Charge 25% wykorzystano jako parametry prototypowe. Paski pogrupowane według ID oraz 20 konkretnych linii to nowe jawne założenia, nie dowód odtworzenia v0.1. Reguły, cele, parametry, dane historyczne i nierozstrzygnięte kwestie rozdzielono w GDD.

## Cel → wynik → metoda → odchylenie → interpretacja


| Cel | Wynik | Metoda | Odchylenie | Interpretacja |
|---|---|---|---|---|
| Total RTP 96%; zakres 95,5–96,5% | 80,54166419% przed cap | EXACT | -15,458336 pp względem 96% | Poza zakresem; cap pomijalnie obniża wynik |
| Base ≈ 73,5 pp | 74,45299832 pp | EXACT; także po cap | 0,952998 pp | Blisko założenia orientacyjnego |
| Bonus ≈ 22,5 pp | 6,08866588 pp przed cap | EXACT | -16,411334 pp | Główna luka w RTP |
| Hit base 25–30% | 13,8555% | MONTE CARLO 1M | -11,1445 pp do dolnej granicy | Stosy skupiają wygrane na mniejszej liczbie rund |
| Bonus 1/150–250; środek 1/200 | 1/196,549763 | EXACT | -3,450237 rund do 200 | Cel częstości spełniony |
| Medium-high | s² = 24,412779; s = 4,940929 | MONTE CARLO 1M | Brak zatwierdzonego progu kategorii | Liczbowa charakterystyka poniżej; nazwa kategorii niecertyfikowana |
| Cap 5000× osiągalny | Raw max 12324×; paid max 5000× | EXACT: bound + świadek | 0× względem limitu | Dodatnie prawdopodobieństwo; brak trafień w 1M nie przeczy osiągalności |

## Analityka naturalnego generatora

Pełne paski i paylines: `configs/reconstruction_v0_1.json`; statystyki każdego paska: `reports/results/analysis.json`. Pięć identycznych pasków 36-stopowych, wspólnych dla base i FS, z historycznymi licznościami i nowym pogrupowanym porządkiem. Każdy stop jest równomierny; trzy pola to kolejne pozycje cykliczne. P(SC w oknie)=3/36, najwyżej jeden SC na bęben. Dla tej konfiguracji rozkład jest dwumianowy, lecz kod analityki splata faktyczne histogramy okien każdego bębna.


| Wielkość | Wartość | Klasyfikacja |
|---|---|---|
| P(3 SC) | 0,486271862% | EXACT |
| P(4 SC) | 0,022103266% | EXACT |
| P(5 SC) | 0,000401878% | EXACT |
| P(bonus) | 211/41472 = 0,508777006% | EXACT |
| E[liczba FS \| bonus] | 8,090047393 | EXACT |
| E[liczba FS na rundę] | 0,041160301 | EXACT |
| Średnia wypłata FS | 1,479256891× | EXACT przed cap |
| E[wypłata bonusu \| trigger] | 11,967258352× | EXACT przed cap |
| Wymagana średnia wypłata bonusu dla 22,5 pp | 44,223696682× | EXACT cel, nie wynik gry |
| Wymagana średnia wypłata FS dla 22,5 pp | 5,466432337× | EXACT cel |
| Wkład Scatter base+FS | 0,629720556 pp | EXACT przed cap |

RTP bonusu = P(bonus) · E[wypłata bonusu | trigger] = E[liczba FS na rundę] · E[wypłata FS]. Linie mogą być skorelowane; liniowości użyto tylko do średnich. Charge oceniany jest po zliczeniu naturalnych Scatterów; Scatter payout w FS nie przyznaje kolejnych FS.


| Charge | Wkład bonusu do RTP | Total RTP przed cap | Metoda |
|---|---|---|---|
| 0% | Bonus RTP 3,064508 pp | 77,51750613% | EXACT kontrfaktyczne |
| 25% | Bonus RTP 6,088666 pp | 80,54166419% | EXACT kontrfaktyczne |
| 50% | Bonus RTP 9,112824 pp | 83,56582226% | EXACT kontrfaktyczne |
| 75% | Bonus RTP 12,136982 pp | 86,58998032% | EXACT kontrfaktyczne |
| 100% | Bonus RTP 15,161140 pp | 89,61413838% | EXACT kontrfaktyczne |

Średnia wypłata FS bez Charge = 0,744529983×; warunkowo przy Charge = 3,683437613×. Obecne Charge dodaje do średniej FS 0,734726907×. Osiągnięcie 96% samym Charge wymagałoby 152,790409%, co jest niemożliwe. Wagi bębnów 2/3/4 są punktem startowym, a nie wyprowadzonym optimum.

## Cap i maksimum

Exact post-cap RTP: **NOT CALCULATED** jako pojedyncza dokładna wartość. Zamiast utożsamienia jej z pre-cap wyznaczono **EXACT RIGOROUS BOUND**: wypłata pojedynczego spina ≤ 1020×, średnia wypłata FS znana dokładnie, a FS są niezależne. Przez wypukłość `(x−5000)+` każdą wypłatę FS ∈ [0,M] można zastąpić zmienną M·Bernoulli(E[wypłata FS] / M), uzyskując górne ograniczenie oczekiwanej redukcji. Suma po możliwych liczbach FS i triggerach liczona jest ułamkami. To dowód ograniczenia, nie dokładne prawdopodobieństwo cap.

Górna granica ubytku RTP: **1.73299151027e-10×** (= 1.73299151027e-08 pp). Zatem przy prezentacji 10 miejsc RTP paid mieści się w **[80,5416641769%; 80,5416641943%]**. Końce zaokrąglono na zewnątrz przedziału, operując na dokładnych ułamkach; dokładne granice zapisano w JSON. Base nigdy nie osiąga cap, a bonus po cap mieści się w odpowiednim przedziale JSON; paid base+paid bonus = paid total.

Osobny, mocniejszy dowód maksimum (`scripts/verify_bounds.py`) wykazuje FS ≤ 1000×. Dla ≥3 naturalnych SC po najwyżej jednym Charge zostają ≥2 nieprzykryte SC; co najmniej jeden jest na bębnie 1–4. Pozioma linia przez niego płaci ≤2×, więc spin ≤19·50+2+20=972×. Przy <3 SC limit wynosi 20·50=1000× i jest osiągalny na stopach (31,31,31,31,31). Pełna enumeracja 243 base plansz 5 SC daje maksimum 324× przy stopach (33,33,33,33,33). Rundy 3 SC i 4 SC mają ograniczenia 9020× i 11020×; runda 5 SC ma maksimum 324 + 12·1000=12324× i je osiąga.

Świadek: base: wszystkie zatrzymania 33 oraz 12 FS: wszystkie zatrzymania 31 bez Charge. P tej konkretnej ścieżki=(3/4)^12·36^−65≈2.1931716e-103>0. Maksymalna przyznana wypłata 5000×, redukcja 7324×. `reports/max_win_witness.json` zawiera naturalne/końcowe plansze, linie i resolved settlement_trace. Wszystkie FS są rozgrywane po cap; późniejsza przyznana część wynosi 0. Ta ścieżka jest dowodem osiągalności, nie estymacją częstości wszystkich trafień cap.

## Rzeczywiste symulacje pełnych rund — MONTE CARLO

Backend `numpy-PCG64-splitstreams-v2`, Python 3.10.11, NumPy 2.2.6. Cztery osobne strumienie PCG64 dla base stops, FS stops, Charge i wyboru bębna. Charge i wagi losowane całkowitoliczbowo. Skrypt używa seed=20261017+liczba_rund; próby są odrębne. FS nie zwiększają sumy stawek. Wszystkie osiągalne FS są rozgrywane.


| Rundy | Seed | Stawka B | Wypłata B | Raw RTP=paid RTP | Base pp | Bonus pp | Scatter pp | 95% CI |
|---|---|---|---|---|---|---|---|---|
| 10000 | 20271017 | 10000 | 6943,80 | 69,438000% | 63,655500 | 5,782500 | 0,590000 | 62,10078%–76,77522% |
| 100000 | 20361017 | 100000 | 79858,85 | 79,858850% | 74,435750 | 5,423100 | 0,611000 | 76,94131%–82,77639% |
| 1000000 | 21261017 | 1000000 | 805307,40 | 80,530740% | 74,116355 | 6,414385 | 0,627800 | 79,56234%–81,49914% |

Scatter to podzbiór base+bonus, nie dodatkowa składowa sumowana drugi raz. W każdej próbie redukcja cap=0, osiągnięcia cap=0; dlatego w tych próbach raw=paid. JSON zachowuje oddzielne pola i dokładne sumy w jednostkach 1/100.


| Rundy | s² pełnej rundy | s | Hit base | Hit round | X>1 | 0<X<1 | X=1 | Max X |
|---|---|---|---|---|---|---|---|---|
| 10000 | 14,014168 | 3,743550 | 13,4300% | 13,4300% | 11,0200% | 2,0200% | 0,3900% | 153,00× |
| 100000 | 22,158310 | 4,707261 | 13,9870% | 13,9870% | 11,4790% | 2,0370% | 0,4710% | 511,20× |
| 1000000 | 24,412779 | 4,940929 | 13,8555% | 13,8555% | 11,3757% | 1,9921% | 0,4877% | 755,50× |

Hit base to wypłata base>0 przed FS — robocza definicja celu 25–30%. Hit round to wypłata całej rundy>0. Są tutaj równe, ponieważ każdy trigger ma dodatni Scatter payout.


| Rundy | Bonusy | 1/p | E[wypłata bonusu \| bonus] | FS | E[liczba FS \| bonus] | Charge/FS | Charge/bonus |
|---|---|---|---|---|---|---|---|
| 10000 | 53 | 188,67925 | 10,910377× | 426 | 8,037736 | 24,64789% | 1,981132 |
| 100000 | 492 | 203,25203 | 11,022561× | 3982 | 8,093496 | 25,81617% | 2,089431 |
| 1000000 | 5192 | 192,60401 | 12,354362× | 41956 | 8,080894 | 25,05005% | 2,024268 |

| Rundy | Charge razem | Bęben 2: n / udział | Bęben 3: n / udział | Bęben 4: n / udział |
|---|---|---|---|---|
| 10000 | 105 | 31 / 29,5238% | 30 / 28,5714% | 44 / 41,9048% |
| 100000 | 1028 | 370 / 35,9922% | 342 / 33,2685% | 316 / 30,7393% |
| 1000000 | 10510 | 3490 / 33,2065% | 3502 / 33,3206% | 3518 / 33,4729% |

Bębny 1 i 5: 0 ekspansji w każdej próbie. Teoretycznie Charge/bonus = E[liczba FS | bonus]·0,25=2,02251185; selekcja 2/3/4 po 1/3. Nie ma niezależnego losowania triggera 1/200.

## Rozkład wypłat — MONTE CARLO

Prawdopodobieństwa i wkłady do RTP dla rozłącznych przedziałów, osobno dla każdej próby.


| Przedział X | P 10k | RTP 10k pp | P 100k | RTP 100k pp | P 1M | RTP 1M pp |
|---|---|---|---|---|---|---|
| 0 | 86,570000% | 0,000000 | 86,013000% | 0,000000 | 86,144500% | 0,000000 |
| (0;1) | 2,020000% | 1,246000 | 2,037000% | 1,253800 | 1,992100% | 1,223500 |
| [1;5) | 7,830000% | 18,861500 | 7,964000% | 19,350250 | 7,893700% | 19,061775 |
| [5;20) | 2,950000% | 27,319500 | 3,266000% | 30,716350 | 3,221600% | 30,188645 |
| [20;100) | 0,610000% | 19,167000 | 0,689000% | 23,770650 | 0,716000% | 24,783465 |
| [100;500) | 0,020000% | 2,844000 | 0,030000% | 4,256600 | 0,031800% | 5,072815 |
| [500;1000) | 0,000000% | 0,000000 | 0,001000% | 0,511200 | 0,000300% | 0,200540 |
| [1000;5000) | 0,000000% | 0,000000 | 0,000000% | 0,000000 | 0,000000% | 0,000000 |
| exactly 5000 | 0,000000% | 0,000000 | 0,000000% | 0,000000 | 0,000000% | 0,000000 |

Wiersze sumują się do 100% prawdopodobieństwa i RTP danej próby. Dokładny zwrot X = 1 jest zawarty w [1;5); oddzielna częstość w tabeli powyżej nie stanowi dodatkowego przedziału.


| Ogon bonusu warunkowo na trigger | 10k | 100k | 1M |
|---|---|---|---|
| P(bonus<1×) | 26,415094% | 21,138211% | 22,476888% |
| P(bonus>20×) | 13,207547% | 17,073171% | 17,180277% |
| P(bonus>100×) | 1,886792% | 0,609756% | 1,040062% |
| P(bonus>500×) | 0,000000% | 0,000000% | 0,019260% |
| P(bonus>1000×) | 0,000000% | 0,000000% | 0,000000% |

Mianownik ogona bonusu to liczba triggerów, a wypłata to przyznana część bonusowa z wyłączeniem base. Brak obserwacji >1000× nie dowodzi zerowego prawdopodobieństwa.

## Naturalne Wildy i Scattery

EXACT: P(Wild w ustalonym polu)=1/18=5,555556%; P(≥1 Wild w oknie jednego bębna)=1/9=11,111111%. Naturalnych Wildów nie zastępujemy liczbą Wildów po Charge. Pełne dane per bęben i wszystkie rozkłady z każdej próby zapisano w JSON.


| Próba | Wild — pole base | Wild — okno base | Wild — pole FS | Wild — okno FS |
|---|---|---|---|---|
| 10000 | 5,396667% | 10,738000% | 5,790297% | 11,784038% |
| 100000 | 5,564400% | 11,114600% | 5,536581% | 11,099950% |
| 1000000 | 5,566753% | 11,127800% | 5,582674% | 11,182668% |

| Liczba SC | EXACT P | 1M base: n / P | FS w próbie 1M: n / P |
|---|---|---|---|
| 0 | 64,72278485% | 647763 / 64,776300% | 27104 / 64,601011% |
| 1 | 29,41944766% | 293365 / 29,336500% | 12422 / 29,607208% |
| 2 | 5,34899048% | 53680 / 5,368000% | 2235 / 5,327009% |
| 3 | 0,48627186% | 4983 / 0,498300% | 185 / 0,440938% |
| 4 | 0,02210327% | 208 / 0,020800% | 10 / 0,023834% |
| 5 | 0,00040188% | 1 / 0,000100% | 0 / 0,000000% |

Więcej niż 5 SC jest niemożliwe konstrukcyjnie i sprawdzane przy wczytaniu konfiguracji. FS mają mniejszą liczebność niż 1M; ich rozkład jest osobną, mniej precyzyjną estymacją.

## Wnioski o historii, Wildach i zmienności

Historyczne średnie 80,5417%,74,4530%,6,0887% odtworzono do zaokrąglenia jako **EXACT przed cap dla obecnych jawnych zasad i marginałów**. Sama zbieżność nie weryfikuje starego kodu. Hit 49,6463% i max 130× z dawnej 1M pozostają **REPORTED / UNVERIFIED**; oryginalne paski i seed są niedostępne. Obecne hit 13,8555% i max 755,5× dotyczą innych, jawnych pasków. Nie ma podstaw do przypisywania tej różnicy naprawie dawnego błędu.

Bonus wnosi za mało, ponieważ trigger występuje raz na 196,55 rundy, przyznaje średnio 8,09 FS, a obecny FS ma średnią tylko 1,47926×. Do 22,5 pp potrzeba 5,46643× na FS lub 44,22370× na uruchomiony bonus. Nawet 100% Charge nie wystarcza.

Diagnostyka **EXACT kontrfaktyczna**, bez zmiany konfiguracji: naturalne Wildy potraktowane jako blokery zamiast zastępstwa dają base RTP19,19178914%, wobec obecnych 74,45299832%; różnica 55,26120918 pp. To pokazuje silną rolę substytucji w EV, nie niezależny przyczynowy pomiar hit frequency. Po wyłączeniu wyłącznie Scatter payouts w FS Total RTP wynosiłoby 80,51676938%, spadek 0,02489481 pp. Historyczne średnie są zgodne z obecnością tego payout, lecz brak oryginalnego kodu pozostaje.

Częste małe historyczne wypłaty nie zostały niezależnie odtworzone. Możliwe przyczyny to marginały niskich symboli, Wild substitution i rozproszone okna zwiększające liczbę różnych trafiających linii; kolejność pasków decyduje o zależnościach. W obecnej grupowanej rekonstrukcji wiele linii trafia razem: 86,1445% rund nie wypłaca, 1,9921% wypłaca (0;1), a około3/8 całego RTP pochodzi z[5;20). Nie wolno traktować 20 linii jako 20 niezależnych prób.

Wariancja 24,412779 i SD 4,940929 w×B, ogon do 755,5× w 1M oraz wkład przedziałów ≥20× pokazują szeroki rozkład i duże skupienie RTP w rzadkich wypłatach. Określenie medium-high pozostaje hipotezą projektową: nie uzgodniono progu ani benchmarku, więc nie oznaczamy tej kategorii jako udowodnionej. Wartości liczbowe i histogram stanowią weryfikowalne uzasadnienie charakteru rozkładu.

95% CI: normalny przedział średniej pełnych rund, z wariancją próbkową n−1. 10k dało wynik poza nominalnym CI względem teorii (niska próba; rzadkie duże wypłaty powodują niestabilną wariancję i niedokładne pokrycie). Sprawdzono cykliczne okna, wspólne linie, LUT 100000 kombinacji i zgodność scalar/vector 2048 plansz oraz rozliczenia. 100k i 1M obejmują teoretyczne RTP swoimi CI. Nie wykryto rozbieżności zasad ani zmieniono paytable; pojedynczy 95% przedział nie ma gwarancji pokrycia, zwłaszcza dla 10k. Zgodność 1M z teorią nie wyznacza dokładnie ogona.

## Testy i odtwarzalność


Rzeczywisty wynik testów deterministycznych: `{"tests_run": 43, "failures": 0, "errors": 0, "skipped": 0, "successful": true}`. Pełny zapis `reports/results/tests.txt`, przypadki i mapowanie wymagań: `docs/TEST_PLAN.md`.


Crosscheck scalar/vector: `{"status": "PASS", "samples": 2048, "seed": 91276, "charge_choices_reel_indices": [null, 1, 2, 3], "lut_entries_from_scalar_evaluator": 100000}`.

Powtarzalność symulacji: `{"status": "PASS", "rounds": 10000, "seed": 66251, "batch_sizes": [1000, 333], "comparison": "All result fields identical except processing batch size and elapsed time"}`.

Wszystkie trzy raporty mają prawdziwe asercje sumy paid base+paid bonus, pokrycia histogramu i liczby FS zgodnej z awards. Silnik skalarny z seedem i niezależny prosty evaluator objęte są testami; świadek maksimum został faktycznie oceniony przez ten sam core.


| Element | Wersja / hash |
|---|---|
| Silnik | 0.1.0-reconstruction |
| Konfiguracja | reconstruction-v0.1-grouped-2026-10-17 |
| SHA256 parametrów | 31c72aa957b4cc761c6e68864ba40e720a436c967c0c7700b1bf1fb385cf8d99 |
| SHA256 pakietu Python  | 44b300ec91df9b8e674f0c7d168b78d0b67f183147b0b8c9081e35d44c9c5581 |
| RNG | numpy-PCG64-splitstreams-v2 / numpy.random.Generator(PCG64) |

Dokładna odtwarzalność wymaga tych samych wersji, seedu, liczby rund i konfiguracji. NumPy  backend i random.Random backend są odrębnymi algorytmami; nie oczekujemy identycznych sekwencji między nimi. Zmiana rozmiaru partii nie zmienia wyników. Nie inicjalizuje się stanu rozgrywki z poprzedniej płatnej rundy.

## Stake Engine

Aktualne oficjalne źródła odczytano 17.10.2026; odnośniki i zakres w `docs/STAKE_COMPLIANCE.md`. Naturalny generator i ewentualny przyszły ważony zestaw books to dwa różne rozkłady. Nie powstały books ani wagi, więc ważone RTP: **NOT CALCULATED / NOT APPLICABLE w tej fazie**. Nie uruchomiono SDK/RGS; nie deklarujemy zgodności publikacyjnej. Własny evaluator jest potrzebny, aby zachować wszystkie regularne interpretacje Wildów. W odczytanym bieżącym walidatorze SDK znaleziono wymóg końcowej wypłaty co 0,10×, podczas gdy model zachowuje 0,01×; niczego nie zaokrąglano. Faktycznie uruchomiony lokalny `play_round` z `random.Random`, seedem `20261017`, dał w rundzie o indeksie `147` osiągalną wypłatę **0,45×**, która nie jest wielokrotnością 0,10×. Pełny świadek i parametry odtworzenia: `reports/sdk_payout_step_witness.json`. Status względem odczytanego walidatora: **BLOCKED_BY_CURRENT_SDK_PAYOUT_STEP**. Jest to potwierdzona niezgodność kroku wypłaty z odczytaną regułą, a nie wynik wykonania SDK. Przyszła integracja wymaga przypięcia wersji SDK i rozstrzygnięcia kroku wypłat.

## Trzy niewdrożone warianty tuningu v0.2

Poniższe propozycje nie zostały zastosowane ani zmierzone. Cel pozostaje niespełniony. Każda wymaga nowej wersji pełnych pasków, oddzielnej analityki, testów, 10k/100k/1M i ponownego dowodu maksimum/cap. Nie dodajemy nowej mechaniki.


| Wariant | Obecne → proponowane | Powód i przewidywany wpływ | Ryzyko i walidacja |
|---|---|---|---|
| 1. Układ pasków przy stałych marginałach | Grupowanie z serią L1 długości 7 i Wild 33,34 → regularne stosy ≤2; Wild 8,26; P4 na 6,7; SC 35; liczności 36 bez zmian; wszystkie 5 pasków nadal wspólne | Rozproszyć trafienia i zmniejszyć jednoczesne linie; wzrost hit jest przewidywaniem. Base i bonus EV przed cap pozostaną dokładnie takie same przy tych marginałach / SC; zachowany klaster P4,P4,W umożliwia 1000× w FS | Hit nie jest gwarantowany; zmienność może spaść. Skonstruować pełne listy, potwierdzić P(bonus) bez zmian, zmierzyć hit/variance i ponownie osiągalność cap. Sam ten wariant nie naprawia RTP |
| 2. Osobne mocniejsze paski FS + Charge | Wspólne 36-stopowe W 2, L1=7 i Charge 25% → osobne FS 36-stopowe W 4, L1=5, pozostałe liczności bez zmian, Charge 75%; base bez zmian | Podnieść bonus bez zwiększenia hit base / RTP base. SC 1/36 oraz brak retriggerów pozostają; wymagany próg E[wypłata FS] ≈ 5,46643× służy jako warunek analityczny, nie przewidywany wynik kandydata | Więcej Wildów może zwiększyć hit FS i ogon, a silny Charge obniżyć różnorodność. Najpierw dokładne EV FS / Charge i rozmieszczenie SC, potem wariancja, bonusowe ogony i cap. Nie zakładać, że 4 Wildy osiągną cel |
| 3. Rebalans częstotliwości i paytable | Wspólne paski 36→33 poprzez L1 7→4 (SC 1, W 2 bez zmian); regularne paytable ×1,00 → próbnie ×0,80 w obu fazach, skala 100 pozostaje dokładna; Charge 25%→100%; Scatter 1/5/20 bez zmian | Częstszy SC po skróceniu zwiększy bonusy i naturalne marginały Wildów; redukcja tabeli ma przeciwdziałać wzrostowi base. Sama zmiana Charge nie wystarcza. Kierunek łącznego RTP wymaga obliczeń; nie obiecujemy 96% | 1/33 SC daje więcej triggerów i może podejść do granicy 1/150; hit może wzrosnąć. Wyliczyć dokładne P(bonus) i EV przed symulacją, sprawdzić krok SDK, odrzucić jeśli cel częstości/base lub osiągalność 5000 pogarsza się |

Warianty należy rozpatrywać osobno, z porównaniem zmienianych parametrów. Ze względu na niewystarczający bonus i zbyt niski hit konieczna będzie co najmniej praca nad rozkładem pasków oraz siłą bonusu; samo strojenie Charge ma udowodniony limit. Nie uruchomiono pętli optymalizacyjnych i nie wdrożono powyższych propozycji.

## Artefakty i ograniczenia

`reports/results/analysis.json`: dokładne ułamki, histogramy pasków, diagnostyka i ograniczenia. `simulation_*.json`: wszystkie metryki i sumy. `vector_scalar_crosscheck.json`, `simulation_reproducibility.json`, `tests.*`: rzeczywiste weryfikacje. `max_win_proof.json` i `reports/max_win_witness.json`: dowód i pełny trace. Raport wygenerowano przez `scripts/build_report.py` z tych plików; generator sprawdza zgodność hashy i sum.

NOT CALCULATED: dokładny pełny rozkład/wariancja/hit po cap poza MC oraz dokładna częstość cap. REPORTED / UNVERIFIED: historyczny hit, max i oryginalna implementacja. Zatwierdzenie kategorii zmienności, finalne parametry i integracja Stake pozostają pracą kolejnej fazy. Model jest sprawdzalnym prototypem; jego obecna matematyka odbiega od celów.
