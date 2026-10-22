# POLSKA GUROM — poprawiona matematyka v0.2

Kompletna, działająca wersja prototypu matematycznego. Zachowuje planszę 5×3, 20 stałych linii, 8/10/12 darmowych obrotów, maksymalnie jeden rozwinięty Wild na bębnie 2/3/4 i limit 5000× całej rundy. Nie zawiera frontendu, płatności ani integracji ze Stake Engine.

## Wynik

| Parametr | Wartość |
|---|---:|
| Nominalne RTP | **96,00%** |
| RTP przed limitem, obliczenie wymierne | 95,99999998267222% |
| Udział gry podstawowej | 73,5257863834% |
| Udział bonusu | 22,4742135992% |
| Runda z dodatnią wypłatą | 29,7086953208% |
| Wypłata przewyższająca stawkę | 17,8895236109% |
| Bonus | średnio raz na 196,55 rundy |
| Średnia wypłata uruchomionego bonusu | 44,1730× stawki |
| Odchylenie standardowe pełnej rundy | 5,1380× stawki |
| Limit pełnej rundy | 5000× |

Runda oznacza płatny obrót oraz wszystkie przyznane mu darmowe obroty. Dodatnia wypłata może być mniejsza od stawki. Limit jest osiągalnym sufitem, a nie typową nagrodą. Wpływ limitu na RTP jest mniejszy niż 10⁻⁴⁰ stawki na płatną rundę; wynik 96,00% pozostaje poprawny po ograniczeniu wypłaty. Szczegóły i dokładna granica są w `verification/math_validation.json`.

## Co zmieniono

- Zestaw 20 ścieżek ma dziewięć wspólnych początków na pierwszych trzech bębnach, zachowuje trzy poziome oraz obie linie V. Wszystkie linie są odrębne i zawsze aktywne. Trafienia częściej występują wspólnie, zamiast bardzo często dawać pojedynczy mały zwrot.
- Trzy symbole L1 płacą 0,16× całkowitej stawki zamiast 0,20×; pozostała podstawowa tabela i bębny pozostały takie same.
- Darmowe obroty płacą **×4 za linie**, bez mnożenia Scatterów.
- Szansa HUSSAR CHARGE wynosi dokładnie `216905037/1000000000`, czyli 21,6905037% na darmowy obrót. Wybór jednego z bębnów 2, 3, 4 jest równomierny i niezależny od planszy.
- Rozliczenia są w całkowitych jednostkach 0,01× stawki. Wynik zawiera każdą płatną linię, opłacone pola, stany planszy przed/po ekspansji, historię FS i kwoty rzeczywiście zaliczone przed osiągnięciem limitu.

## Sprawdzenie i użycie

Python 3.12 lub nowszy. Silnik, podstawowe obliczenia i testy korzystają wyłącznie z biblioteki standardowej. NumPy 2.x jest potrzebny do ponownego zbudowania pełnych rozkładów i niezależnej weryfikacji. Gotowe wyniki są dołączone.

Z folderu tej wersji:

```text
python -B run_checks.py
python -B -m polska_gurom theory
python -B -m polska_gurom sample --seed 20261018
python -B -m polska_gurom simulate --spins 100000 --out verification/my_simulation.json
```

Pełne odtworzenie rozkładu i walidacji, z zainstalowanym NumPy:

```text
python -B tools/build_distribution.py
python -B tools/verify_math.py
python -B tools/check_consistency.py
python -B tools/simulate_distribution.py --rounds 10000000
```

Wyniki dokładne opierają się na enumeracji 60 466 176 rzeczywistych układów bębnów oraz trzech stanów rozwinięcia Wild. Symulacja 10 mln rund jest dodatkową kontrolą, oddzielną od symulacji rzeczywistego kodu gry. Po zmianie jakiegokolwiek parametru należy odtworzyć rozkłady i wyniki; narzędzia odrzucają dane z niezgodnym odciskiem konfiguracji.

## Ważne dla dalszej integracji

- Wartości `*_units` są mnożnikami całkowitej stawki w skali 100, nie groszami ani stawką na pojedynczą linię. Wypłata matematyczna to dokładnie `payout_units/100 * total_bet`. Nie dzielić jej ponownie przez 20 ani nie zaokrąglać osobno każdej linii.
- `line_wins` opisują surowe należności. Po osiągnięciu limitu front powinien rozliczać `free_spin_credits` i `cap_reduction_units`; suma zaksięgowanych kwot zawsze jest równa `payout_units`.
- Symulacje używają deterministycznego `random.Random`. Produkcyjna integracja musi użyć generatora platformy z równomiernym losowaniem ograniczonych liczb całkowitych, zachowując opisany rozkład. Losowanie nie należy do frontendu.
- Jednostki rozliczeniowe rzeczywistej platformy, dopuszczalne stawki i ewentualne zaokrąglenia walutowe muszą zachować model albo zostać ponownie uwzględnione w matematyce.
- Integracja zależna od aktualnego Stake Engine SDK pozostaje oddzielnym etapem. Ta wersja jest zweryfikowanym lokalnym prototypem matematyki.

Szczegółowe zasady: [GDD](docs/GAME_DESIGN_DOCUMENT.md), [specyfikacja matematyczna](docs/MATH_SPECIFICATION.md), [PAR sheet](docs/PAR_SHEET.md), [raport walidacji](VERIFICATION_REPORT.md).
