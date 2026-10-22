# Audyt serwera POLSKA GUROM — wynik i ograniczenia

Wersja: `0.5.0-any-start`. Domknięcie przeglądu: 21.10.2026. Zakres: aktualny `test-interface-any-start/server.py`, jego API, rozliczenie wirtualnego portfela, współbieżność, odzyskiwanie po awariach oraz pakiet portable. Nie zmieniano gry ani materiałów `sources/`.

**Wniosek: zwykłe ścieżki rozliczenia przechodzą testy, ale potwierdzono lukę w atomowości rozliczenia po wymuszonej awarii przygotowania odpowiedzi. Wynik testów nie oznacza braku błędów ani gotowości do rozliczania prawdziwych pieniędzy.**

## Co faktycznie wykonano

| Zestaw | Wynik | Dowód |
|---|---:|---|
| HTTP / portfel / scenariusze | 10/10 | `test_server_unrestricted.log` |
| Kaskady / ruchy / limity | 10/10 | `test_cascades_unrestricted.log` |
| Bonus 12 FS, również rzeczywista publikowana dystrybucja (`--require-exported`) | 10/10 | `test_bonus12_api_unrestricted.log`, `api_12fs_results.json` |
| Awarie połączenia / ponowienia / utrata sesji | 17/17 | `test_network_faults_unrestricted.log`, `network_faults_results.json` |
| Pakiet portable | 27/27 kontroli | `portable/portable_check.json` |
| Dodatkowe próby audytowe | 14/14 oczekiwanych obserwacji | `extended_server_results.json` |

Ostatni wiersz obejmuje **12 pozytywnych kontroli, jedną udaną reprodukcję błędu i jedną potwierdzoną obserwację historycznego salda**. `pass` przy `test_09_record_serialization_failure_exposes_non_atomic_settlement` oznacza, że błąd został odtworzony, a nie że zachowanie gry jest prawidłowe. Nie należy sumować tych wyników jako „88 testów bez błędów”.

Pierwsze próby HTTP były blokowane przez izolację środowiska (`WinError 10013`). Następnie uruchomiono je po zaakceptowanym dostępie do lokalnego połączenia 127.0.0.1; wszystkie 47 regresji przeszły. Nie klasyfikowano blokady środowiska jako awarii gry. Testy API i kaskad importowały bieżący serwer i silnik z izolowanej kopii aktualnej wersji, nie stary `test-interface`.

Przy domknięciu nie powtarzano ukończonych testów: ponownie porównano SHA256 **45/45 plików** aktualnego źródła, kopii testowej i zapisanego manifestu — identyczne. ZIP także odpowiada dokładnie pakietowi sprawdzonemu przez smoke test. Dowód: `evidence_revalidated_2026_10_21.json`. SHA256 ZIP: `7f93e15007ba25d4faa486ff9597e8761fe9b6177fc0de59ba35f13450d749ec`.

## Potwierdzony błąd: rozliczenie może nastąpić bez zapisania identyfikatora rundy

**P2 dla lokalnego testera; do usunięcia przed użyciem tego wzorca w rzeczywistym portfelu.** Lokalizacja: `test-interface-any-start/server.py:342–345`, `353`, `360–361`. Saldo i statystyki zmieniają się przed wykonaniem `asdict(result)` oraz przed dodaniem wyniku do pamięci odpowiedzi i `processed_ids`. Blokada sesji chroni przed przeplataniem wątków, ale nie cofa częściowo wykonanej operacji po wyjątku.

Reprodukcja w `extended_server_audit.py`, test 09:

1. Wybrano prawidłową przegrywającą rundę i stawkę 100 centów, `request_id="commit-gap"`.
2. Jednorazowo wymuszono `MemoryError` w `asdict`, bez zmiany plików serwera.
3. Pierwsze żądanie zwróciło HTTP 500. Saldo spadło z 1 000 000 do 999 900; licznik rund wzrósł do 1; historia pozostała pusta.
4. Ponowienie tego samego identyfikatora zwróciło HTTP 200 i rozliczyło kolejną rundę: saldo 999 800, licznik 2.

To **potwierdzona luka ujawniona przez kontrolowane wstrzyknięcie awarii**. Nie zaobserwowano naturalnego `MemoryError` podczas zwykłej gry i nie ustalono częstości takiej awarii. Nie jest to dowód, że normalne ponowienia sieciowe pobierają stawkę dwukrotnie — takie ponowienia przeszły osobne testy.

Kierunek poprawy: przygotować kompletny wynik przed zmianą portfela i zapisywać saldo, statystyki oraz rejestr przetworzonego ID jako jedną operację z gwarancją wycofania po błędzie. W systemie z rzeczywistymi środkami wymaga to trwałej transakcji, a nie wyłącznie blokady pamięci procesu. W tym audycie nie wdrażano poprawki.

## Obserwacja: retry zwraca historyczne saldo

Lokalizacja: `server.py:320–325`. Ponowienie poprawnie zwraca identyczny zapisany wynik rundy, wraz z dawnym saldem i statystykami. W reprodukcji po dwóch rozliczeniach aktualne saldo wynosiło 999 400, a odpowiedź na ponowienie pierwszej rundy zawierała 999 900 i licznik 1 zamiast 2.

**Nie jest to dowód błędnego rozliczenia portfela serwera.** To konsekwencja kontraktu zapamiętanej odpowiedzi. Klient musi odróżniać historyczny wynik od aktualnego stanu, szczególnie przy dwóch kartach. Wpływ na ekran użytkownika wymaga oceny frontendu; nie zakłada się tutaj, że UI na pewno prezentuje błędne saldo.

## Potwierdzone zabezpieczenia

W testowanym zakresie poprawne były: 28 równoległych różnych identyfikatorów przy siedmiu stawkach i zgodna suma salda; konflikt stawek pod jednym ID; odrzucenie nadmiernych obciążeń przy małym saldzie; rozliczenie wszystkich siedmiu stawek bez utraty centów; scenariusze bez obciążania portfela; 30 niepoprawnych prób wejścia, w tym narzucania siatki, Scatterów i wypłaty; ochrona przed starym identyfikatorem sesji po resecie. Błąd selektora przed rozliczeniem oraz błąd wysyłki odpowiedzi po zapisaniu wyniku nie powodowały podwójnego rozliczenia.

## Ograniczenia zakresu

To lokalny tester z wirtualnym portfelem w pamięci. Restart usuwa sesje; stare żądanie jest odrzucane, lecz utracone saldo i historia nie są odtwarzane. Pamięć przechowuje 100 pełnych odpowiedzi; później stare ID jest odrzucane bez ponownego obciążenia. Limit 100 000 identyfikatorów, wygaśnięcie sesji i reset zostały sprawdzone, część przez zmianę izolowanego stanu testowego zamiast wielogodzinnego oczekiwania.

Testy nie obejmowały rzeczywistego Stake RGS, zewnętrznego portfela, autoryzacji operatora ani trwałej księgi transakcji. Przejście testów HTTP i portable nie potwierdza zgodności integracji produkcyjnej. Pełna ocena matematyki i przeglądarki należy do osobnych części audytu.
