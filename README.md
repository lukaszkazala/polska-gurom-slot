# POLSKA GUROM — model matematyczny

**PROTOTYPE / NOT MATH-FROZEN. Nowa implementacja / rekonstrukcja z jawnymi założeniami, nie wierne odtworzenie v0.1.** Dokumentacja po polsku; kod Python 3.10+.

Projekt początkowo był pusty: brak AGENTS.md, kodu, oryginalnych pasków, testów i raportów. Nie ma katalogu `sources/`; ewentualne przyszłe materiały w nim pozostają tylko do odczytu. Model nie jest integracją produkcyjną Stake ani modelem z zamrożoną matematyką.

## Uruchomienie

Z katalogu projektu, z zainstalowanym Pythonem i NumPy:

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/run_analysis.py --output reports/results/analysis.json
python scripts/run_simulations.py
python scripts/sample_round.py --seed 20261017
python scripts/sample_round.py --witness --output reports/max_win_witness.json
python scripts/verify_bounds.py
python scripts/check_sdk_precision.py
python scripts/build_report.py
```

Skrypt symulacji domyślnie wykonuje 10 000, 100 000 i 1 000 000 pełnych płatnych rund, z seedami 20271017, 20361017 i 21261017 (seed bazowy 20261017 + liczba rund). Wyniki JSON znajdują się w `reports/results/`, a interpretacja w `reports/MATH_REPORT.md`. Raport sprawdza zgodność zapisanych wyników z hashem aktualnego pakietu. Log ostatnich testów deterministycznych zapisano w `reports/results/tests.txt`. Polecenia instalacyjne podano dla odtwarzalności; nie oznaczają, że zależności były instalowane podczas tego audytu. W zastanym środowisku dostępne były Python 3.10.11 i NumPy 2.2.6.

## Co sprawdzać

- `configs/reconstruction_v0_1.json`: pełne uporządkowane paski, 20 linii, wszystkie kwoty i prawdopodobieństwa. To źródło parametrów matematycznych.
- `configs/presentation.json`: oddzielne nazwy i kandydatury grafik; silnik nie wczytuje tej mapy.
- `polska_gurom/`: konfiguracja, symbole, bębny, evaluator, Scatter, Charge, cap, silnik rund, analityka, symulacja i most jednostek.
- `tests/test_math.py`, `docs/TEST_PLAN.md`: deterministyczna weryfikacja zasad i niezależny evaluator referencyjny.
- `docs/GAME_DESIGN_DOCUMENT.md`, `docs/MATH_SPECIFICATION.md`, `docs/PAR_SHEET.md`: reguły, jednostki, metody oraz parametry.
- `docs/STAKE_COMPLIANCE.md`: aktualne oficjalne źródła, różnice SDK i granice zgodności.
- `reports/MATH_REPORT.md`: wyniki uruchomień, cele i maksymalnie trzy niewdrożone warianty tuningu.

Runda to jeden płatny spin i wszystkie przyznane FS. Stawka analityczna B=1. Kwoty są brutto w jednostkach 1/100 TOTAL BET; nie dzielimy pojedynczej wygranej liniowej przez 20. Netto gracza = przyznana wypłata − 1. Wszystkie FS są rozgrywane także po osiągnięciu cap 5000×; suma przyznanych składowych pozostaje zgodna z cap całej rundy.

Analityka wyznacza dokładne średnie **przed cap**, a wpływ cap ogranicza dowodem. Hit frequency i wariancja uwzględniają wspólne zatrzymania bębnów w Monte Carlo. Zgodność średnich historycznych nie dowodzi zgodności kolejności pasków ani rozkładu wypłat. Szczegóły klasyfikacji wyników są w raporcie.

## Odtwarzalność

Skalarny silnik przyjmuje `random.Random`; wynik rundy przechowuje naturalne i końcowe plansze, zatrzymania, wygrane linie, Scattery, przyznane FS i Charge. Symulator używa jawnie wersjonowanego backendu NumPy PCG64 oraz seedów. Sekwencje dwóch backendów są różne; powtarzalność wymaga tego samego backendu, wersji kodu, konfiguracji i bibliotek. Raporty zapisują hash parametrów i kodu. Nie ma stanu przenoszonego między płatnymi rundami, retriggerów ani optymalizacji wag.
