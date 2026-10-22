# Waluty i stawki platformy — 22.10.2026

W uruchomieniu RGS walutę określa `balance.currency` z `/wallet/authenticate`. Przyciski minus/plus wybierają wyłącznie poziomy `config.betLevels`. Platforma dostarcza też `minBet`, `maxBet`, `stepBet` oraz kwotę `defaultBetLevel`. Nie ma lokalnego przełącznika portfela ani przeliczania kursów.

Kwoty API pozostają całkowitymi mikrojednostkami: 1 jednostka waluty = 1 000 000 jednostek API. Kod waluty jest widoczny przy saldzie, stawce i wygranej. Format PL/EN/DE zachowuje minimalną liczbę miejsc właściwą dla waluty oraz wszystkie istotne cyfry aż do sześciu miejsc. Przykład: stawka `10000` w JPY to **0,01 JPY**, wypłata `3000` to **0,003 JPY**. Nie są zaokrąglane do zera. Wartości bliskie granicy bezpiecznych liczb również są formatowane bez utraty mikrojednostek.

Konfiguracja jest sprawdzana przed grą: dodatnie bezpieczne liczby całkowite, granice, krok, unikalne poziomy, obecność minimum, maksimum i domyślnej kwoty na liście. Niespójna konfiguracja blokuje uruchomienie zamiast tworzyć dodatkowe stawki. Zmienione poziomy otrzymane przy ponownym uwierzytelnieniu trafiają do interfejsu. Już opłacona runda zachowuje swoją stawkę; po jej zakończeniu niedostępna stawka zmienia się na nową domyślną, a AUTO zatrzymuje się.

Wybrana stawka jest zapisywana osobno dla sesji platformy i waluty. Zmiana waluty w odpowiedzi portfela lub po odświeżeniu tej samej utrwalonej sesji blokuje dalsze zakłady. Parametr `currency` w zwykłym linku nie zastępuje waluty uwierzytelnionego portfela. Parametr `amount` jest używany w osobnej obsłudze replay; nie zmienia domyślnej stawki zwykłej sesji.

Sprawdzono formatter dla wszystkich 34 walut fiat wymienionych przez oficjalnego klienta. Kody 3–8 wielkich liter, np. USDT/DOGE, mają dodatkową obsługę formatowania i testy syntetyczne; nie oznacza to potwierdzenia dostępności tych portfeli na Stake.

## Zakres social

Bieżące wydanie standardowego RGS nie obejmuje social. `social=true`, waluty XSC/XGC/SC/GC oraz flaga `socialCasino` z odpowiedzi authenticate blokują grę. Pełne social wymaga oddzielnego wdrożenia słownika, angielskiego interfejsu, mapowania XSC→SC i XGC→GC oraz odbioru rynku docelowego.

## Lokalne sprawdzenie

W paczce testera otwórz terminal w rozpakowanym folderze i uruchom:

```powershell
python qa/rgs_mock_server.py --currency JPY --port 8872
```

Symulator otworzy stronę z wirtualnym saldem 100 JPY. Zmniejsz stawkę do 0,01 JPY. Scenariusz `middle` zwraca 0,003 JPY, końcowe saldo wynosi 99,993 JPY. Można też wybrać np. `--currency KWD` lub `--currency MXN`. Symulator powtarza rzeczywistą rundę z banku; nie testuje losowania RTP.

Lokalne demo bez parametrów sesji nadal używa swojego salda i stawek PLN. Rzeczywisty launch i akceptacja platformy wymagają jej środowiska.

## Źródła

- [Authenticate](https://github.com/engineio/docs/blob/main/src/routes/docs/api/authenticate/%2Bpage.svx)
- [Typy i waluty oficjalnego klienta](https://github.com/engineio/ts-client/blob/main/src/types.ts)
- [Walidacja stawek oficjalnego klienta](https://github.com/engineio/ts-client/blob/main/src/client.ts)
- [Parametry uruchomienia](https://github.com/engineio/docs/blob/main/src/routes/docs/reference/url-structure/%2Bpage.svx)
- [Social](https://github.com/engineio/docs/blob/main/src/routes/docs/reference/social-mode/%2Bpage.svx)

Odczyt źródeł: 22.10.2026. Wyniki testów lokalnych nie zastępują odbioru na rzeczywistej platformie.
