# Waluty i stawki platformy — zakończenie 22.10.2026

Zaktualizowano aktywną wersję `test-interface-any-start` oraz obie paczki RGS. Waluta, saldo i dopuszczalne stawki pochodzą z uwierzytelnienia platformy. Lokalny tryb demo pozostaje w PLN.

## Zmiany

- Kwoty są wyświetlane z kodem waluty i bez utraty mikrojednostek, do sześciu miejsc; zachowane minima formatu JPY/KWD i lokalizacje PL/EN/DE.
- Formatowanie używa całkowitej części i ułamka BigInt, również przy granicy bezpiecznych liczb. Poszerzono tolerowaną składnię kodów do 3–8 wielkich liter.
- Dostępne stawki muszą odpowiadać liście, minimum, maksimum, krokowi i domyślnej kwocie z platformy. Niespójne konfiguracje blokują grę.
- Zmiany stawek otrzymane przy ponownym uwierzytelnieniu są widoczne w interfejsie. Opłacona runda zachowuje historyczną stawkę. Usunięcie wybranej stawki zatrzymuje AUTO po rozliczeniu i ustawia nową domyślną stawkę.
- Preferencja stawki jest rozdzielona według sesji i waluty. Zmiana waluty utrwalonej sesji blokuje dalsze zakłady.
- Zasady sesji platformowej PL/EN/DE nie opisują już lokalnego portfela PLN; zachowano regułę limitu wygranej.
- Social pozostaje poza wydaniem standardowego RGS. Blokowane są social=true, SC/GC/XSC/XGC oraz oba formaty flagi socialCasino w authenticate.
- Tester ma opcję `--currency`, a jego paczka zawiera instrukcję `README_WALUTY_PL.md`.

## Weryfikacja

| Zestaw | Wynik |
|---|---:|
| Nowe testy walut, stawek i aktualizacji konfiguracji | 53/53 |
| Klient RGS i logika interfejsu | 60/60 |
| Odzyskiwanie rund RGS | 33/33 |
| Regresje wcześniejszych napraw | 28/28 |
| AUTO | 13/13 |
| Prezentacja pełnego bonusu 12 FS | 7/7 |
| Wygrane od dowolnego bębna | 3/3 |
| Rzeczywisty HTTP z lokalnym symulatorem | 5/5 |

W przeglądarce sprawdzono wybór minimum i pełną rundę: **100 JPY − 0,01 JPY + 0,003 JPY = 99,993 JPY**. Zrzut: `jpy-desktop.png`. Testy formatowania obejmują wszystkie 34 waluty fiat oficjalnego klienta oraz syntetyczne kody tokenów. Obsługa syntetycznych kodów nie potwierdza dostępności takich portfeli na platformie.

Obie paczki ZIP są poprawne i zawierają aktualne pliki interfejsu. Statyczna paczka frontendowa nie zawiera lokalnego silnika ani symulatora. Szczegóły, skróty paczek i źródeł zapisano w `delivery_verification.json`; wyniki i dzienniki testów znajdują się obok tego raportu.

Nie wykonano odbioru na rzeczywistym środowisku Stake ani ACP. Pozostaje on odrębnym etapem integracji. Źródła kontraktu i instrukcja sprawdzenia: `test-interface-any-start/README_WALUTY_PL.md`.
