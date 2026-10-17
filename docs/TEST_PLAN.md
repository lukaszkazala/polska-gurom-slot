# Plan i wynik testów matematyki POLSKA GUROM

Status modelu: **PROTOTYPE / NOT MATH-FROZEN**. Testowana jest nowa implementacja i jawna rekonstrukcja kolejności pasków, a nie potwierdzone odtworzenie historycznego evaluatora v0.1.

## Rzeczywisty wynik uruchomienia

Dnia 2026-10-17 uruchomiono `unittest.defaultTestLoader.discover('tests')` i `unittest.TextTestRunner(verbosity=2)` na rzeczywistych plikach projektu:

| Testy | Niepowodzenia | Błędy | Pominięte | Wynik | Czas testów |
|---:|---:|---:|---:|---|---:|
| 43 | 0 | 0 | 0 | OK | 1,038 s |

Surowy log: [`../reports/results/tests.txt`](../reports/results/tests.txt). Podsumowanie do automatycznego odczytu: [`../reports/results/tests.json`](../reports/results/tests.json). Są to faktyczne wyniki deterministycznych sprawdzeń, nie estymacje Monte Carlo. Czas obejmuje wykonanie testów, bez startu powłoki i interpretera.

Powtórzenie całej baterii z katalogu głównego:

```powershell
python -m unittest discover -s tests -v
```

Źródło testów: [`../tests/test_math.py`](../tests/test_math.py). Bateria używa wyłącznie biblioteki standardowej Pythona. Poniższe nazwy odnoszą się do rzeczywiście uruchomionych metod tego pliku.

## Pokrycie 26 wymaganych grup

| Nr | Wymaganie | Test lub testy |
|---:|---|---|
| 1 | Przegrana | `EvaluatorTests.test_losing_line` |
| 2 | Kombinacje 3, 4 i 5 symboli | `EvaluatorTests.test_three_four_and_five_matching_symbols` |
| 3 | Początek na pierwszym bębnie | `EvaluatorTests.test_match_must_start_on_first_reel` |
| 4 | Przerwanie kombinacji | `EvaluatorTests.test_interruption_ends_run` |
| 5 | Zastępowanie symbolu przez Wild | `EvaluatorTests.test_wild_substitution_inside_run` |
| 6 | Wild nie zastępuje Scattera | `EvaluatorTests.test_wild_does_not_substitute_scatter` |
| 7 | Początkowe Wildy i same Wildy | `EvaluatorTests.test_leading_wilds_and_all_wilds` |
| 8 | Jedna najwyższa interpretacja linii | `EvaluatorTests.test_one_highest_interpretation_per_line`, `test_equal_payout_interpretations_use_stable_symbol_order` |
| 9 | Brak sumowania 3/4/5 tego samego dopasowania | `EvaluatorTests.test_no_sum_of_three_four_five_on_same_line` |
| 10 | Kilka wygrywających linii | `EvaluatorTests.test_multiple_winning_lines_and_line_indices` |
| 11 | Jednostki TOTAL BET i konwersja stawki liniowej | `EvaluatorTests.test_total_bet_units_and_sdk_line_bet_equivalence` |
| 12 | Zawijanie indeksów pasków | `ReelAndScatterTests.test_cyclic_window_wraps_at_strip_end` |
| 13 | Dokładnie 3/4/5 Scatterów | `ReelAndScatterTests.test_exactly_three_four_five_scatters_and_free_spin_awards` |
| 14 | Przyznanie 8/10/12 FS | `ReelAndScatterTests.test_exactly_three_four_five_scatters_and_free_spin_awards` |
| 15 | Brak retriggerów | `BonusTests.test_free_spin_scatter_pays_without_retrigger`, `test_play_round_has_no_retriggers` |
| 16 | Bonus z Charge i bez niego | `BonusTests.test_free_spin_without_charge_preserves_natural_board`, `test_charge_expands_each_allowed_reel_and_only_one` |
| 17 | Ekspansja ludzkich bębnów 2/3/4 | `BonusTests.test_charge_expands_each_allowed_reel_and_only_one` |
| 18 | Zakaz ekspansji ludzkich bębnów 1/5 | `BonusTests.test_charge_rejects_reels_one_five_and_base_game` |
| 19 | Maksymalnie jeden rozszerzony bęben | `BonusTests.test_charge_expands_each_allowed_reel_and_only_one` |
| 20 | Reset ekspansji przed kolejnym FS | `BonusTests.test_charge_resets_before_next_free_spin` |
| 21 | Scatter przykryty ekspansją | `BonusTests.test_scatter_hidden_by_charge_still_pays_from_natural_board` |
| 22 | Agregacja pełnej rundy | `RoundAndCapTests.test_full_round_aggregation`, `test_round_without_bonus_has_no_free_spins` |
| 23 | Wynik poniżej, równy i powyżej 5000× | `RoundAndCapTests.test_cap_below_equal_and_above_five_thousand_total_bet`, `test_reachable_positive_probability_cap_witness` |
| 24 | Suma przyznanych składowych po cap | `RoundAndCapTests.test_paid_components_sum_after_cap`, `test_serialized_per_spin_settlement_preserves_raw_and_paid_totals` |
| 25 | Ten sam seed daje ten sam wynik | `RoundAndCapTests.test_same_seed_config_and_engine_reproduce_complete_rounds` |
| 26 | Niezależny evaluator referencyjny | `EvaluatorTests.test_reference_evaluator_exhaustive_small_alphabet`, `test_reference_evaluator_seeded_all_symbols` |

Indeksy w Pythonie są o jeden mniejsze od numerów ludzkich bębnów: Charge dopuszcza `1, 2, 3`, czyli bębny 2, 3, 4.

## Niezależność sprawdzeń evaluatora

Funkcja referencyjna `reference_line` nie skanuje kolejnych celów symbolicznych algorytmem silnika. Enumeruje wszystkie przypisania regularnych symboli do pozycji Wildów, a następnie ocenia zwykłą serię identycznych, już literalnych symboli od lewej. Z otrzymanych wypłat wybiera najwyższą. Rozstrzyga remis według stabilnej kolejności symboli matematycznych.

Porównanie obejmuje:

- wszystkie 1024 linie długości pięciu nad alfabetem `L1, P3, SCATTER, WILD`; dla linii samych Wildów referencja przechodzi przez wszystkie `8^5` przypisań;
- 1000 dodatkowych linii nad wszystkimi dziesięcioma identyfikatorami, z seedem `20261017`;
- osobne jawne asercje wszystkich czterech przykładów z wymagań, w tym sporu krótszej kombinacji premium z dłuższą low;
- pojedynczy wynik na linię i brak podwójnego liczenia podkombinacji.

Robocza konwencja daje: `W W P3 P3 L1` → 5,50×, `W W W L1 L1` → 2,50×, `W W W W W` → 50×, `W W SCATTER P4 P4` → 0. Dodatkowo `W W W W L1` → 10× jako cztery P4. Kwoty dotyczą jednej linii i są w mnożnikach TOTAL BET.

## Paski, Scatter, RNG i pełny ślad rundy

`test_historical_counts_are_preserved_but_order_is_explicit` sprawdza długość 36, wszystkie liczności historyczne oraz końcowe pozycje `WILD, WILD, SCATTER`. To świadomy test konkretnej wersji rekonstrukcji. Zmiana pasków w nowej wersji wymaga odpowiedniej aktualizacji tego testu, konfiguracji i dokumentacji.

`test_at_most_one_visible_scatter_per_reel` przechodzi przez wszystkie zatrzymania każdego paska. Na każdym pasku potwierdza 33 okna bez Scattera i 3 okna z jednym Scatterem, zatem nie więcej niż pięć Scatterów na całej planszy. Testy sprawdzają także błędne zatrzymania i jawne odrzucanie liczby Scatterów spoza 0–5.

`QueueRng` dostarcza jawne liczby całkowite z kontrolą granic losowania. Pozwala sprawdzić wszystkie cztery wyniki decyzji Charge przy `p=1/4`, wszystkie sześć wyników próbnego nierównomiernego wyboru `(1, 2, 3)` i reset ekspansji w dwóch kolejnych prawdziwych wywołaniach `play_spin`. Nie trzeba polegać na statystycznym przybliżeniu, aby sprawdzić te rozkłady.

Test powtarzalności porównuje pełne serializowane wyniki 300 rund z dwóch generatorów `random.Random(123456789)`. Obejmuje plansze, zatrzymania, bonusy, Charge oraz rozliczenie. Osobny test sprawdza brak ukrytego stanu zależnego od poprzedniej płatnej rundy. Determinizm dotyczy tej samej konfiguracji i wersji wykonania; zmiana wersji generatora lub silnika wymaga ponownej walidacji.

## Cap i konstruktywny dowód osiągalności

`test_reachable_positive_probability_cap_witness` korzysta wyłącznie z dozwolonych zatrzymań bieżących pasków:

1. Base: zatrzymania `(33, 33, 33, 33, 33)` dają pięć naturalnych Scatterów i 12 FS.
2. Każdy z dwunastu FS: zatrzymania `(31, 31, 31, 31, 31)` oraz brak Charge.
3. Pełna surowa wypłata wynosi 1 232 400 jednostek, czyli 12 324×. Wypłata przyznana wynosi 500 000 jednostek, czyli 5000×; redukcja wynosi 7324×.

Prawdopodobieństwo tego konkretnego przebiegu wynosi `(1/36)^(5·13) · (3/4)^12 > 0`. Dowodzi to osiągalności cap, bez twierdzenia, że jest to najkrótszy lub najbardziej prawdopodobny taki przebieg.

`test_all_awarded_spins_are_simulated_after_cap` potwierdza rozegranie wszystkich 12 FS. `test_serialized_per_spin_settlement_preserves_raw_and_paid_totals` sprawdza 13 pozycji śladu, końcowe sumy surowe i przyznane, sumę składowych line/scatter oraz ostatni FS z dodatnią wypłatą surową i zerową przyznaną po wykorzystaniu limitu. Nie stosuje się osobnego cap dla każdego FS.

## Dodatkowa walidacja i ograniczenia

Testy odrzucają niepełne albo retriggerowane ślady rund, nieznane symbole, błędny rozmiar planszy, ujemne kwoty rozliczenia, powtarzające się linie, błędne rzędy, liczbę bębnów inną niż pięć, niedozwolone skupienie Scatterów, niepełny paytable, zmianę zatwierdzonych nagród 8/10/12 FS, niepoprawne wagi Charge i cap inny niż 5000×. Hash konfiguracji pozostaje stabilny przy powtórnym odczycie i zmienia się po zmianie parametrów matematycznych.

Test konwersji jednostek sprawdza dokładną równość wymierną dla wszystkich 24 pozycji paytable: mnożnik stawki liniowej razy `1/20` jest równy pierwotnej wypłacie w TOTAL BET. To test przeliczenia jednostek, a nie certyfikacja integracji z zewnętrznym SDK.

Zaliczenie tej baterii potwierdza sprawdzane zachowania silnika. Nie dowodzi osiągnięcia RTP 96%, hit frequency 25–30%, klasy zmienności ani zgodności produkcyjnej ze Stake Engine. Walidację analityki, wektorowego symulatora, rozkładów Monte Carlo i ograniczeń SDK dokumentują osobne wyniki i raport matematyczny. Bateria nie enumeruje wszystkich `36^5` plansz ani wszystkich pełnych rund.
