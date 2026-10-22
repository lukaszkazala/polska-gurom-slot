# Audyt matematyki POLSKA GUROM v0.2 — 19.10.2026

## Wynik

Aktualna implementacja zgadza się z lokalną specyfikacją matematyczną. Świeże obliczenia potwierdzają nominalne 96,00% RTP, częstość bonusu, 20 linii, wszystkie wypłaty, kolejność Scatter/ekspansja, brak retriggerów oraz rozliczenie limitu. Nie oznacza to gotowości do publikacji w Stake Engine: model wypłat zawiera setne stawki, a sufit 5000× jest astronomicznie rzadki. Ocena ich zgodności z aktualnymi kryteriami platformy należy do części audytu oficjalnych wymagań.

Nie zmieniano implementacji ani poprzednich wyników. Wszystkie nowe pliki zapisano w niniejszym katalogu. Poprzednich raportów nie używano jako dowodu aktualności: histogramy oraz walidację obliczono ponownie od zera; dopiero potem wykonano porównanie ze starymi histogramami.

## Ustalenia wymagające rozwiązania przed integracją

### P1 — rozliczenie generuje wypłaty niebędące wielokrotnością 0,10×

- Źródło: `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/polska_gurom_v0_2/polska_gurom/config.py:10`, tabela `:30`–`:31`, sumowanie i ekspozycja wyniku `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/polska_gurom_v0_2/polska_gurom/game.py:173`–`:181` oraz `:206`–`:220`.
- Świeży pełny histogram wykazuje 7 808 220 / 60 466 176 = 216895/1679616 = **12,913368293705227% wszystkich rund**, które nie uruchamiają bonusu i kończą się wypłatą w setnych niepodzielnych przez dziesięć. Jest to dolne ograniczenie dla całego modelu, bez potrzeby analizowania końcowej reszty wypłat bonusowych.
- Przykłady wypłat bez bonusu: 0,32×, 0,48×, 0,64×, 0,75×, 0,82×, 0,92×, 0,96×. Naturalna runda `game.play_round(random.Random(17))` daje 0,32×: linie 13 i 15 płacą po 0,16× za L1×3. Seed 0 daje 2,66×, seed 16 daje 1,25×.
- Dowód: `extra_checks.json`, sekcja `untriggered_rounds_payout_hundredths_not_divisible_by_ten`; `test_results.json`, sekcja `payout_hundredths_not_divisible_by_ten_witnesses`.
- Skutek: jeżeli obowiązujący walidator Stake wymaga `payoutMultiplier % 10 == 0` w skali 100, obecne wyniki są niezgodne. Samo przemnożenie jednostek nie zachowa znaczenia wypłaty; samo zaokrąglenie zmieni RTP i pełny rozkład. Rozwiązanie wymaga jawnej zmiany matematyki lub potwierdzonej obsługi dokładności 0,01× przez docelowy format.

### P1/P2 — matematycznie osiągalne 5000× jest praktycznie nieobecne w rozkładzie

- Źródło limitu: `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/polska_gurom_v0_2/polska_gurom/config.py:9`–`:11`; implementacja limitu `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/polska_gurom_v0_2/polska_gurom/game.py:206`–`:220`.
- Osiągalność potwierdza świeżo uruchomiony test `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/polska_gurom_v0_2/tests/test_game.py:372`–`:388`: 50,22× + 12 × 714× = 8618,22× surowo, dokładnie 5000× po limicie. Świadek wykorzystuje prawidłowe okna rzeczywistych pasków, ale wymusza kolejne wyniki; nie stanowi dowodu rozsądnej częstości.
- Świeże, skierowane na zewnątrz obliczenie Decimal/Chernoff daje **P(T ≥ 5000×) ≤ 1,2495723306290231·10⁻⁴⁷**. Dla miliona niezależnych naturalnych rund prawdopodobieństwo choć jednego takiego trafienia jest ≤ 1,2495723306290231·10⁻⁴¹ (granica sumy). To wynik analityczny; nie twierdzenie o zaobserwowanym trafieniu w symulacji.
- Osobny rachunek w `extra_checks.py`, z tym samym świeżym histogramem i arytmetyką Decimal, daje **P(T ≥ 1000×) ≤ 1,901661487749514·10⁻⁹**. Nawet 1000× jest zatem rzadsze niż około raz na 525,85 mln rund. Ta granica jest konserwatywna; rzeczywista częstość może być znacznie mniejsza.
- Maksymalna wypłata bez uruchomienia bonusu to 104,55×, zatem nieuwzględnienie niebonusowych rund w MGF progów 1000× i 5000× jest prawidłowe.
- Dowód: `math_validation.json`, sekcja `cap_bound`; niezależne powtórzenie i próg 1000× w `extra_checks.json`, `independent_decimal_chernoff_probability_upper_bounds`.
- Skutek: sam zielony test limitu nie oznacza zgodności z kryteriami częstotliwości maksymalnej wygranej lub jakości rozkładu. Waga P1, jeśli aktualne kryterium akceptacji wymaga reprezentatywnego max win; P2 jako ryzyko projektu i deklarowanej największej wygranej. Zmiana wag w bibliotece wyników, aby sztucznie zwiększyć tę częstość, zmieni opublikowaną matematykę i wymaga ponownej kalibracji.

## Faktycznie wykonana weryfikacja

1. Odczytano `config.py`, `game.py`, `theory.py`, narzędzia budowy/walidacji, oba pliki testów, README, GDD, specyfikację matematyczną i PAR sheet.
2. Uruchomiono ponownie **20/20 istniejących testów** za pomocą `run_readonly_tests.py`, bez zapisu do `verification/`. Zawierają one m.in. wszystkie 100 000 sekwencji pięciu symboli, zweryfikowane wobec niezależnego prefiksowego orakla, wszystkie linie, granicę całkowitoliczbowego losu ekspansji, 8/10/12 FS bez retriggerów, kolejność Scatter/ekspansja, osiągalny limit i pełną deterministyczność historii dla seedów 123/124.
3. Ponownie zbudowano pełny rozkład wszystkich **36⁵ = 60 466 176 naturalnych układów** oraz wszystkich trzech stanów wymuszonej ekspansji za pomocą istniejącego narzędzia `build_distribution.py` i aktualnego kodu konfiguracji. Czas: około 48 s. Nowe dane: `joint_counts.npz`, `distribution_summary.json`.
4. Narzędziem `verify_math.py` ponownie sprawdzono konfigurację, masę i nieujemność histogramów, rozkład Scatterów, niezależne marginalne EV, momenty wymierne i zależność wypłaty bazy od liczby FS. Nowy raport: `math_validation.json`.
5. Niezależnie porównano 1000 naturalnych plansz bazowych i 3000 odpowiadających im stanów FS z wymuszoną ekspansją, między rzeczywistym silnikiem i skalarnym oraklem narzędzia. Wszystkie zgodne.
6. Obliczono aktualne reszty wypłat modulo 10 i świadków rzeczywistych seedów oraz odrębne granice Chernoffa dla 1000× i 5000×. Dane: `extra_checks.json`, `test_results.json`.
7. Dopiero po odtworzeniu porównano wszystkie cztery nowe histogramy z poprzednimi — identyczne. Odcisk aktualnej konfiguracji: `d79c6643b616c077afe91803cb0b96a65a7a7ef004b4d51416dad18570958148`.
8. Agent prowadzący uruchomił dodatkowo rzeczywisty silnik dla 100 000 rund, seed 20261019: RTP 96,28928%, empiryczny normalny przedział 95% [93,1645700127%; 99,4139899873%], dodatnia wypłata 29,756%, 512 bonusów, największa wypłata 304,76× i zero osiągnięć limitu. Wynik zgodny z teorią w granicach szumu próbkowania; raport `simulation_engine_100k.json`. Jest to dodatkowy smoke test, bez dowodu eksportu ani akceptacji platformy.

Jeden z istniejących testów odczytuje poprzedni raport matematyczny; jego przejście jest wyłącznie testem regresji. Świeże wyniki enumeracji i walidacji stanowią osobny, aktualny dowód.

## Potwierdzone liczby i reguły

| Wielkość | Świeży wynik |
|---|---:|
| RTP przed limitem | 95,99999998267222% |
| RTP bazowe | 73,52578638344849% |
| Bonus w RTP | 22,474213599223736% |
| Górna granica utraty RTP przez limit | 5,20655137762093·10⁻⁴⁶ stawki/rundę |
| Dodatnia wypłata | 29,70869532083524% |
| Wypłata powyżej stawki | 17,88952361085797% |
| Dodatnia wypłata poniżej stawki | 11,64221795669698% |
| Bonus | 0,5087770061728395% = raz na 196,549763 rundy |
| Średnia liczba FS na bonus | 8,090047393364928 |
| Średnia wypłata aktywowanego bonusu | 44,17301357284393× |
| SD pełnej rundy przed limitem | 5,13802976275141× |
| Maksymalny FS | 714× |
| Maksymalna runda przed limitem | 8618,22× |
| Limit końcowy | 5000× |

Wszystkie 20 linii jest zawsze aktywnych; opłaca się najwyższą jedną interpretację Wild na linii; wypłaty są mnożnikami całkowitej stawki, bez ponownego dzielenia przez 20. Scattery są liczone przed ekspansją i nie otrzymują mnożnika ×4. Ekspansja jest jednostajnym wyborem bębna 2/3/4, niezależnym od planszy, ze szansą 216905037/1000000000. Nie ma retriggerów. Silnik rozdziela surowe należności od faktycznie zaliczonych kredytów po wykorzystaniu limitu.

## Granice tego audytu

Nie uruchamiano produkcyjnego SDK Stake ani generatora opublikowanej biblioteki wyników, bo ten podprojekt ich nie zawiera. Lokalne `random.Random` jest deterministyczne; nie jest to dowód integracji z losowaniem/platformą Stake. README `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/polska_gurom_v0_2/README.md:58`–`:60` sam wskazuje tę granicę. Nie testowano płatności walutowych ani frontendu w tym podzadaniu. Dodatkowej symulacji 100 tys. rund nie używano do oceny rzadkich maksimów; pełna enumeracja i analityczne granice odpowiadają na te pytania dokładniej.
