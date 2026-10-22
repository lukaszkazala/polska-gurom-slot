# Gotowy tester grafik — 20.10.2026

Uruchomiona wersja: http://127.0.0.1:8772 . Serwer jest lokalny, z wirtualnym saldem. Uruchamiacz na później: `test-interface/START_UX.cmd`. Paczka: `test-interface/POLSKA_GUROM_UX_18_SYMBOLI.zip`.

Zgodnie z wyborem użytkownika dodano zestawy graficzne, zachowując matematykę. Katalog obejmuje 18 ilustracji, z nowymi pierogami, bocianem i smokiem wawelskim. Każdy z 3 zestawów ma 8 zwykłych symboli oraz WILD i SCATTER. Zmieniono wygląd planszy, tabelę wypłat i nazwy zgodnie z zestawem, dodano katalog grafik, trwały wybór i blokadę przełączania w trakcie rundy, oczekującego wyniku oraz autoobrotów. Przy braku zasobów nazwy i grafiki wracają do symboli zastępczych.

## Weryfikacja

- Sprawdzono identyczność SHA-256 dwunastu plików silnika i matematyki względem kopii sprzed zmian. Żaden nie zmienił się; także w nowej paczce ZIP.
- Testy HTTP: 10 zakończonych powodzeniem. Pierwszą próbę ograniczyły uprawnienia sieciowe środowiska; po uruchomieniu poza tym ograniczeniem testy przeszły.
- Regresja frontendu: 13 scenariuszy autoobrotów z prawdziwym `app.js`, w tym po 100 rund dla czterech szybkości, zatrzymanie i ponowienia żądań. To kontrola logiki, nie statystyczne badanie RTP.
- Przeglądarka: wszystkie 3 zestawy, po 15 widocznych grafik i ścieżek przycięcia, po 8 wierszy wypłat i po 10 aktywnych pozycji z katalogu 18. Wszystkie komórki wypłat identyczne między zestawami. Wyniki w `browser_themes.json`.
- Przeglądarka: zwykła runda zakończona, wybór zestawu niedostępny podczas obrotu, ponownie dostępny po zakończeniu.
- Przeglądarka: scenariusz bonusu zakończony z licznikiem 8/8 i wynikiem 22,20 zł; saldo sesji testowej 9998 zł bez zmiany, zgodnie z zasadami scenariuszy.
- Przeglądarka: teksty PL/EN/DE, brak błędów konsoli w kontrolowanej sesji.
- Telefon 390 × 844: 15 pól, brak poziomego przewijania, plansza i przycisk obrotu widoczne w pierwszym ekranie. Zapis `mobile.png`. Komputer: `desktop.png`.
- Paczka ZIP: sprawdzona integralność i obecność nowych grafik, styli, katalogu oraz uruchamiacza. Szczegóły w `release_checks.json`.

Podczas kontroli wykryto odsłanianie sąsiednich fragmentów atlasu przy dopasowywaniu ilustracji do pola. Dodano odrębne ścieżki przycięcia SVG w układzie współrzędnych źródła; powtórna kontrola galerii potwierdziła izolację obiektów.

Sesja kontrolna używała hosta `localhost`, a sesja użytkownika `127.0.0.1`, dzięki czemu nie resetowano jego salda i historii. Serwer ma obsługę obu nazw hosta, ale nasłuchuje wyłącznie lokalnie. Kartę kontrolną zamknięto; kartę użytkownika zachowano jako wynik pracy. Serwer pozostawiono uruchomiony do testowania.

## Ograniczenia

To lokalny tester UX. Nie włączono muzyki ani integracji RGS i nie publikowano gry na Stake. Ilustracje są połączone w lokalne atlasy i przycinane w przeglądarce; nie są osobnymi plikami każdego symbolu. Prawa i finalne podobieństwo zasobów wymagają końcowej weryfikacji zgodnie z wcześniejszym rejestrem oraz `web/assets/art/PROVENANCE.md` — nie zadeklarowano pełnego zatwierdzenia prawnego.
