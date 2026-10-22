# Język uruchomienia i formaty kwot

Aktualizacja: 22.10.2026. Dotyczy wersji `0.6.0-high-wins`, lokalnego demo, sesji RGS i powtórek.

## Wybór języka

- `?lang=pl`, `?lang=en` i `?lang=de` wybierają język przed pierwszym żądaniem sieciowym, także przy błędnym linku startowym.
- Wielkość liter, spacje wokół kodu i odmiany regionalne są normalizowane: `PL`, `pl-PL`, `en_US`, `de-DE`.
- Podany parametr ma pierwszeństwo przed zapamiętanym ustawieniem. Pusty lub nieobsługiwany kod wybiera angielski.
- Bez parametru sesja RGS i publiczna powtórka używają angielskiego. Lokalne demo używa zapamiętanego prawidłowego języka, a przy jego braku — polskiego.
- Język można zmienić w ustawieniach. Ponowne łączenie zachowuje wybór dokonany w bieżącej karcie. Nowe wejście przez link z `lang` ponownie respektuje parametr.

Przykłady lokalnego demo: `http://127.0.0.1:8772/?lang=en`, `http://127.0.0.1:8772/?lang=de-DE`.

## Komunikaty

Sprawdzono kompletność słowników PL/EN/DE, ekrany ładowania, błędy uruchomienia i sesji, przyciski, podpowiedzi, etykiety dostępności, zasady, historię i powtórki. Komunikaty błędów są wybierane z lokalnego słownika na podstawie kodu; surowa treść błędu serwera nie trafia do interfejsu. Zmiana języka po błędzie zachowuje informację o blokadzie gry.

Zasady sesji RGS opisują portfel platformy. Zasady publicznej powtórki opisują odtwarzanie zapisanego wyniku. Nie pokazują instrukcji resetowania lokalnego portfela. Przed odczytem salda pola kwot mają znak „—”.

## Kwoty

Waluta zwykłej gry RGS pochodzi z uwierzytelnienia platformy. Wszystkie kwoty tej ścieżki są wyświetlane z jawnym kodem waluty, np. USD lub KWD. Separatory zależą od języka. Standardowa liczba miejsc dziesiętnych waluty jest zachowana; dodatkowe cyfry do sześciu miejsc pokazują rzeczywistą precyzję mikrojednostek. Przykładowo jedna mikrojednostka USD to `0,000001 USD` w PL/DE, a pół JPY nie jest zaokrąglane do całego jena.

Formatowanie używa części całkowitej i ułamkowej, bez utraty końcowych cyfr przez dzielenie dużej liczby zmiennoprzecinkowej. Obejmuje saldo, stawkę, wygraną, wynik sesji, historię i powtórki. Lokalne demo zachowuje PLN i skalę 100. Komunikat nowej sesji pokazuje faktycznie zwrócone saldo.

## Weryfikacja

`node qa/test_localization.cjs` wykonuje 73 scenariusze lokalizacji z rzeczywistym kodem interfejsu i klienta RGS, minimalnym modelem DOM oraz symulowanym API. Osobne testy obejmują waluty platformy, rundy, odzyskiwanie, powtórki, AUTO i błędy sieci.

Testy nie są potwierdzeniem działania na rzeczywistej platformie ani wizualnym odbiorem w przeglądarce. Podczas tej weryfikacji testy HTTP do lokalnego symulatora zostały zablokowane ograniczeniami środowiska; dodatkowa próba ich uruchomienia nie została wykonana, ponieważ automatyczny przegląd uprawnień nie mógł się zakończyć z powodu limitu użycia.
