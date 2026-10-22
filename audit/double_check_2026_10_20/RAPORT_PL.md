# Podwójna kontrola gry i wymagań Stake Engine

Data: 20.10.2026. Badana matematyka: **0.4.1-weighted-12fs**.

**Wynik: rachunki, mechanika i dostarczone wyniki są zgodne. Paczka pozostaje lokalnym demonstratorem; integracja produkcyjna Stake jest niekompletna.**

## Co sprawdzono ponownie

1. Niezależny evaluator napisany na potrzeby tego audytu przeliczył wszystkie **100 048 wyników** z eksportu, nie wywołując produkcyjnego evaluatora wygranych. Sprawdził linie, WILD, Scattery przed rozwinięciem, opadanie i nowe symbole, kaskady, bonusy 8/10/12, mnożnik ×4 tylko dla linii, limit całej rundy i sumowanie kredytów. Wynik: PASS.
2. Wagi i wypłaty z CSV przeliczono dokładnie jako liczby całkowite i ułamki. Osobno sprawdzono odpowiadające im książki Zstandard, metadane i identyfikatory. Wynik: PASS.
3. Wszystkie **300 144 rekordy trzech histogramów** sprawdzono dwiema drogami: Python/Fraction oraz osobnymi zapytaniami SQLite. Zgadza się każda suma rund, wypłat, kwadratów wypłat i wariantów bonusu. Wynik: **100/100 kontroli dowodów PASS**.
4. Odtworzono wszystkie **160 mln pierwotnych losowań** z oryginalnymi ziarnami, inną wielkością partii i innym algorytmem mapowania biletów na wyniki. Zgadza się licznik każdego wyniku i początkowy/końcowy stan RNG we wszystkich trzech seriach. Są to powtórzenia tych samych strumieni, a nie nowe niezależne eksperymenty.
5. Wykonano rzeczywistą ponowną kompilację całej matematyki do osobnego folderu audytu. `index.json`, skompresowane książki, CSV wag i `selection.json` są identyczne bajtowo z dostarczonym eksportem. `mathematics.json` różni się wyłącznie czasem wykonania kompilacji. Pliki działającej gry pozostały nietknięte.
6. Ponownie wykonano **135/135 testów regresji**, bez pominięć: silnik 10, API serwera 10, pokrycie bonusów 11, autospin 13, logika awarii 30, HTTP/TCP 17, paczka przenośna 27, API 12 FS 10 i interfejs 12 FS 7. Testy interfejsu w Node sprawdzają prawdziwy kod z minimalnym DOM i wirtualnym transportem; nie są testem renderowania ani portfela Stake.
7. Ponownie uruchomiono niezmodyfikowany publiczny walidator SDK przypięty do commitu `a6dccd86de740cc5d318079483cb6204cc5c19bc`. Sprawdzono hashe jego źródeł. Wynik PASS, bez ostrzeżeń. Nie jest to test prywatnego uploadera ani approval.
8. Sprawdzono dashboard i samodzielny HTML, **166 kopii raportów**, zachowanie **139 historycznych dowodów** oraz **19/19 plików gry ZIP**. Są zgodne bajtowo ze źródłami. Archiwalnych serii nie doliczono do bieżących wyników.

## Potwierdzone liczby

| Parametr | Wynik |
|---|---:|
| Dokładne RTP | **24/25 = 96%** |
| Suma wag | 1 000 000 000 000 |
| Liczba różnych pełnych wyników | 100 048 |
| Niezerowe wypłaty | 29,4433510567% płatnych rund |
| Częstość dowolnego bonusu | 0,496993554% |
| Bonus 8 FS / 3 Scattery | 473 wyniki; 0,4679041094% |
| Bonus 10 FS / 4 Scattery | 29 wyników; 0,028687567% |
| Bonus 12 FS / 5 Scatterów | 24 wyniki; **0,0004018776%**, około 1:248 832 |
| Maksymalna wygrana | 5000×, średnio 1:8 000 000 |
| Wariancja wyniku w wielokrotnościach stawki | 48,71660045279382 |

| Pierwotna seria, ponownie odtworzona | RTP | Trafienia 12 FS |
|---|---:|---:|
| 10 mln | 96,171822% | 53 |
| 50 mln | 96,1249922% | 230 |
| 100 mln | 96,0104817% | 374 |

**Zastrzeżenie statystyczne:** RTP wszystkich trzech serii mieści się w 95% paśmie odniesienia. Nie dotyczy to każdej pojedynczej częstości bonusu: 230 trafień 12 FS w 50 mln przekracza górną granicę centralnego przedziału liczby trafień 174–229; 29 172 trafienia 10 FS w 100 mln przekracza przedział 28 356–29 020. Są to odtwarzalne wyniki losowania, nie rozbieżność między raportem a danymi. Łączny test czterech kategorii bonusowych dla 160 mln ma p≈0,1542. Nie zmieniano wag ani ziaren, żeby dopasować wyniki do przedziałów. Pełne statystyki, także pozostałe kategorie, są w `evidence/bonus_sampling_addendum.json`.

## Zgodność z dokumentacją Stake

| Obszar | Ocena |
|---|---|
| Format index/CSV/Zstandard, skala wypłat, zgodność ID i wypłat | PASS lokalnie |
| RTP 90–98%, dodatnie prawdopodobieństwo reklamowanego maksimum, liczba wyników i hit rate | Warunki liczbowe spełnione |
| Reguły gry: 8/10/12 FS, ×4, kaskady, limit 5000× | Zgodne z przeliczonymi wynikami |
| Brak zakupu bonusu i Double Chance | Prawidłowo opisany; funkcje te nie są obowiązkiem Stake |
| Portfel i cykl rundy prawdziwego RGS | **Niezaimplementowane — blokuje publikację gry** |
| Replay wymagany przez platformę | **Niezaimplementowany — blokuje approval** |
| Wszystkie stawki, waluty i precyzja kwot RGS | **Niezaimplementowane** |
| Social mode dla stake.us | **Niezaimplementowany; wymagany dla tego rynku** |
| Docelowy build na CDN, mini-player/mobile, audio, oryginalność i prawa do assets | Do kontroli docelowej wersji i review; obecny audyt nie przyznaje PASS |

### Konkretne braki przed publikacją

**1. Połączenie z RGS i wznowienie.** `test-interface/web/app.js:222` wysyła rundy do lokalnego `/api/spin`, a `:490` wczytuje lokalne `/api/config` i `/api/state`. Nie ma obsługi parametrów `rgs_url`/`sessionID`, uwierzytelnienia portfela ani zamknięcia aktywnej rundy. `test-interface/server.py:335` rozlicza fikcyjną wygraną przed animacją. Produkcyjny frontend musi obsługiwać authenticate → play → end-round dla aktywnych rund oraz odtwarzać rundę zwróconą przy ponownej autoryzacji. Lokalne testy ponawiania żądań nie sprawdzają tego kontraktu. [Wymagania RGS](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/rgs-requirements/%2Bpage.svx), [opis przepływu RGS](https://stake-engine.com/docs/rgs).

**2. Waluty i drobne stawki.** `test-interface/server.py:40` zawiera stałe stawki od 1 PLN, a `test-interface/web/app.js:62` formatuje wyłącznie PLN i grosze. RGS przesyła kwoty jako liczby całkowite w skali 1 000 000; stawki i ich krok pochodzą z authenticate. Docelowo trzeba obsłużyć małe nominały oraz dokładnie pokazywać drobne wygrane: 0,01 jednostki × 0,1 = 0,001, bez obcięcia do zera. Obecny portfel demo jest poprawny dla dozwolonych pełnych złotych, lecz nie nadaje się do bezpośredniego podłączenia zamiast adaptera RGS. [RGS — kwoty i stawki](https://stake-engine.com/docs/rgs).

**3. Replay.** W źródłach frontendowych nie ma obsługi `replay=true` ani `/bet/replay/{game}/{version}/{mode}/{event}`. Lokalna historia i podgląd wyniku nie zastępują odtwarzania platformowego bez sesji i bez możliwości stawiania zakładów. [Oficjalny wymagany replay](https://github.com/engineio/docs/blob/main/src/routes/docs/api/bet-replay/%2Bpage.svx).

**4. Parametry uruchomienia i social mode.** Języki PL/EN/DE istnieją w demo, ale nie są pobierane z parametrów uruchomienia platformy. Brakuje rozróżnienia social=true oraz właściwych tekstów i oznaczeń dla stake.us. To osobny wymóg tego rynku, a nie błąd RTP. [Social mode](https://github.com/engineio/docs/blob/main/src/routes/docs/reference/social-mode/%2Bpage.svx).

**5. Końcowy przegląd UI i zasobów.** Potrzebny jest test docelowej paczki z CDN w małym mini-playerze i na urządzeniach mobilnych, sprawdzenie dźwięku/wyciszania, czytelności fastplay, zasobów i ich praw. Tego nie dowodzi zgodność matematyki ani minimalny DOM testów automatycznych. [Frontend Requirements](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/frontend-requirements/%2Bpage.svx).

### Ważne rozróżnienia

- **8/10/12 FS to nasze zasady gry**, nie narzucona liczba obrotów przez Stake. Dokumentacja wymaga spójności zasad, wyniku i prezentacji.
- Model końcowy losuje kompletne książki według wag. Rozkład naturalnego generatora kandydatów nie jest tym samym rozkładem: proporcje 8/10 FS zachowano z próbki 473:29, a 12 FS skalibrowano do około 1:248 832. Jest to jawna kalibracja skończonego modelu, nie dowód odtworzenia wszystkich naturalnych częstości.
- 24 legalne książki 12 FS zapewniają dostępność tego bonusu. Nie oznacza to wyczerpania wszystkich naturalnych wyników tego bonusu.
- Kryteria jakości zmienności i różnorodności podlegają review. Spełnienie progów liczbowych i brak ostrzeżeń SDK nie dają gwarancji zatwierdzenia.
- Dokumentacja opisuje payout w skali 100; użyty SDK sprawdza dodatkowo krok 10, czyli 0,1×. Eksport spełnia oba warunki. Nie mylić tego ze skalą kwot portfela 1 000 000.

Podstawy matematyczne: [Math Requirements](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/math-requirements/%2Bpage.svx), [How RGS Works](https://github.com/engineio/docs/blob/main/src/routes/docs/architecture/how-rgs-works/%2Bpage.svx), [publiczny walidator SDK](https://github.com/engineio/math-sdk/blob/a6dccd86de740cc5d318079483cb6204cc5c19bc/utils/rgs_verification.py). Oficjalne źródła porównano ponownie 20.10.2026.

## Dowody i granice audytu

Nowe raporty są w `math/`, `regression/`, `evidence/` i `rebuild_results.json`. Zachowano oryginalne raporty, matematykę, paczkę gry i opublikowany dashboard. W dwóch skryptach QA dodano wyłącznie wybór katalogu wynikowego, żeby kolejne kontrole nie nadpisywały wcześniejszych dowodów. Pierwsze uruchomienie testu API pominęło opcjonalny przypadek eksportu; test ponowiono z `--require-exported` i końcowy raport zawiera 10/10 PASS, zero pominięć. Końcowe 135/135 obejmuje ten pełny przebieg.

Nie kontaktowano się z prawdziwym portfelem, nie wykonywano zakładów pieniężnych i nie przesyłano gry do approval. Audyt potwierdza dostępne lokalne właściwości i wskazuje pozostałe prace integracyjne.
