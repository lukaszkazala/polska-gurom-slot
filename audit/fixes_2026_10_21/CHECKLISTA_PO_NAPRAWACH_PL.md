# Checklista po naprawach — 21.10.2026

Dotyczy lokalnego demo 0.5.0-any-start. Tylko punkty objęte nowymi dowodami zmieniono względem audytu wejściowego. Pozostałe oceny zachowują pierwotny zakres i ograniczenia.

| Punkt | Status | Uzasadnienie |
|---|---|---|
| G01 | TAK | Kod, pełny bank i niezależny kalkulator; zakres lokalny v0.5. |
| G02 | TAK | Kod, pełny bank i niezależny kalkulator; zakres lokalny v0.5. |
| G03 | TAK | B07 naprawione: aktywne zasady PL/EN/DE opisują lewy początek przy remisie; algorytm i wagi niezmienione. |
| G04 | TAK | Kod, pełny bank i niezależny kalkulator; zakres lokalny v0.5. |
| G05 | TAK | Kod, pełny bank i niezależny kalkulator; zakres lokalny v0.5. |
| G06 | TAK | B07 naprawione: wykluczenie Scattera, brak własnej tabeli Wilda i wypłaty samych Wildów są jawne. |
| G07 | TAK | Kod, pełny bank i niezależny kalkulator; zakres lokalny v0.5. |
| G08 | TAK | Kod, pełny bank i niezależny kalkulator; zakres lokalny v0.5. |
| G09 | TAK | Kod, pełny bank i niezależny kalkulator; zakres lokalny v0.5. |
| G10 | TAK | Kod, pełny bank i niezależny kalkulator; zakres lokalny v0.5. |
| G11 | TAK | Kod, pełny bank i niezależny kalkulator; zakres lokalny v0.5. |
| G12 | NIEZWERYFIKOWANE | Cap rozlicza poprawnie; forced bonus-cap PASS, lecz bank nie ma bonus-cap i UI liczy wykonane FS, nie opisuje przerwanych przydzielonych FS. |
| G13 | TAK | Kod, pełny bank i niezależny kalkulator; zakres lokalny v0.5. |
| G14 | TAK | Jeden tryb base, koszt 1; brak zakupu bonusu i Double Chance w aktualnym UI. |
| G15 | TAK | Kod, pełny bank i niezależny kalkulator; zakres lokalny v0.5. |
| G16 | TAK | B08 naprawione: jeden aktywny README v0.5, poprawne 100049 rund i kompilator aktualnego wariantu. |
| SE01 | TAK | Dokładne wagi i publiczny SDK PASS; jeden tryb base, koszt 1, eksport 100049 rekordów. |
| SE02 | TAK | Dokładne wagi i publiczny SDK PASS; jeden tryb base, koszt 1, eksport 100049 rekordów. |
| W01 | NIEZWERYFIKOWANE | Statystyki policzone, max 1:8 mln spełnia oba publiczne progi; jakość dziur i ogona pozostaje do oceny platformy. |
| W02 | TAK | 100k pełnych ważonych rund, 1 mln losowań wag; trafienie dodatnie 1:6,40095. |
| W03 | TAK | Policzono dodatnie wagi, udział płatnych rekordów, dominację i przedziały; ujawniono znaczne dziury wysokich wypłat. |
| QA01 | TAK | Pełny bank, exact rational metrics, 8/10/12 FS z dodatnią wagą, granice selektora i analiza kodu selekcji. |
| QA02 | TAK | Pełny bank, exact rational metrics, 8/10/12 FS z dodatnią wagą, granice selektora i analiza kodu selekcji. |
| QA03 | TAK | Pełny bank, exact rational metrics, 8/10/12 FS z dodatnią wagą, granice selektora i analiza kodu selekcji. |
| QA04 | TAK | Pełny bank, exact rational metrics, 8/10/12 FS z dodatnią wagą, granice selektora i analiza kodu selekcji. |
| QA05 | TAK | Pełny bank, exact rational metrics, 8/10/12 FS z dodatnią wagą, granice selektora i analiza kodu selekcji. |
| QA06 | TAK | Pełny bank, exact rational metrics, 8/10/12 FS z dodatnią wagą, granice selektora i analiza kodu selekcji. |
| QA07 | TAK | Pełny bank, exact rational metrics, 8/10/12 FS z dodatnią wagą, granice selektora i analiza kodu selekcji. |
| QA08 | TAK | Pełny bank, exact rational metrics, 8/10/12 FS z dodatnią wagą, granice selektora i analiza kodu selekcji. |
| SE03 | TAK | Dokładne wagi i publiczny SDK PASS; jeden tryb base, koszt 1, eksport 100049 rekordów. |
| SE04 | TAK | Dokładne wagi i publiczny SDK PASS; jeden tryb base, koszt 1, eksport 100049 rekordów. |
| SE05 | TAK | Dokładne wagi i publiczny SDK PASS; jeden tryb base, koszt 1, eksport 100049 rekordów. |
| QA09 | NIEZWERYFIKOWANE | Brak duplikatów/przesunięć; lokalny publiczny SDK akceptuje ID od zera. Aktualny prywatny uploader nie został sprawdzony. |
| QA10 | NIEZWERYFIKOWANE | Eksport scale100 i krok10 poprawne; produkcyjne kwoty portfela scale1000000 niewdrożone. |
| QA11 | NIEZWERYFIKOWANE | Publiczny SDK commit a6dccd86… PASS; brak uploadu i analizy ACP. |
| QA12 | TAK | Cały bank ma kompletne dane i poprawne przejścia, sumy i cap; wykonano exact replay selektora. B05 dotyczy odporności UI na podmienioną odpowiedź. |
| QA13 | TAK | Cały bank ma kompletne dane i poprawne przejścia, sumy i cap; wykonano exact replay selektora. B05 dotyczy odporności UI na podmienioną odpowiedź. |
| QA14 | TAK | Cały bank ma kompletne dane i poprawne przejścia, sumy i cap; wykonano exact replay selektora. B05 dotyczy odporności UI na podmienioną odpowiedź. |
| QA15 | NIEZWERYFIKOWANE | Źródła/bank i nowy audytowy ZIP zgodne, rebuild identyczny; brak identyfikacji finalnej paczki produkcyjnej dostarczonej do ACP. |
| SE06 | NIE | Lokalny Python i /api/*; brak produkcyjnego RGS, authenticate/play/end-round i stawek z auth. |
| SE07 | NIE | Lokalny Python i /api/*; brak produkcyjnego RGS, authenticate/play/end-round i stawek z auth. |
| SE08 | NIE | Lokalny Python i /api/*; brak produkcyjnego RGS, authenticate/play/end-round i stawek z auth. |
| SE09 | NIE | Lokalny Python i /api/*; brak produkcyjnego RGS, authenticate/play/end-round i stawek z auth. |
| QA16 | NIE | Waluta PLN wpisana w UI i pełne stawki PLN; brak wielowalutowego kontraktu portfela RGS. |
| QA17 | NIEZWERYFIKOWANE | B03 lokalnie naprawione i sprawdzone: stawka oraz postęp FS zachowane; produkcyjne recovery RGS nadal niedostępne. |
| QA18 | NIEZWERYFIKOWANE | Lokalny retry zwykle bezpieczny; B01 ujawnia lukę zapisu. Brak produkcyjnej ścieżki recovery RGS. |
| QA19 | NIEZWERYFIKOWANE | Lokalne testy HTTP/network PASS; end-round, sesje i awarie produkcyjnego RGS nie są dostępne. |
| QA20 | TAK | Zakres lokalny: regresje współbieżności/idempotencji oraz nowe awarie zapisu i odzyskiwanie w dwóch kartach przechodzą. |
| QA21 | TAK | B05 naprawione: walidacja całych przejść i sum; odrzucenie uszkodzonej odpowiedzi zachowuje request ID. Awaria odczytu portfela również go zachowuje. |
| QA22 | NIEZWERYFIKOWANE | W testowanej konsoli brak ostrzeżeń/błędów przy zwykłym UI; brak produkcyjnych tokenów/RGS do sprawdzenia. |
| SE10 | TAK | Zakres lokalny: tabela, RTP i limit obecne; uzupełniono brakujące zasady Wildów i remisów. Nie jest to akceptacja platformy. |
| SE11 | TAK | B02 naprawione: wynik rundy jest historyczny, bieżący portfel pobierany osobno; sumy wygranych zachowane. |
| SE12 | NIEZWERYFIKOWANE | Spacja i potwierdzenie AUTO sprawdzone. Aktualny frontend nie zawiera aktywnego audio/mute; test docelowego dźwięku niemożliwy. |
| SE13 | NIE DOTYCZY | Jeden tryb base kosztujący 1×; brak trybu kosztującego ponad2×. |
| SE14 | NIEZWERYFIKOWANE | B04 naprawione, pięć viewportów bez uciętych kart i pozaekranowych kontrolek. Fizyczny dotyk i rzeczywisty popout platformy pozostają do sprawdzenia. |
| SE15 | NIEZWERYFIKOWANE | Logika normal/quick/turbo/instant przechodzi; pełnej oceny czytelności kwot i kombinacji przy maksymalnym tempie nie zakończono. |
| SE16 | NIEZWERYFIKOWANE | Testowane zasoby lokalne kompletne; hosting/CDN produkcji i prawa do finalnych materiałów niepotwierdzone. |
| SE17 | NIE | Wybór EN działa, lecz lang z adresu uruchomienia jest ignorowany; brak kompletnego kontraktu językowego platformy. |
| QA23 | TAK | Ustawienia prezentacji nie wpływają na selekcję matematyki; skin jest mapowaniem tych samych kodów. Nie jest to pełna macierz zmian na każdym etapie bonusu. |
| QA24 | TAK | 13 testów AUTO i30 network VM obejmują STOP po bieżącej rundzie, retry i brak automatycznego restartu po awarii. |
| QA25 | NIEZWERYFIKOWANE | Prawdziwa runda max: kwota i trwała informacja poprawne. Podgląd linii pokazuje wartości surowe bez rozdziału części objętej cap; ocena komunikacji pozostaje otwarta. |
| QA26 | TAK | UI rozróżnia przegraną, częściowy zwrot, zwrot stawki i zysk; scenariusz0,60PLN przy2PLN pokazuje częściowy zwrot. |
| QA27 | NIEZWERYFIKOWANE | Viewporty, przewijanie tabeli i dostępne kontrolki sprawdzone; brak pełnych testów dotyku, tła na fizycznym urządzeniu i docelowego audio. |
| QA28 | TAK | Scenariusze są oznaczone i nie obciążają salda; tools ukryte bez studio. To izolacja lokalnego demo, brak zatwierdzonej paczki produkcyjnej. |
| SE18 | NIE | Brak trybu replay platformy. replay=true jest ignorowane; dostępne pozostają zwykłe SPIN/AUTO i portfel demo. |
| SE19 | NIE | Brak trybu replay platformy. replay=true jest ignorowane; dostępne pozostają zwykłe SPIN/AUTO i portfel demo. |
| SE20 | NIE | Brak trybu replay platformy. replay=true jest ignorowane; dostępne pozostają zwykłe SPIN/AUTO i portfel demo. |
| SE21 | NIE | Brak trybu replay platformy. replay=true jest ignorowane; dostępne pozostają zwykłe SPIN/AUTO i portfel demo. |
| SE22 | NIE | Brak trybu replay platformy. replay=true jest ignorowane; dostępne pozostają zwykłe SPIN/AUTO i portfel demo. |
| QA29 | NIE | Brak replay i brak bonus-cap w banku. Są dodatnie rekordy8/10/12FS, middle i max bazy. |
| QA30 | NIEZWERYFIKOWANE | Brak wersjonowanego odtwarzania historycznych wyników RGS. |
| SE23 | NIE | social=true ignorowane, brak pełnych zamian słownika i obsługi SC/GC; waluta stale PLN. |
| SE24 | NIE | social=true ignorowane, brak pełnych zamian słownika i obsługi SC/GC; waluta stale PLN. |
| SE25 | TAK | Pełna runda stanowi jeden niezależnie wybrany book; brak jackpot/gamble/continuation/cashout w aktualnym silniku. |
| SE26 | NIEZWERYFIKOWANE | Jest opis pochodzenia grafik. Nie wykonano prawnego clearance, weryfikacji unikalności nazwy ani pełnego przeglądu treści. |
| QA31 | NIEZWERYFIKOWANE | Jest opis pochodzenia grafik. Nie wykonano prawnego clearance, weryfikacji unikalności nazwy ani pełnego przeglądu treści. |
| SE27 | NIE | Zasady mają notę o RTP/demo; brak kompletnego docelowego disclaimeru o awariach/recovery/rozstrzygnięciu RGS. |
| SE28 | NIEZWERYFIKOWANE | Brak dostępu do finalnego zgłoszenia, kafelka i stanów Approved/Active w ACP; brak dowodu zamrożenia/akceptacji konkretnej wersji. |
| SE29 | NIEZWERYFIKOWANE | Brak dostępu do finalnego zgłoszenia, kafelka i stanów Approved/Active w ACP; brak dowodu zamrożenia/akceptacji konkretnej wersji. |
| SE30 | NIEZWERYFIKOWANE | Brak dostępu do finalnego zgłoszenia, kafelka i stanów Approved/Active w ACP; brak dowodu zamrożenia/akceptacji konkretnej wersji. |
| SE31 | NIEZWERYFIKOWANE | Brak dostępu do finalnego zgłoszenia, kafelka i stanów Approved/Active w ACP; brak dowodu zamrożenia/akceptacji konkretnej wersji. |
