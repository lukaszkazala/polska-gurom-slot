# iPhone 15 / Safari — pierwsza próba

Przygotowano 22.10.2026. Telefon i komputer: ta sama sieć Wi‑Fi. Gra korzysta wyłącznie z wirtualnego salda.

**Build do tej próby:** `iphone15-safari-20261022T095007`. Manifest SHA-256: `601312412e29e69039eee70451cb1d161db7897c0e412e87bf00b31ec7bb264f`. Kopia zawiera nową obsługę audio, sześć plików WAV i przycisk wyciszenia. Jest osobnym buildem do testów, nie potwierdzeniem gotowości platformowej.

1. Zeskanuj aparatem iPhone’a [kod QR](IPHONE15_QR.png) i otwórz go w Safari albo użyj [linku testowego](http://192.168.1.19:8785/__phone/start?key=wv5lVdTgW_vVHUXAXDcl6SO4A0WvlHJT). Komputer musi pozostać włączony i połączony z tą siecią. Link działa tylko lokalnie. Jeśli otwieranie z innej aplikacji zawiedzie, wklej cały adres bezpośrednio do Safari.
2. Poczekaj na symbole i saldo. Podaj wersję iOS oraz potwierdź, czy gra się otworzyła. Jeśli nie — zapisz komunikat Safari. Sam timeout nie rozstrzyga, czy przyczyną jest zapora komputera, izolacja urządzeń Wi‑Fi czy połączenie telefonu.
3. W pionie ustaw zwykłą szybkość i wykonaj jeden obrót. Posłuchaj, czy po dotknięciu zaczęła grać muzyka. Sprawdź przycisk głośnika: wycisz, wykonaj obrót, następnie włącz dźwięk.
4. Wyłącz blokadę obrotu telefonu. Obróć go poziomo i z powrotem pionowo: najpierw w spoczynku, potem w trakcie rundy. Sprawdź, czy nadal widać planszę, saldo, stawkę i przycisk obrotu.
5. Przejdź do innej aplikacji na 30 sekund i wróć; następnie powtórz z blokadą ekranu. Sprawdź, czy gra reaguje, dźwięk zachowuje ustawione wyciszenie i nic nie uruchamia nowej rundy bez Twojego gestu.
6. Otwórz koło zębate → **Przetestuj po swojemu** → **Scenariusz następnej rundy**. Wybierz **Uruchomienie bonusu**, zamknij ustawienia i rozpocznij pokaz. W trakcie bonusu obróć telefon, a w osobnej próbie wyjdź do innej aplikacji na 30 sekund. Scenariusz jest demonstracyjny i nie zmienia salda.

Pierwszy opis wyniku może być krótki:

```text
iOS:
Gra otwiera się: tak/nie + komunikat
Dotyk: OK/błąd + opis
Obrót: OK/błąd + opis
Powrót po 30 s i blokadzie: OK/błąd + opis
Muzyka i wyciszenie: OK/błąd + opis
Bonus: OK/błąd + opis
```

To pierwsza próba. Pełne powtórzenia, AUTO, przerwane połączenie, utrata pamięci karty i pozostałe przypadki opisuje [protokół testów](TESTY_FIZYCZNE_PL.md). Bez ich wyników nie oznaczać całego zakresu jako zaliczonego. Brak dostępu do platformy nadal blokuje test rzeczywistej ramki i popout.

## Dla obsługi na komputerze

Serwer testowy nasłuchuje tylko na wskazanym adresie Wi‑Fi, a dostęp do gry wymaga lokalnego linku. Nie udostępnia katalogu projektu, silnika ani plików raportów. Nie zmieniano ustawień zapory Windows ani routera. Po zmianie adresu komputera lub ponownym uruchomieniu serwera wygenerować aktualny link; obecny może przestać działać.

Zatrzymanie: uruchomić `python phone_server.py --stop` z katalogu tego raportu. Ponowne uruchomienie: `python phone_server.py --host 192.168.1.19 --port 8785`. Aktualny link jest zapisywany w `phone_runtime.json`. Nie zmieniać zamrożonego folderu gry w trakcie testów; poprawki wymagają nowego buildu i manifestu.

Weryfikacja przygotowania: 7/7 lokalnych testów HTTP serwera zaliczonych; strona i wszystkie sześć plików audio dostępne z komputera pod adresem Wi‑Fi. **Połączenie z iPhone’a i testy fizyczne: jeszcze niepotwierdzone.**
