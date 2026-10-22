# POLSKA GUROM — audyt zgodności ze Stake Engine

Data: 19 października 2026 r. Zakres: aktualne `polska_gurom_v0_2`, `test-interface`, obie paczki ZIP oraz oficjalna publiczna dokumentacja i walidator SDK odczytane tego dnia.

## Werdykt

**Nie wszystko zgadza się jeszcze z wymaganiami Stake Engine.** Lokalna matematyka v0.2 jest spójna ze swoją specyfikacją, a podstawowe testy przechodzą. Obecny projekt pozostaje prototypem matematycznym z lokalnym testerem. Dwa problemy wymagają decyzji matematycznej przed finalizacją animacji: niezgodny krok wypłat oraz praktycznie nieosiągalny reklamowany max win 5000×. Do publikacji potrzebne są także eksport wyników, integracja RGS i uzupełnienia interfejsu.

To audyt lokalny i porównanie z oficjalnymi źródłami. Nie wykonywano uploadu do ACP, serwerowej walidacji Stake ani testów rzeczywistego portfela. Nie zmieniono implementacji, dokumentów projektu, paczek ZIP ani plików `sources/`. Nowe dowody i raporty zapisano w katalogu tego audytu.

## Potwierdzone zgodności

| Obszar | Wynik obecnej implementacji |
|---|---|
| RTP | Nominalnie 96,00%; dokładnie przed limitem 95,99999998267222%. Wpływ limitu jest mniejszy niż 5,21 × 10⁻⁴⁶ stawki na rundę. Spełnia ogólny zakres RTP 90–98% w aktualnej dokumentacji. |
| Dodatnia wypłata | 29,7086953% rund; wypłata powyżej stawki 17,8895236%. Nie należy nazywać każdej dodatniej wypłaty zyskiem. |
| Bonus | Średnio co 196,549763 rundy; zgodny z lokalnym celem 150–250. |
| Plansza i linie | 5×3, 20 odrębnych, zawsze aktywnych linii; minimum 3 zgodne symbole od lewej. |
| Wild i Scatter | Jedna najlepsza interpretacja na linii; Wild nie zastępuje Scattera. Scatter liczony przed ekspansją. |
| Darmowe obroty | 3/4/5 Scatterów → 8/10/12 FS; mnożnik ×4 tylko dla linii; bez retriggerów. |
| Ekspansja | Szansa 21,6905037% na FS, jednostajny wybór jednego z bębnów 2/3/4, niezależnie od planszy. |
| Niezależność zakładów | Brak jackpotu, gamble, wcześniejszego cashoutu i trwałego postępu wpływającego na wynik. Stan salda i historii w lokalnym testerze nie jest sam w sobie naruszeniem niezależności wyniku zakładów. |
| Rozliczenie limitu | Suma kredytów odpowiada wypłacie; limit pełnej rundy 5000× działa. Osiągalność w wymuszonym poprawnym przebiegu potwierdzona, częstość pozostaje problemem opisanym niżej. |
| Podstawowy tester | Scenariusze nie zmieniają salda, natychmiastowe ponowienie tego samego żądania nie pobiera stawki drugi raz, STOP zatrzymuje kolejne autoobroty; obsługiwana spacja i trzy języki PL/EN/DE. |
| Paczki | ZIP matematyki: 31 plików, ZIP testera: 13 plików; poprawne CRC, zgodna zawartość z aktualnymi plikami roboczymi. |

Liczby są wynikiem ponownego obliczenia, nie przepisaniem poprzednich raportów. Zgodność z lokalnymi celami nie wystarcza do approval platformy.

## Problemy wymagające rozwiązania

### SE-01 — krok wypłat nie przechodzi publicznego walidatora SDK

**Priorytet: blokada kompatybilności aktualnego SDK.** Silnik rozlicza setne całkowitej stawki (`PAYOUT_SCALE = 100`) i pozwala na wypłaty 0,32×, 0,48×, 0,75×, 1,25×, 2,66× itd. Aktualny oficjalny `verify_lookup_format` wymaga całkowitych nieujemnych wartości, dodatniej wypłaty co najmniej 10 oraz `payout % 10 == 0`. Przy skali 100 oznacza to krok 0,10×.

Świeża enumeracja wykazała **7 808 220 / 60 466 176 = 12,9133683% wszystkich płatnych rund**, które nie uruchamiają bonusu i już samodzielnie naruszają ten krok. Jest to dolne ograniczenie dla całego modelu; nie obejmuje kolejnych możliwych niezgodności końcowej wypłaty bonusu. Naturalny seed 17 daje 0,32×: dwie linie po 0,16×.

Źródło projektu: [config.py](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/polska_gurom_v0_2/polska_gurom/config.py), linie 9–12 i 29–32; [game.py](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/polska_gurom_v0_2/polska_gurom/game.py), rozliczenie wyników. Dowody: [extra_checks.json](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/stake_engine_2026_10_19/math/extra_checks.json), [test_results.json](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/stake_engine_2026_10_19/math/test_results.json). Oficjalne źródło: [rgs_verification.py, verify_lookup_format](https://github.com/engineio/math-sdk/blob/main/utils/rgs_verification.py#L94).

Dokumentacja formatu opisuje skalę 100, ale nie wyjaśnia tej dodatkowej restrykcji. Nie wykonano zdalnego uploadu, dlatego nie twierdzimy, że RGS odrzucił naszą paczkę. Konflikt z bieżącym publicznym walidatorem jest jednak konkretny. Potrzebna jest korekta tabeli/rozkładu albo jednoznaczne potwierdzenie przez platformę obsługi setnych w docelowym pipeline. Proste zaokrąglenie lub przemnożenie jednostek zmieni znaczenie wypłat i RTP; po zmianie trzeba ponownie skalibrować model.

### SE-02 — max win 5000× jest skrajnie rzadszy niż przewidują kryteria

**Priorytet: poważny problem modelu przed approval.** Kod potrafi ograniczyć osiągalny surowy przebieg 8618,22× do 5000×. Jest to osiągalność kombinatoryczna. Analityczna, zaokrąglana w górę granica prawdopodobieństwa daje jednak:

- P(wypłata ≥ 5000×) ≤ **1,249572330629 × 10⁻⁴⁷** na płatną rundę.
- P(co najmniej jedno takie trafienie w milionie naturalnych rund) ≤ **1,249572330629 × 10⁻⁴¹**.
- Nawet P(wypłata ≥ 1000×) ≤ **1,901661487750 × 10⁻⁹**, czyli rzadziej niż około raz na 526 mln rund.

Są to konserwatywne górne granice analityczne, nie oszacowanie z braku trafień w symulacji. Oficjalne [Math Requirements](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/math-requirements/%2Bpage.svx) wymagają realnej osiągalności maksymalnej wygranej i wskazują typowo częściej niż 1:10 mln, zależnie od wysokości. Oficjalna [checklist](https://github.com/engineio/docs/blob/main/static/mockchecklist.json) podaje 1:20 mln lub częściej. Dokumenty różnią się progiem, ale obecny rozkład jest bardzo daleko od obu wartości.

Dowody: [math_validation.json](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/stake_engine_2026_10_19/math/math_validation.json), sekcja `cap_bound`; niezależnie powtórzony rachunek [extra_checks.json](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/stake_engine_2026_10_19/math/extra_checks.json). Limit: [config.py](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/polska_gurom_v0_2/polska_gurom/config.py), linie 9–11. Potrzebna jest zmiana struktury/wag wysokich wyników lub sensowny niższy max win i ponowna walidacja. Dodanie wymuszonej maksymalnej rundy do biblioteki z nową wagą także zmienia opublikowaną matematykę.

### SE-03 — brakuje wymaganej paczki matematyki

**Priorytet: blokada publikacji.** Nie ma `index.json`, tabeli CSV wyników i wag ani `books_*.jsonl.zst`. `joint_counts.npz` oraz raport statystyczny nie zastępują biblioteki pełnych rund.

Wymagane są manifest trybów z kosztem oraz nazwami plików, CSV z ID/wagą/wypłatą i JSONL skompresowany Zstandard zawierający `id`, `events`, `payoutMultiplier`. Wypłaty oraz kolejność muszą zgadzać się pomiędzy CSV a books. Wyzwolony bonus należy zapisać jako część kompletnego niezależnego zakładu.

Dowód: [delivery_checks.json](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/stake_engine_2026_10_19/delivery_checks.json). Źródło: [Required Math File Format](https://engineio.github.io/math-sdk/rgs_docs/data_format/). Własny silnik i własny frontend są dozwolone; użycie Svelte/Pixi ani konkretnego SDK nie jest warunkiem samo w sobie.

### SE-04 — lokalne API nie realizuje cyklu RGS

**Priorytet: blokada uruchomienia na platformie.** Front korzysta z `/api/config`, `/api/state`, `/api/spin`, `/api/reset`. Lokalny serwer losuje i natychmiast rozlicza wynik. Brakuje parametrów uruchomienia `sessionID`/`rgs_url`, autoryzacji, odtwarzania wyniku otrzymanego z RGS, zamknięcia wygrywającej rundy oraz wznowienia aktywnej rundy.

W RGS dane wyniku przychodzą z `/wallet/play`; wygrywająca runda jest zamykana po prezentacji przez `/wallet/end-round`, a stawki i waluta wynikają z authenticate. Kwoty portfela są w skali 1 000 000, niezależnej od skali 100 mnożników matematycznych. Obecnych `*_cents` i kwot PLN nie można podłączyć bezpośrednio.

Źródło projektu: [server.py](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/server.py), linie 237–327; [app.js](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/web/app.js), linie 153–198 i 273–286. Wymagania: [RGS Requirements](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/rgs-requirements/%2Bpage.svx), [Authenticate](https://github.com/engineio/docs/blob/main/src/routes/docs/api/authenticate/%2Bpage.svx), [End Round](https://github.com/engineio/docs/blob/main/src/routes/docs/api/end-round/%2Bpage.svx).

Obecne retry działa przy natychmiastowym powtórzeniu w tej samej sesji. `pending` istnieje tylko w pamięci strony, reload nie kontynuuje animacji bonusu i domyślnie ustawia stawkę 2 PLN. Serwer pamięta 100 wyników; po wyparciu identyfikatora to samo żądanie może oznaczać nową płatną rundę. Stare buforowane odpowiedzi zawierają historyczne saldo. To ograniczenia testera, nie rozwiązanie recovery produkcyjnego. Dowód: [server_probe_results.json](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/stake_engine_2026_10_19/frontend/server_probe_results.json).

### SE-05 — brak replay platformy

**Priorytet: wymagane do approval.** Podgląd scenariuszy i JSON historii nie obsługuje URL replay. Potrzebna jest osobna ścieżka `replay=true`, pobranie wskazanego eventu przez `/bet/replay/{game}/{version}/{mode}/{event}`, odtworzenie całego przebiegu, Play/Play Again i wymagane informacje o koszcie i wyniku. Ten tryb nie może otwierać zakładu ani autoryzować portfela.

Źródło: [Bet Replay](https://github.com/engineio/docs/blob/main/src/routes/docs/api/bet-replay/%2Bpage.svx). Brak obsługi parametrów replay potwierdzony przeglądem całego aktualnego `app.js`.

### SE-06 — autoplay zaczyna się jednym kliknięciem

**Priorytet: konkretna niezgodność UI.** Domyślnie wybrane jest 25 obrotów. Kliknięcie AUTO od razu ustawia licznik i wywołuje `spin()` bez potwierdzenia. Sam wybór liczby obrotów nie jest krokiem potwierdzającym.

Źródło projektu: [index.html](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/web/index.html), linia 59; [app.js](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/web/app.js), linia 254. Dodać okno/panel z liczbą obrotów i kosztem oraz oddzielnym potwierdzeniem startu. Zatrzymanie auto działa prawidłowo. Wymaganie: [Frontend Requirements](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/frontend-requirements/%2Bpage.svx).

### SE-07 — brak RTP w informacjach dostępnych graczowi

**Priorytet: wymagane uzupełnienie przed approval.** Zasady opisują bonus, Wild, Scatter i limit 5000×, ale nie podają RTP 96,00%. `/api/config` również go nie przesyła. RTP w plikach matematycznych nie zastępuje informacji w grze. Brakuje też wymaganego disclaimera produkcyjnego; instrukcję przycisków trzeba uzupełnić odpowiednio do finalnego UI.

Źródło projektu: [app.js](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/web/app.js), `ruleText` dla PL/EN/DE i generowanie zasad w linii 228; [server.py](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/server.py), linie 237–247. Wymagania: [Frontend Requirements](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/frontend-requirements/%2Bpage.svx), [Game Disclaimer](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/disclaimer/%2Bpage.svx).

### SE-08 — waluty, stawki i social nie są jeszcze obsługiwane

**Priorytet: wymagane w integracji; social dotyczy Stake.us.** Tester ma siedem stawek w pełnych PLN i na sztywno formatuje walutę jako PLN. Brakuje poziomów stawek z authenticate, obsługi innych walut, parametru `social=true` i tokenów SC/GC.

Tryb social wymaga angielskiego niezależnie od `lang`, odpowiednich nazw w każdym elemencie UI, zasadach, komunikatach i replay oraz wyświetlania SC/GC bez znaku dolara. W EN występują m.in. `Bet` i `Paytable`. Tekstów wymagających wariantów social nie należy trwale wtapiać w grafiki.

Źródło projektu: [server.py](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/server.py), linia 40; [app.js](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/web/app.js), linie 10 i 28. Wymagania: [RGS Requirements](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/rgs-requirements/%2Bpage.svx), [Social Mode](https://github.com/engineio/docs/blob/main/src/routes/docs/reference/social-mode/%2Bpage.svx).

### SE-09 — komunikat limitu znika, a surowe należności wyglądają jak wypłata

**Priorytet: poprawić przed efektami wygranej.** Silnik prawidłowo oddziela surowe należności od kwot faktycznie zaksięgowanych. Front po osiągnięciu limitu pokazuje komunikat, ale cykliczny podgląd linii nadpisuje go opisem „Wypłata tej linii”. W teście ostatni FS miał kredyt 0, a opis wskazywał 4 PLN i mnożnik ×4. Suma rundy i saldo pozostały poprawne.

Źródło projektu: [app.js](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/web/app.js), linie 92–103 i 185–189. Dowód logiczny na wymuszonym poprawnym przebiegu: [presentation_probe_results.json](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/stake_engine_2026_10_19/frontend/presentation_probe_results.json). Komunikat limitu powinien pozostać widoczny, a surowe kwoty muszą mieć jasny opis i nie uruchamiać efektu sugerującego dodatkową wypłatę.

### SE-10 — zmiana języka podczas rundy podmienia licznik

**Priorytet: błąd prezentacji.** Wybór języka pozostaje aktywny podczas `busy`; `translate()` odtwarza sumę i podpis z poprzedniej historii, a nie z aktualnie animowanej rundy. Sonda potwierdziła zmianę bieżącego licznika 123,45 PLN na 0,00 PLN przy wciąż trwającej rundzie. Rozliczenie serwera się nie zmienia.

Źródło projektu: [app.js](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/web/app.js), linie 115–129, 235–238 i 257. Dowód: [presentation_probe_results.json](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/stake_engine_2026_10_19/frontend/presentation_probe_results.json). Trzeba zachować stan prezentowanej rundy przy tłumaczeniu albo zablokować zmianę do jej końca.

### SE-11 — trzy symbole nie zgadzają się z GDD

**Priorytet: ustalić przed zamawianiem/generowaniem finalnych grafik.** GDD przypisuje P1=Pierogi, P2=Bocian, P3=Szabla, a manifest i tester P1=Lilia, P2=Kielich, P3=Korona. Kody i wypłaty są takie same, zatem nie jest to błąd RTP. Jest to rozbieżność między dokumentacją projektu a aktualną warstwą wizualną. Żadnego wariantu nie uznano w tym audycie automatycznie za docelowy.

Źródła: [GDD](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/polska_gurom_v0_2/docs/GAME_DESIGN_DOCUMENT.md), linia 9; [symbols.json](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/web/assets/symbols.json), linie 6–8. Ujednolicić wybrany zestaw w grafikach, nazwach, zasadach i specyfikacji.

### SE-12 — audio, CDN i ekrany wymagają końcowej weryfikacji

**Status: etap do wykonania, częściowo niezweryfikowany.** Obecny tester nie implementuje dźwięków ani przycisku wyciszenia. Wraz z efektami trzeba dodać mute i własne audio. Finalne grafiki i fonty muszą być dostarczane z zasobów gry na CDN platformy; import z lokalnych plików w testerze jest tylko narzędziem roboczym.

CSS zawiera widoki mobilne i redukcję ruchu, lecz tego dnia nie potwierdzono działania układu w prawdziwej przeglądarce: dostępna przeglądarka nie połączyła się z lokalnym adresem testera (`ERR_CONNECTION_TIMED_OUT`). Poprzedni raport z 18.10 nie jest nowym testem. Po zmianach wymagane są aktualne kontrole desktop/mobile/popout S/M, czytelności w fastplay, brakujących assetów i zachowania całego bonusu po resize/reload.

Własność/licencje i jakość finalnych assetów oraz zgodność treści trzeba ocenić na gotowym zestawie. Źródło: [Frontend Requirements](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/frontend-requirements/%2Bpage.svx), [Approval](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/%2Bpage.svx).

## Wykonane sprawdzenia i ograniczenia dowodów

- Ponownie uruchomiono 20/20 istniejących testów matematyki; obejmują m.in. 100 000 sekwencji symboli, reguły bonusu, osiągalność capu i deterministyczność.
- Od nowa wyliczono 60 466 176 naturalnych plansz oraz trzy stany ekspansji. Sprawdzono dokładną masę, momenty, Scatter i zgodność konfiguracji. Po wyliczeniu nowe histogramy porównano ze starymi: identyczne.
- Osobno porównano rzeczywisty silnik z niezależnym skalarnym oraklem na 1000 planszach bazowych i 3000 stanach FS. Wszystkie zgodne.
- Ponownie uruchomiono 9/9 istniejących testów serwera HTTP; składnia `app.js` poprawna.
- Dodatkowe testy logiki prezentacji użyły oryginalnego `app.js` w minimalnym modelu DOM oraz rzeczywistych/wymuszonych poprawnych wyników silnika. Nie są testem renderowania, dotyku ani przeglądarki.
- Nowa symulacja rzeczywistego silnika: 100 000 rund, seed 20261019, RTP próbki 96,28928%, 512 bonusów, dodatnia wypłata 29,756%, maksimum 304,76×. Próbka jest zgodna z teorią; nie rozstrzyga rzadkich zdarzeń ani approval. [Wynik](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/stake_engine_2026_10_19/math/simulation_engine_100k.json).
- Sprawdzono zgodność istniejących ZIP z aktualnym kodem i brak plików publikacyjnych. [Wynik](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/stake_engine_2026_10_19/delivery_checks.json).

Szczegóły: [raport matematyki](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/stake_engine_2026_10_19/math/REPORT_PL.md), [raport frontendu](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/stake_engine_2026_10_19/frontend/RAPORT_FRONTEND_PL.md), [aktualne oficjalne wymagania](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/stake_engine_2026_10_19/OFICJALNE_WYMAGANIA.md).

Ogólne kryteria approval trzeba odróżnić od ostrzeżeń oceny 3-star w `verify_mode_volatility`: np. jego limit RTP 96,7% nie zastępuje ogólnego zakresu 90–98%. Dokumentacja podaje także dopuszczalną różnicę RTP trybów 0,5 p.p., podczas gdy kod SDK ostrzega dopiero powyżej 0,05 w ułamku RTP, czyli 5 p.p. Zielony walidator nie wystarcza do oceny wszystkich warunków. Obecnie jest jeden płatny tryb, więc ta różnica nie zmienia werdyktu. Nie klasyfikowano flag `config.jurisdiction` jako osobnej pewnej niezgodności, ponieważ ich aktualny opis API każe je ignorować; obowiązkowość social ma odrębne potwierdzenie.

## Kolejność dalszych prac

1. Rozstrzygnąć precyzję wypłat oraz realny max win, następnie ponownie przeliczyć RTP i rozkład finalnej biblioteki wyników.
2. Ustalić docelowe przypisanie P1/P2/P3 i kontrakt zdarzeń rundy: plansza, Scattery, ekspansja, wygrane linii, faktyczne kredyty, limit, bonus i wynik końcowy.
3. Zbudować wymagany eksport i integrację RGS z prawidłowymi jednostkami, recovery i replay.
4. Uzupełnić autoplay, informacje dla gracza, waluty/social i dwa potwierdzone błędy prezentacji.
5. Na tym kontrakcie przygotować finalne grafiki, animacje i audio, z mute, wersjami tekstów oraz czytelnością desktop/mobile/popout. Wykonać końcowy test w środowisku Stake przed zgłoszeniem approval.

Koncepcje artystyczne można opracowywać już teraz. Finalne sekwencje wygranych i bonusu powinny opierać się na uzgodnionym modelu wypłat i zdarzeń.
