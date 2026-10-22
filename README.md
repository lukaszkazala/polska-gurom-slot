# POLSKA GUROM — gra i matematyka 0.6.0-high-wins

Aktualny lokalny wariant gry znajduje się w **[test-interface-any-start/](test-interface-any-start/README_PL.md)**. Obejmuje demo z wirtualnym saldem, kaskady, układy od dowolnego bębna, bonusy 8/10/12 FS, replay oraz klienta RGS. Data ostatniej przebudowy matematyki: **22.10.2026**.

## Uruchomienie aktualnej gry

Potrzebny jest Python **3.12 lub nowszy**. Zwykłe demo korzysta z biblioteki standardowej Pythona; nie wymaga instalowania NumPy ani zstandard.

Na Windows uruchom **[test-interface-any-start/START_UX.cmd](test-interface-any-start/START_UX.cmd)**. Gra otworzy się pod **http://127.0.0.1:8772**. Można też uruchomić serwer z katalogu repozytorium:

```powershell
python test-interface-any-start/server.py --port 8772 --no-browser
```

Następnie otwórz ten adres w przeglądarce. Po aktualizacji zakończ poprzedni proces serwera i uruchom go ponownie, aby wczytał nowy kod i bank. Saldo demo jest wirtualne i przechowywane w pamięci serwera.

Gotowa paczka przenośna: **[POLSKA_GUROM_TESTER.zip](test-interface-any-start/POLSKA_GUROM_TESTER.zip)**. Wypakuj całe archiwum i uruchom `START_UX.cmd` z wypakowanego folderu.

## Parametry bieżącego eksportu

Matematyka **0.6.0-high-wins** wykorzystuje ważony bank **100 343 różnych pełnych rund**. Jedna płatna runda obejmuje bazę, wszystkie jej kaskady i przyznane darmowe obroty; po osiągnięciu limitu pozostałe FS nie są wykonywane.

| Parametr | Wartość |
|---|---:|
| Dokładne RTP | 24/25 = 96% |
| Koszt płatnej rundy | 1× |
| Krok wypłaty | 0,1× całej stawki |
| Limit całej rundy | 5000× |
| Łączna szansa maksimum | 1:8 000 000 |
| Suma wag | 1 000 000 000 000 biletów |
| Łączna masa maksimum | 125 000 biletów |
| Różne osiągalne kwoty ≥500× | 297 |
| Największa luka 500×–5000×, z brzegami zakresu | 98,6× |
| Wkład wypłat ≥500× do RTP | 2,44355542032 p.p. |

Maksimum ma dodatnią wagę w bazie oraz **w każdym wariancie 8/10/12 FS**. Podział istniejących 125 000 biletów maksimum wynosi: baza **62 500**, 8 FS **31 250**, 10 FS **18 750**, 12 FS **12 500**. Nie podwojono łącznej szansy maksimum.

Zachowano masy wejścia do bonusów: 8 FS **4 679 041 094**, 10 FS **286 875 670**, 12 FS **4 018 776** biletów. Bębny, tabela wypłat, zasady linii i kaskad, mnożnik linii 4× w FS oraz ekspansja Wildów pozostały bez zmian.

**Istotny skutek strojenia:** przy tym samym budżecie RTP wysokich wypłat ich łączna częstość ≥500× spada z około **1:27 959** do około **1:47 374**. Wariancja rośnie z około **99,02362** do **111,43297** stawki². Nowy rozkład daje więcej różnych wysokich rezultatów; nie obiecuje częstszych wysokich wygranych ani poprawy wyników krótkiej sesji.

## Odbiór i dowody

[Raport przebudowy wysokich wygranych](audit/high_wins_rebuild_2026_10_22/RAPORT_PL.md) zawiera porównanie z `0.5.0-any-start`, plan częstości i wkładów RTP zapisany przed doborem wag, podział maksimum oraz wyniki kontroli. Sprawdzono wszystkie 100 343 eksportowane rundy i ich zdarzenia; **18/18 zestawów regresji** głównego wariantu przeszło. Starszy interfejs przeszedł dodatkowo 45/45 testów prezentacji limitu. Obie paczki sprawdzono po wypakowaniu.

- [Pełna niezależna weryfikacja eksportu](audit/high_wins_rebuild_2026_10_22/final_verification.json)
- [Wyniki regresji](audit/high_wins_rebuild_2026_10_22/regression_summary.json)
- [Zgodność zweryfikowanych plików i gotowych paczek](audit/high_wins_rebuild_2026_10_22/DELIVERY.json)
- [Decyzja projektowa](decisions/high_wins_2026_10_22/DECYZJA_PL.md) i [potwierdzenie wykonania](decisions/high_wins_2026_10_22/WYKONANIE_PL.md)
- [Nowy eksport matematyki ZIP](audit/high_wins_rebuild_2026_10_22/POLSKA_GUROM_MATH_v0_6_0_HIGH_WINS.zip)

Lokalne testy i eksport nie stanowią zatwierdzenia platformy. Integracja z rzeczywistym środowiskiem RGS i jej odbiór są osobnym etapem; opis znajduje się w [instrukcji RGS](test-interface-any-start/README_RGS_PL.md).

## Struktura repozytorium

| Ścieżka | Rola |
|---|---|
| `test-interface-any-start/` | Główny aktualny wariant gry, silnik, selektor, bank, RGS i replay |
| `test-interface/` | Starszy wariant interfejsu z zachowanymi grafikami i efektami; korzysta z tego samego banku 0.6.0 |
| `audit/high_wins_rebuild_2026_10_22/` | Plan, kopia odniesienia, weryfikatory, porównanie, testy i dowody przebudowy |
| `decisions/` | Decyzje projektowe i zapisy ich wykonania |
| `music-polska-gurom-v1/`, `ux-stake-v1/` | Muzyka, grafiki, projekty i informacje o zasobach |
| `publication/`, `results-dashboard/` | Materiały publikacyjne i dashboard wyników; historyczne kopie zachowują wersję opisaną we własnych metadanych |
| `polska_gurom_v0_2/` | Zachowany wcześniejszy model 0.2 |
| `polska_gurom/`, `configs/`, `scripts/`, `tests/`, `reports/` w katalogu głównym | **Historyczna rekonstrukcja v0.1** z wcześniejszej historii repozytorium; nie jest silnikiem aktualnej gry 0.6.0 |

Opis i polecenia dla historycznej rekonstrukcji zachowano w **[docs/README_RECONSTRUCTION_v0_1.md](docs/README_RECONSTRUCTION_v0_1.md)**. Główne `requirements.txt` dotyczy tego starszego pakietu. Aby uruchomić bieżącą grę, użyj polecenia z pierwszej sekcji tego README.

## Odtworzenie i kontrola aktualnej matematyki

Z katalogu repozytorium:

```powershell
python test-interface-any-start/build_math.py
python audit/high_wins_rebuild_2026_10_22/verify_events.py --game test-interface-any-start --bank test-interface-any-start/stake_math --output audit/high_wins_rebuild_2026_10_22/final_verification.json --acceptance
python audit/high_wins_rebuild_2026_10_22/run_regressions.py
```

Budowanie i odczyt kompresowanego eksportu wymagają modułu `zstandard` odpowiedniego dla używanego Pythona i systemu. Kompilator korzysta także z zapisanych naturalnych świadków 12 FS wskazanych w kodzie. W repozytorium zachowano użyte wcześniej zależności kompilatora; nie są one wymagane do zwykłego uruchomienia demo.

Plik **[.gitattributes](.gitattributes)** wyłącza automatyczną zamianę końców linii (`* -text`). Selektor sprawdza sumy SHA256 plików źródłowych i eksportu, dlatego ich bajty muszą pozostać identyczne również po pobraniu repozytorium na innym systemie. Zmiana reguł lub źródeł silnika wymaga ponownego zbudowania i sprawdzenia banku.

[.gitignore](.gitignore) pomija pamięci podręczne, chwilowe wyniki kompilatora i wypakowane kopie testów paczek. Rzeczywiste zasoby, eksporty, archiwa ZIP, raporty i logi audytów pozostają częścią projektu. Materiały w `sources/`, jeżeli są dostępne, stanowią odniesienia tylko do odczytu.
