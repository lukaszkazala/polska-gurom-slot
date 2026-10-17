# POLSKA GUROM — audyt zgodności z docelowym Stake Engine

Status modelu: **PROTOTYPE / NOT MATH-FROZEN**. Data audytu źródeł: **2026-10-17**.

Status integracji: **OFFICIAL SOURCE AUDIT COMPLETED / NOT SDK-RUN / NOT RGS-VALIDATED**.
W tej fazie nie wykonano integracji z SDK, eksportu plików publikacyjnych, optymalizacji wag ani publikacji.

## 1. Zakres i pochodzenie implementacji

Projekt jest nową implementacją z rekonstrukcją historycznych liczności symboli i tabeli wypłat. Nie jest wiernym odtworzeniem v0.1: nie odnaleziono oryginalnego kodu ani pełnych uporządkowanych pasków historycznej wersji. Własny evaluator bada interpretacje dla wszystkich ośmiu symboli regularnych i wybiera jedną najwyższą poprawną wypłatę na linię. Rozliczenia używają całkowitoliczbowej skali **100 jednostek = 1× TOTAL BET**. Brak automatycznego dostrojenia do celów matematycznych.

Niniejszy dokument ocenia zgodność koncepcji i lokalnego kontraktu danych ze źródłami publicznymi. Odczyt źródeł nie stanowi potwierdzenia przejścia testów zainstalowanego SDK ani akceptacji RGS/ACP. Nie uruchamiano SDK, jego przykładowych gier, walidatora RGS ani uploadu. Nie zweryfikowano zachowania docelowego frontendu.

## 2. Metoda i aktualność źródeł

Sprawdzono oficjalne strony Stake Engine oraz pliki oficjalnego repozytorium `engineio/math-sdk` z gałęzi `main`. Bezpośredni odczyt trzech stron dokumentacji zwracał powłokę JavaScript; treść była dostępna w wynikach wyszukiwania tych samych oficjalnych stron. Kod repozytorium odczytano z `raw.githubusercontent.com/engineio/math-sdk/main/`.

Odwołania `main` są ruchome. **Nie przypięto i nie uruchomiono lokalnego commitu SDK**. Z tego powodu dokument rejestruje datę odczytu i konkretne ścieżki, a nie deklaruje identyczności z przyszłą wersją SDK. Przed przyszłą integracją należy zapisać SHA rzeczywiście użytego commitu i ponownie wykonać jego kontrole. Nie korzystano z nieoficjalnych poradników ani forków jako źródeł wymagań.

## 3. Udokumentowany kontrakt plików RGS

Oficjalny [Math File Format](https://stake-engine.com/docs/math/math-file-format) opisuje minimalny zestaw jako: `index.json`, tabelę CSV oraz book w JSON Lines skompresowanym Zstandard. Manifest wskazuje dla każdego trybu jego `name`, `cost`, `events` i `weights`. Każda runda booka wymaga `id`, `events` i `payoutMultiplier`; odpowiadający wiersz CSV zawiera ID, wagę i tę samą wypłatę w całkowitych nieujemnych wartościach `uint64`. Skala wypłat wynosi 100: `1150` oznacza 11,50× przy koszcie trybu 1,0×.

Bieżący [kod generowania konfiguracji](https://raw.githubusercontent.com/engineio/math-sdk/main/src/write_data/write_configs.py) potwierdza klucze manifestu. Standardowy pipeline SDK tworzy również konfiguracje FE/BE i hashe. Powyższy opis dokumentuje istniejący kontrakt; **w tej fazie nie tworzy się ani nie deklaruje gotowego pakietu publikacyjnego**.

Docelowo wystarczy jeden płatny tryb `base` o koszcie 1× TOTAL BET. Free Spins stanowią część tej samej rundy i nie wymagają osobnego płatnego trybu. Tryb `bonus` z przykładów SDK jest trybem bonus buy i nie należy do zatwierdzonych zasad POLSKA GUROM.

## 4. Rozbieżność: precyzja modelu a bieżący walidator SDK

W odczytanym [utils/rgs_verification.py](https://raw.githubusercontent.com/engineio/math-sdk/main/utils/rgs_verification.py), funkcja `verify_lookup_format()` wymaga nieujemnych całkowitych payout i wag, minimalnej dodatniej wypłaty 10, warunku `payout % 10 == 0` oraz sumy wag nieprzekraczającej `uint64`. Przy skali ×100 odpowiada to krokowi końcowej wypłaty **0,10× TOTAL BET**. Tablice payout z books i LUT są porównywane w tej samej kolejności.

Dokumentacja formatu opisuje `uint64`, lecz nie ujawnia tego dodatkowego ograniczenia kroku. To rozbieżność pomiędzy odczytaną dokumentacją a kodem walidatora, której nie rozstrzygnięto testem RGS. Warunek dotyczy końcowej wypłaty rundy zapisanej w LUT; nie należy automatycznie przenosić go na każdą linię lub zdarzenie.

Historyczny paytable zawiera np. 0,25× i 3,50×. Dokładna wypłata rundy 0,25× miałaby wartość 25 w skali ×100 i nie spełniałaby odczytanego warunku modulo. Skala całkowitoliczbowa modelu prawidłowo zachowuje taką kwotę, lecz sama w sobie nie zapewnia zgodności publikacyjnej.

Faktyczne uruchomienie `python scripts/check_sdk_precision.py` znalazło osiągalną pełną rundę o wypłacie **0,45×**, czyli 45 jednostek. Seed `random.Random(20261017)`, indeks rundy 147 liczony od zera. Jej pełny trace zapisano w [`../reports/sdk_payout_step_witness.json`](../reports/sdk_payout_step_witness.json). Wartość 45 nie jest podzielna przez 10: **BLOCKED_BY_CURRENT_SDK_PAYOUT_STEP** względem odczytanego kodu walidatora. To konkretna niezgodność, a nie tylko możliwość wynikająca z jednej pozycji paytable. Nie uruchomiono SDK ani RGS; nie ustalono jeszcze pełnej częstości niezgodnych rund.

**Zasada projektu: nie zaokrąglać cicho wypłat i nie zmieniać paytable w adapterze.** Zmiana kroku lub zasad zaokrągleń zmienia matematykę i wymaga osobnej decyzji, analizy RTP, testów oraz nowej wersji konfiguracji. Do tego czasu integracja ma status **PAYOUT_STEP_COMPATIBILITY_UNRESOLVED**; wynik wykrywający niezgodne rundy powinien otrzymać status **BLOCKED_BY_CURRENT_SDK_PAYOUT_STEP**.

Ten sam moduł zawiera ostrzeżenia dotyczące statystyk zmienności oraz limitu RTP 0,967. Są to zaobserwowane kontrole kodu SDK, a nie pełna specyfikacja akceptacji platformy ani dowód, że nasz model je spełnia.

## 5. Jednostki paytable i własny evaluator

Aktualny [src/calculations/lines.py](https://raw.githubusercontent.com/engineio/math-sdk/main/src/calculations/lines.py) sumuje kwoty z paytable bez dzielenia przez liczbę linii. Dla tego interfejsu **nie jest potrzebna konwersja tabeli ×20**. Wartości projektu pozostają w mnożnikach TOTAL BET również dla pojedynczej linii. Konwersja ×20 miałaby zastosowanie wyłącznie do jawnie innego interfejsu wymagającego jednostek stawki liniowej B/20; przed użyciem należałoby udowodnić równoważność testem.

Nie należy podmieniać własnego evaluatora na SDK `Lines.get_lines()` bez porównania reguł. Kod SDK rozpatruje początkowy ciąg Wildów i pierwszy symbol niewildowy; możliwość osobnej wypłaty Wild-only zależy od wpisu Wild w paytable. Bez takiego wpisu same Wildy nie płacą jako najwyższy regularny symbol. Własna konwencja projektu sprawdza wszystkie symbole regularne i może nadać początkowym Wildom krótszą, wyżej płatną interpretację niż dalsze dopasowanie innego symbolu. Różnica jest zamierzonym, jawnym założeniem nowej implementacji.

## 6. Aktualne przykłady i ograniczenia ich ponownego użycia

| Przykład | Zaobserwowany zakres | Znaczenie dla projektu |
|---|---|---|
| `games/0_0_lines` | 5 bębnów, 3 rzędy, 20 linii; osobne Wild pays, multipliery, retriggery, inne nagrody FS i bonus buy | Referencja organizacji i zdarzeń; jego reguły nie stanowią zasad POLSKA GUROM. |
| `games/0_0_expwilds` | 5×5, 15 linii, trwające pomiędzy spinami expanded Wilds, możliwość wielu rozszerzeń, multipliery i dodatkowy superspin z nagrodami | Nie jest gotową implementacją Hussar Charge. |
| `games/template` | Puste wymiary/paytable i szkielet kodu; odczytany `run.py` zawiera `upload_data=True` | Wymaga świadomej konfiguracji; nie uruchamiać bez przeglądu skutków. |

Źródła przykładów: [lines config](https://raw.githubusercontent.com/engineio/math-sdk/main/games/0_0_lines/game_config.py), [lines state](https://raw.githubusercontent.com/engineio/math-sdk/main/games/0_0_lines/gamestate.py), [expwilds config](https://raw.githubusercontent.com/engineio/math-sdk/main/games/0_0_expwilds/game_config.py), [expwilds state](https://raw.githubusercontent.com/engineio/math-sdk/main/games/0_0_expwilds/gamestate.py), [template config](https://raw.githubusercontent.com/engineio/math-sdk/main/games/template/game_config.py), [template run](https://raw.githubusercontent.com/engineio/math-sdk/main/games/template/run.py). Wszystkie odczytano 2026-10-17; nie uruchamiano ich.

Projekt zachowuje jednorazowy Charge na maksymalnie jednym z bębnów 2/3/4, brak sticky, brak retriggerów, brak bonus buy i brak dodatkowych mnożników. Kopiowanie przykładów nie może wprowadzić ich mechanik.

## 7. Zdarzenia, plansze i odtwarzanie

Odczytany [src/events/events.py](https://raw.githubusercontent.com/engineio/math-sdk/main/src/events/events.py) używa plansz `board[reel][row]`, symboli w formie obiektów z nazwą i m.in. zdarzeń `reveal`, `winInfo`, `setWin`, `setTotalWin`, `finalWin` oraz zdarzeń FS. Opcjonalny padding zmienia indeksy wierszy pozycji wygrywających o jeden. Kwoty zdarzeń są skalowane ×100.

Przyszłe mapowanie musi jawnie odróżniać wewnętrzne wiersze 0–2 od ewentualnego paddingu. Pełny wynik lokalnej rundy powinien pozostać niezależnym źródłem prawdy: naturalna plansza, stop positions, oryginalne Scattery, Charge, plansza po ekspansji, win lines, surowe wypłaty, redukcja cap i wypłacone składowe. Nazwa własnego zdarzenia Charge byłaby kontraktem projektu, nie twierdzeniem o istniejącym API SDK. Nie wykonano takiego mapowania ani testów odtwarzania frontendu.

## 8. Naturalne prawdopodobieństwa a ważone books

Oficjalny [opis działania Math](https://stake-engine.com/docs/math) wyjaśnia, że RGS wybiera wcześniej przygotowany wynik według tabeli wag. Rozkład skończonego zestawu books jest zatem odrębną matematyką od naturalnego generatora bębnów.

[Quick Start](https://stake-engine.com/docs/math/quick-start) opisuje początkowe wagi 1 oraz przykłady wymuszające bonusy i max wins. Surowy udział wymuszonych wyników nie oznacza naturalnej częstości zdarzeń. W tej fazie wszystkie analizy odnoszą się do niezależnych naturalnych zatrzymań cyklicznych bębnów i jawnego losowania Charge; nie powstał ważony zestaw wyników docelowej gry.

Jeżeli w późniejszej, osobno zleconej fazie powstanie zestaw books, dla kosztu trybu 1× należy obliczyć bezpośrednio:

`RTP_books = sum(weight_i * payout_units_i) / (100 * sum(weight_i))`.

Częstość bonusu i trafień ma używać wag rund. Częstość Charge na Free Spin ma mianownik `sum(weight_i * liczba_FS_i)`, a średnia liczba Charge na bonus — ważoną liczbę uruchomionych bonusów. Trzeba również raportować rozkład wybranych bębnów oraz składowe base/bonus po cap. Nawet naturalnie próbkowany zestaw z wagami 1 definiuje skończony rozkład empiryczny; jego dokładne RTP nie jest dokładnym RTP generatora bębnów.

## 9. Warunki przyszłej integracji

Poniższe punkty są pracą na późniejszą fazę, nie deklaracją wykonania:

1. Przypiąć commit oficjalnego SDK i rozstrzygnąć krok payout z rzeczywistym walidatorem/platformą.
2. Zachować jeden wynik booka na pełną płatną rundę, obejmującą cały przyznany bonus i jeden wspólny cap 5000×.
3. Zweryfikować wymagane pola, uint64, sumę wag, zgodność ID, kolejność oraz identyczność payout w book/LUT; sprawdzić brak strat precyzji.
4. Udowodnić odtwarzalność zdarzeń i zgodność ich kwot z faktycznie przyznanymi składowymi po cap.
5. Policzyć odrębne statystyki końcowego ważonego zestawu i porównać je z naturalną matematyką, bez mieszania definicji.
6. Uruchomić kontrole SDK i zapisać rzeczywisty wynik, wersję oraz ograniczenia; następnie wykonać osobny przegląd integracyjny.

Nie nadano statusu Math Freeze, gotowości publikacyjnej ani zgodności zatwierdzonej przez Stake Engine. Ponieważ oficjalne źródła udało się odczytać, nie oznaczono dokumentacji jako całkowicie niedostępnej. Brak wykonania SDK i RGS jest niezależnym, jawnym ograniczeniem tego audytu.

## 10. Rejestr źródeł

Wszystkie poniższe źródła zweryfikowano w zakresie odczytu **2026-10-17**:

- [Math Quick Start](https://stake-engine.com/docs/math/quick-start) — przykłady, books/LUT, wymuszanie i rozdzielenie etapów.
- [Math](https://stake-engine.com/docs/math) — model statycznych wyników wybieranych przez RGS.
- [Math File Format](https://stake-engine.com/docs/math/math-file-format) — minimalny manifest, CSV, JSONL.Zstandard i skala payout.
- [Oficjalne repozytorium](https://github.com/engineio/math-sdk) — Python ≥3.12; Rust/Cargo przy optymalizacji.
- [SDK directory](https://stake-engine.com/docs/math/sdk-directory) — aktualne ścieżki przykładów i rola template.
- Konkretne pliki źródłowe podlinkowane w sekcjach 3–7 — zachowanie odczytanego kodu `main`, bez uruchomienia i bez przypiętego lokalnego commitu.
