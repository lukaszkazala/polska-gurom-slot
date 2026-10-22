# Audyt interfejsu — 19.10.2026

Zakres: bieżące `test-interface/server.py`, `web/app.js`, `web/index.html`, `web/style.css`, manifest symboli, README, istniejące testy i paczka ZIP. Implementacja nie została zmieniona. Wszystkie nowe pliki powstały w tym folderze audytu. Pliki `sources/` nie były modyfikowane.

## Ocena

Jest to działający lokalny tester matematyki v0.2, nie frontend połączony ze Stake Engine RGS. Można przygotowywać ilustracje symboli, ale przed utrwalaniem animacji i bonusowych sekwencji należy ustalić nazwy P1–P3 oraz poprawić dwa odtworzone problemy prezentacji. Integracja produkcyjna wymaga osobnego adaptera odpowiedzi i cyklu rundy.

## Ustalenia

1. **Brak integracji RGS, sesji uruchomieniowej i waluty platformy.** Frontend wywołuje wyłącznie własne `/api/config`, `/api/state`, `/api/spin`, `/api/reset`; nie odczytuje `sessionID`, `rgs_url` ani innych parametrów launch URL. Serwer sam losuje i księguje pełną rundę. Kwoty są centami lokalnego PLN, waluta jest wpisana na stałe, stawki 1/2/5/10/20/50/100 zł są zakodowane w serwerze. To jawnie opisane demo i nie należy interpretować go jako potwierdzenia zgodności wdrożeniowej.
   - `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/web/app.js:24`, `:31`, `:159`, `:278`
   - `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/server.py:40`, `:236`, `:275`, `:309`

2. **Odtworzony błąd prezentacji limitu 5000×.** Po zakończeniu rundy komunikat o limitowanej wypłacie zostaje nadpisany przy pierwszej automatycznej zmianie wyświetlanej linii. W wymuszonej, osiągalnej sekwencji z testów końcowy FS ma kredyt 0, ale panel wyświetla potem „Wypłata tej linii: 4,00 zł · ×4”. Suma rundy 5000,00 zł i saldo pozostają poprawne przy stawce 1 zł. Grafika wygranej musi odróżnić wynik surowy od zaksięgowanego; komunikat o limicie powinien pozostać widoczny poza cyklem linii.
   - `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/web/app.js:92`, `:102`, `:185`, `:188`
   - Dowód: `presentation_probe_results.json`, pole `cap_warning_overwritten_by_line_cycle`.

3. **Odtworzony błąd zmiany języka podczas animacji.** Wybór języka pozostaje aktywny przy `busy=true`. `translate()` przerysowuje planszę, panel linii i kwotę wygranej z poprzedniej historii, choć trwa nowy obrót/bonus. Sonda odtworzyła zmianę bieżącego „123,45 zł” na „PLN 0.00” z poprzedniej rundy. Nie wpływa to na matematyczne rozliczenie, ale może zepsuć prezentację i przyszłe efekty w połowie sekwencji.
   - `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/web/app.js:115`, `:235`, `:238`, `:257`
   - Dowód: `presentation_probe_results.json`, pole `change_language_during_spin`.

4. **Nazwy i grafiki P1–P3 różnią się od zatwierdzonego lokalnego GDD.** GDD podaje P1 Pierogi, P2 Bocian, P3 Szabla. Manifest, zastępcze ilustracje i README używają Lilia/Kielich/Korona. Kody i wypłaty się zgadzają, ale tematyka i opisy wymagają rozstrzygnięcia przed zamawianiem/generowaniem docelowych grafik.
   - `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/polska_gurom_v0_2/docs/GAME_DESIGN_DOCUMENT.md:9`
   - `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/web/assets/symbols.json:6`
   - `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/web/app.js:46`
   - `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/README_PL.md:38`

5. **Recovery jest lokalne i częściowe.** Ponowienie requestu bez przeładowania zachowuje `request_id`, a serwer księguje go tylko raz, dopóki wpis pozostaje w pamięci. Po odświeżeniu `pending` przepada; start odczytuje historię i pokazuje ostatnią planszę końcową, bez wznowienia przerwanego bonusu lub indeksu animacji. Nie ma stanu aktywnej rundy, potwierdzania jej zakończenia ani trwałego zapisu. Restart serwera, 24 h bezczynności lub usunięcie sesji usuwa recovery. Jest to akceptowalne ograniczenie opisanego lokalnego demo, ale nie zamiennik cyklu recovery RGS.
   - `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/web/app.js:21`, `:156`, `:162`, `:272`, `:280`, `:284`
   - `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/server.py:98`, `:106`, `:114`, `:325`

6. **Cache retry ma tylko 100 wyników wspólnie dla gry i preview.** Odtworzono: płatna runda A, 100 scenariuszy preview, ponowienie A z identycznym `request_id` → nowa płatna runda i drugie księgowanie. Inny odtworzony przypadek: po rundach A i B ponowienie A zwraca zapisane saldo/statystyki z A, chociaż rzeczywista sesja jest już po B. Dotyczy m.in. wielu kart tej samej przeglądarki. Obecne zapewnienie użytkownika, że retry nigdy nie pobierze stawki ponownie, wymaga ograniczenia do okresu istnienia wpisu lub wzmocnienia mechanizmu.
   - `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/server.py:44`, `:298`, `:303`, `:325`
   - `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/web/app.js:7`, `:166`, `:192`
   - Dowód: `server_probe_results.json`, pola `eviction_after_100_previews` i `cached_wallet_snapshot`.

7. **Błędy prezentacji nie zatrzymują auto.** Wyjątek z renderowania/animacji jest tylko logowany i pokazany jako toast; `finally` nadal dopisuje historię i planuje następną rundę AUTO. Przed rozbudową efektów warto wymagać zatrzymania auto przy takim błędzie i bezpiecznego pokazania zaksięgowanego wyniku.
   - `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/web/app.js:190`, `:197`

8. **Zasady UI nie pokazują teoretycznego RTP.** Zasady wyjaśniają linie, Scatter, FS, mnożnik i cap, ale nie podają nominalnych 96% z lokalnego GDD. Słownik zawiera nieużywane `sessionRtp`, co nie jest informacją o teoretycznym RTP gry. Produkcyjny panel zasad należy powiązać z ostatecznym zatwierdzonym wariantem matematyki.
   - `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/web/app.js:7`, `:229`
   - `C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/polska_gurom_v0_2/docs/GAME_DESIGN_DOCUMENT.md:3`

## Potwierdzone dobre zachowanie

- Świeże uruchomienie wszystkich 9 istniejących testów HTTP zakończyło się `OK`. Sprawdzają konfigurację, dokładne rozliczenie, separację sesji, scenariusze, historię 100 rund, reset, niewystarczające środki, cap oraz 8 równoległych retry tej samej rundy. Pierwsze uruchomienie zablokował sandbox (`WinError 10013`); powtórzenie z dopuszczonym lokalnym loopback przeszło. Nie jest to błąd implementacji.
- `node --check test-interface/web/app.js` — poprawna składnia.
- Dodatkowa sonda oryginalnego JavaScriptu z minimalnym DOM potwierdziła, że AUTO po jednej z dwóch rund zmniejsza licznik do 1, planuje tylko kolejną rundę, a STOP usuwa oczekujący timer bez nowego requestu.
- Serwer losuje wynik przed animacją; frontend nie losuje wypłat. Saldo jest księgowane raz na całą rundę i bonus, a grafika pokazuje wynik otrzymany z silnika.
- UI używa `free_spin_credits` do sumy bonusu i nie dodaje surowych wygranych ponad 5000× do salda.
- W scenariuszach saldo i statystyki pozostają bez zmian; normalne auto jest niedostępne dla scenariuszy.
- Wypłata mniejsza od stawki ma osobną etykietę „Częściowy zwrot stawki”; wygrane linie podają ID i wyróżniają opłacone pola, nie całe 5 pól przy trafieniu 3.
- Scatter jest obliczany na oryginalnym gridzie, a przy ekspansji jest pokazywany przed przerysowaniem WILD.
- Ukrycie okna zatrzymuje auto; rozpoczęta runda kończy prezentację. Zmiana stawki i scenariusza podczas rundy jest blokowana.
- Jest obsługa `prefers-reduced-motion` i przyspieszenia. Nie ma jeszcze systemu audio, regulatora głośności ani docelowych animowanych atlasów; to zakres przyszłych efektów, nie dowód niezgodności matematyki.
- Wszystkie 5 głównych plików testera w `POLSKA_GUROM_TESTER.zip` jest identycznych bajtowo z bieżącą implementacją (`server.py`, `web/app.js`, `web/style.css`, `web/index.html`, `README_PL.md`).

## Ograniczenia tej weryfikacji

Sondy JavaScript działają na minimalnym fake DOM z prawdziwymi fixture wyników silnika. Potwierdzają logikę kodu, nie układ CSS, zachowanie dotyku, dostępność na urządzeniach ani E2E w przeglądarce. Rodzic audytu próbował otworzyć lokalny tester w udostępnionej przeglądarce; zdalna przeglądarka nie ma dostępu do loopback komputera i zwróciła timeout. Dlatego mobile/desktop należy nadal sprawdzić na prawdziwej przeglądarce przed odbiorem grafik. Nie użyto starych raportów jako dowodu świeżego przejścia testów.

## Kolejność przed grafiką i efektami

1. Ustalić ostateczne motywy P1–P3, zachowując mapowanie kodów i kolejność siły wypłat.
2. Utrwalić kontrakt danych: kolejność reveal → Scatter → ekspansja → linie → zaksięgowany wynik; osobne kwoty surowe i kredyty; trwała informacja o cap.
3. Uporządkować zmianę języka i błąd animacji podczas aktywnej rundy.
4. Oddzielić panel testowy od docelowego launch/RGS, recovery i wymagań walutowych, przed uznaniem frontendu za wdrażalny.
5. Następnie wykonać odbiór na mobile/desktop i docelowych assetach, z wolnym trybem, szybkim trybem i ograniczeniem ruchu.
