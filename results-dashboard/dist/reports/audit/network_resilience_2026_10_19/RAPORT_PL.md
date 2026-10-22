# Testy utraty połączenia — POLSKA GUROM

Wynik: **47/47 nowych testów awarii PASS** — 17 przez rzeczywiste połączenia HTTP/TCP oraz 30 testów logiki interfejsu. Ponownie przeszło 13 testów autospinu, 10 testów HTTP i salda oraz 27 kontroli wypakowanej paczki.

## Sprawdzone sytuacje

| Sytuacja | Wynik po poprawkach |
|---|---|
| Brak połączenia przed dotarciem żądania | Brak pobrania stawki; ponowienie używa tego samego identyfikatora. |
| Serwer rozliczył rundę, ale odpowiedź zginęła lub została ucięta | Odzyskano ten sam wynik; stawka i wygrana są księgowane jeden raz. |
| Odpowiedź trwa ponad 15 sekund, również jej treść | Żądanie przestaje blokować interfejs; pozostaje możliwość odczytu tej samej rundy. |
| Błędy 408, 429, 500, 502, 503 | Autospin ponawia tę samą rundę maksymalnie trzy razy. |
| Dłuższa awaria | Seria zatrzymuje się z powodem i przyciskiem „PONÓW ODCZYT”. |
| Błędny JSON, zły kształt odpowiedzi, niezgodny identyfikator rundy/sesji/matematyki | Odpowiedź nie usuwa oczekującego żądania i nie zatwierdza błędnego wyniku. |
| Odświeżenie karty z nierozstrzygniętym obrotem | Żądanie jest odzyskiwane z pamięci sesji karty; nie uruchamia automatycznie nowej serii. |
| Restart, wygaśnięcie sesji lub brak ciasteczka | Stary obrót jest odrzucany przed rozliczeniem; potrzebne odczytanie nowej sesji. |
| Reset sesji w drugiej karcie | Stary identyfikator sesji jest odrzucany; brak naliczenia nowej stawki. |
| Osiem równoległych ponowień, podwójne kliknięcie | Jedna zaakceptowana runda i jedno rozliczenie. |
| Ponowienie po wypadnięciu wyniku z historii 100 rund | Identyfikator pozostaje oznaczony jako rozliczony; brak drugiego pobrania stawki. |
| Utrata połączenia po otrzymaniu całego bonusu | Prezentacja przyznanych darmowych obrotów kończy się; kolejna płatna runda podlega kontroli połączenia. |

## Testy w rzeczywistej przeglądarce

W osobnym środowisku lokalnym przekaźnik fizycznie zrywał połączenia HTTP lub opóźniał odpowiedź. Nie zmieniano ustawień internetu komputera. Samo wyłączenie Wi-Fi nie odcina tej gry od lokalnego adresu 127.0.0.1; badano połączenie gry z jej serwerem.

1. Trzy przerwane próby przed dotarciem do serwera: licznik **0/10**, saldo **10 000 zł**, widoczny komunikat „Brak połączenia” i „PONÓW ODCZYT”. Po przywróceniu połączenia rozliczono tylko jedną rundę; seria pozostała zatrzymana.
2. Zerwana odpowiedź po rozliczeniu: ręczny odczyt zwrócił dokładnie ten sam wynik, bez kolejnej stawki.
3. Odpowiedź opóźniona o 18 sekund: zadziałał limit 15 sekund; ręczny odczyt zwrócił wcześniej rozliczoną rundę.
4. Seria **100/100** ze zgubieniem odpowiedzi po rozliczeniu pierwszej rundy: seria zakończyła się w całości. W całym laboratorium było **103 różnych płatnych rund**, a suma stawek wyniosła dokładnie **103 × 2 zł**. Każde ponowienie miało ten sam wynik, identyfikator i saldo co pierwsza odpowiedź serwera.

Odświeżenie z oczekującym żądaniem, błędny JSON, błędy 408/429/5xx i awaria podczas bonusu zostały dodatkowo sprawdzone deterministycznie w rzeczywistej logice app.js. Testy tej warstwy używają kontrolowanego transportu i przyspieszonego zegara; nie są przedstawiane jako fizyczne odłączenie internetu.

## Usunięte problemy

- Żądanie obrotu jest związane z konkretną sesją. Restart lub reset nie zamienia starego żądania w nową płatną rundę.
- Historia 100 wyników i ślady rozliczonych identyfikatorów są przechowywane osobno. Wyparcie szczegółów nie pozwala ponownie pobrać stawki.
- Oczekujący obrót jest zapisywany w pamięci sesji karty. Wynik po odzyskaniu nie jest dublowany w historii.
- Odpowiedź jest sprawdzana przed usunięciem oczekującego żądania. Dodano poprawną obsługę 408/429 i limit czasu również dla pliku symboli.

RTP wynosi nadal dokładnie **96%**. Sumy SHA-256 silnika oraz opublikowanego rozkładu matematyki zgadzają się z wcześniejszym audytem; ta zmiana dotyczy obsługi połączenia i rozliczania żądań.

## Ograniczenia lokalnego testera

Restart procesu usuwa wirtualny portfel i historię z pamięci. Zabezpieczenie blokuje ponowne rozliczenie starego żądania; nie odtwarza utraconego portfela. Po 100 zapisanych wynikach starszy pełny wynik nie jest odtwarzany, choć stary identyfikator nadal nie może pobrać stawki. Odzyskiwanie po odświeżeniu wymaga dostępnej pamięci sessionStorage tej samej karty. Nie testowano rzeczywistego portfela ani prywatnego RGS Stake.

## Dowody i paczka

- [Nowa paczka gry ZIP](<C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/POLSKA_GUROM_v0_4_NETWORK_FIX.zip>)
- [17 testów HTTP/TCP](<C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/qa/network_faults_results.json>)
- [30 testów logiki awarii](<C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/qa/network_logic_results.json>)
- [13 wcześniejszych testów autospinu](<C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/qa/autoplay_logic_results.json>)
- [Odczyty z przeglądarki](<C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/qa/network_browser_results.json>)
- [Dziennik rzeczywistych prób i rozliczeń laboratorium](<C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/qa/browser_fault_events.jsonl>)
- [Kontrole paczki](<C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/qa/portable_check.json>)
- [Zbiorczy wynik i sumy kontrolne](<C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/network_resilience_2026_10_19/results.json>)

Testy można odtworzyć poleceniami: `python test-interface/qa/test_network_faults.py`, `node test-interface/qa/test_network_logic.cjs` oraz `node test-interface/qa/test_autoplay.cjs`. Są izolowane od otwartej sesji gry i nie wyłączają internetu komputera.
