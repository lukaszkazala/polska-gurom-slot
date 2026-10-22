# Audyt POLSKA GUROM — prototyp v0.1

Data: 18 października 2026 r.

**Wniosek:** obecny kod poprawnie realizuje opisaną matematykę prototypu przy konfiguracji `expansion_probability=0.25`. Odtworzono zapisane wyniki, a niezależne obliczenia potwierdziły RTP, częstość bonusu i reguły wypłat. Model nie spełnia docelowego RTP ani częstości trafień. Deklaracja maksymalnej wygranej wymaga doprecyzowania, testy są za słabe, a interfejs rundy nie zachowuje pełnego przebiegu bonusu.

Plików oryginalnego projektu nie zmieniono. Przeliczenie było audytem, bez strojenia bębnów, wypłat ani prawdopodobieństw.

## Co znajduje się w folderze

`polska_gurom_phase2_v0.1` zawiera 16 plików:

- konfigurację symboli, bębnów, 20 linii i wypłat (`polska_gurom/config.py`);
- generowanie układu, ocenę wygranych i bonus (`game.py`);
- obliczenia wartości oczekiwanych (`theory.py`);
- deterministyczny symulator i statystyki (`sim.py`);
- plik inicjalizacyjny pakietu oraz 12 funkcji testowych;
- README, konfigurację projektu, skrócony projekt gry, specyfikację matematyczną, PAR sheet i raport;
- wyniki trzech symulacji oraz wyniki teoretyczne w JSON.

W folderze nadrzędnym jest również oryginalny ZIP i sześć plików PNG w `grafiki`: dwie grafiki główne, dwie wersje podglądu gry, ramka symboli i BIG WIN. Grafiki nie są połączone z silnikiem; w paczce nie ma działającego frontendu ani integracji ze Stake Engine.

## Ustalenia wymagające działania

### 1. Model nie osiąga założeń matematycznych

| Parametr | Wynik niezależnego obliczenia | Założenie projektu |
|---|---:|---:|
| Całkowite RTP | **80,541664%** | około 96% |
| RTP gry podstawowej | 74,452998% | około 73,5% |
| Wkład bonusu do RTP | **6,088666%** | około 22,5% |
| Dowolna dodatnia wypłata w rundzie | **49,622101%** | 25–30% |
| Częstość bonusu | 0,508777% — raz na 196,549763 rundy | raz na 150–250 rund |
| Średnia liczba Free Spinów na bonus | 8,090047 | 8/10/12 według Scatterów |
| Średnia suma wypłat Free Spinów na bonus | 11,967258× | brak osobnego targetu |

Do docelowego RTP brakuje **15,458336 punktu procentowego**. Większość różnicy dotyczy bonusu. To rezultat obecnych parametrów, a nie wykryty błąd sumowania w kodzie. Dokumentacja uczciwie oznacza tę wersję jako prototyp bez zamrożonej matematyki.

Samo zwiększenie częstości Hussar Charge nie wystarczy: przy ekspansji w każdym Free Spinie RTP wyniosłoby **89,614138%**. Przy niezmienionych bębnach i tabeli wypłat osiągnięcie 96% tą drogą wymagałoby prawdopodobieństwa ekspansji 152,790409%, co nie jest możliwym prawdopodobieństwem. Potrzebna jest zmiana ekonomii wypłat/bonusu lub bębnów, z ponownym wyznaczeniem całego rozkładu.

Hit frequency oznacza w tym kodzie **każdą wypłatę większą od zera**, również mniejszą niż stawka. Nie jest to częstość zysku netto. W zapisanej symulacji miliona rund 29,0543% wszystkich rund zwracało dodatnią kwotę mniejszą od stawki.

### 2. 5000× jest limitem technicznym, lecz nieosiągalną wygraną

GDD:13 oraz PAR_SHEET:11 podają „Max Win 5000×”. W kodzie istnieje prawidłowy ogranicznik do 5000×, jednak obecne bębny i wypłaty nie mogą do niego dojść.

Wyczerpująca enumeracja **36⁵ = 60 466 176** układów gry podstawowej oraz układów z wymuszonym bębnem Wild dała:

| Zdarzenie | Rzeczywista maksymalna wypłata |
|---|---:|
| Sam płatny obrót, przed doliczeniem bonusu | 168× |
| Pojedynczy Free Spin | 249,15× |
| Cała runda z 8 Free Spinami | 2044,40× |
| Cała runda z 10 Free Spinami | 2526,50× |
| Cała runda z 12 Free Spinami | **3037,30×** |

Maksimum rundy to **47,50× z obrotu z pięcioma Scatterami + 12 × 249,15×**. Nie można użyć 168× jako składnika tego samego maksimum, ponieważ układ dający 168× nie uruchamia 12 Free Spinów. Uwzględniono więc zależność wypłaty podstawowej od liczby Scatterów.

Odtworzono również konkretny osiągalny układ przez oryginalne `play_round()`. Zwrócił 3037,3000000000006; końcówka jest zwykłym skutkiem reprezentacji `float`. Dokładny wynik to 3037,30×.

Należy określić w dokumentacji osobno „limit wypłaty: 5000×” i „osiągalne maksimum bieżącej konfiguracji: 3037,30×” albo zmienić model, jeżeli 5000× ma być rzeczywiście osiągalne.

### 3. Istniejące testy nie chronią najważniejszych reguł

Wszystkie 12 oryginalnych funkcji testowych przeszło. Jednak wszystkie 12 przechodzi również po każdej z następujących, osobno wprowadzonych zmian w pamięci procesu:

| Kontrolowane uszkodzenie | Wynik oryginalnych testów |
|---|---:|
| Podwojenie wszystkich wypłat linii | 12/12 przechodzi |
| Wyzerowanie wypłat Scatterów | 12/12 przechodzi |
| Usunięcie faktycznej zamiany bębna na Wild | 12/12 przechodzi |

Przyczyny: `tests/test_math.py:28–34` sprawdza dolne granice przez `>=`, wiersz 43 tylko `>`; wiersze 50–55 sprawdzają liczbę Scatterów i Free Spinów bez ich wypłaty; wiersze 57–65 sprawdzają obecność numeru ekspansji bez weryfikacji zmienionego układu i kwoty wygranej.

Potrzebne są testy z dokładnymi oczekiwanymi kwotami, test rzeczywistej ekspansji każdego dozwolonego bębna, zachowania Scatterów, braku retriggerów i sumowania całej rundy. Limit należy sprawdzać na wymuszonej rundzie przekraczającej 5000×; obecny test sprawdza głównie samą funkcję `min`.

Te próby nie zmieniały plików projektu i nie oznaczają, że obecne wypłaty są podwojone lub wyłączone. Pokazują, że testy nie wykryją takich regresji.

### 4. Brakuje walidacji prawdopodobieństwa ekspansji

`evaluate_free_spin()` w `game.py:85–98` porównuje losową liczbę z przekazanym parametrem. `theoretical_metrics()` w `theory.py:45–55` używa parametru jako wagi średniej. Żadna funkcja nie odrzuca wartości poza [0, 1].

Konkretny przykład: dla `expansion_probability=1.5` teoria podaje RTP **95,662454%**, podczas gdy silnik zawsze wykonuje ekspansję i zachowuje się identycznie jak dla 1.0, czyli odpowiada modelowi o RTP **89,614138%**. Porównanie wyników symulacji z tym samym seedem potwierdza identyczność silnika dla 1.0 i 1.5.

To nie wpływa na bieżącą wartość 0.25. Może jednak prowadzić do błędnych wniosków przy strojeniu. Parametr powinien być skończoną liczbą w [0, 1], a liczba rund dodatnią liczbą całkowitą; błędne wejścia powinny być odrzucane jasno.

### 5. Wynik rundy nie wystarczy do wiernego pokazania bonusu

`game.py:101–111` zwraca wynik podstawowy, sumę bonusu i liczbę ekspansji. Nie zwraca układów bębnów, listy wygranych linii ani wyników poszczególnych Free Spinów. Wybrany bęben jest dostępny wewnątrz `evaluate_free_spin()`, ale `play_round()` go odrzuca.

W kontrolowanej próbie dwa bonusy z różnymi rozszerzanymi bębnami dały identyczny wynik publiczny rundy. Frontend nie odtworzy więc przebiegu wyłącznie na podstawie tego wyniku. Jest to luka interfejsu przed integracją, nie błąd obecnego RTP. Wynik rundy powinien zawierać pełną listę zdarzeń potrzebną do animacji i odtworzenia rozliczenia.

## Sprawdzenie reguł krok po kroku

1. **Losowanie.** Każdy z pięciu bębnów ma 36 pozycji; pozycja jest losowana niezależnie. Na ekran trafiają trzy kolejne symbole z zawijaniem paska. To prawidłowe okno bębna. Piętnaście widocznych komórek nie jest losowanych niezależnie: symbole w tej samej kolumnie są powiązane kolejnością paska.
2. **Linie.** Istnieje 20 różnych, poprawnie indeksowanych linii. Każda jest oceniana od pierwszego bębna w prawo. Minimalne trafienie ma długość 3. Wynik jednej linii to jedna najwyższa dopuszczalna wypłata; następnie wypłaty linii są sumowane.
3. **Wild.** Zastępuje osiem zwykłych symboli i nie zastępuje Scattera. Nie ma osobnej tabeli Wild. Dokumentacja jawnie pozwala rozliczać przedrostek samych Wildów jako najwyżej płatną interpretację zwykłego symbolu. Przykładowo `WILD WILD WILD L1 L2` płaci 2× jako trzy P4; nie sumuje tego z inną interpretacją. Wszystkie 100 000 pięciosymbolowych linii sprawdzono niezależnym wzorcem bez rozbieżności.
4. **Scatter.** Liczony jest na całym pierwotnym ekranie, niezależnie od linii. 3/4/5 płaci 1×/5×/20× i przyznaje 8/10/12 Free Spinów. Obecny pasek zawiera jeden Scatter, więc fizycznie w jednej kolumnie można zobaczyć najwyżej jeden; więcej niż pięć na całym ekranie nie wystąpi przy tej konfiguracji.
5. **Hussar Charge.** Każdy Free Spin ma 25% szansy na jeden pełny bęben Wild. Przy zdarzeniu bębny 2, 3 i 4 są wybierane z równym prawdopodobieństwem. Scatter jest rozliczany przed przykryciem bębna. Brak retriggerów działa zgodnie z dokumentacją; oryginalny układ wejściowy nie jest mutowany.
6. **Agregacja.** Wszystkie przyznane Free Spiny są rozgrywane i dodawane do wypłaty podstawowej. Łączna kwota jest ograniczana do 5000×. Sztuczny układ kontrolny potwierdził działanie ogranicznika przy przekroczeniu; nie jest to układ osiągalny z obecnych pasków.

Wypłaty w tej wersji są wielokrotnościami **całej stawki**, nie stawki podzielonej przez 20 linii. Kod jest w tym zgodny z tabelą i specyfikacją.

## Niezależne wyprowadzenie RTP

Przy jednym Scatterze na pasku długości 36, widocznym w trzywierszowym oknie dla trzech pozycji, prawdopodobieństwo Scattera na pojedynczym bębnie wynosi `3/36 = 1/12`. Liczba widocznych Scatterów `K` ma zatem rozkład dwumianowy:

`P(K=k) = C(5,k) × (1/12)^k × (11/12)^(5-k)`.

Z niego wynika `P(K≥3) = 0.005087770061728395`. Średnia liczba Free Spinów przypadająca na jeden płatny obrót wynosi `E[N] = 0.04116030092592592`.

Oczekiwana suma wypłat linii bez ekspansji: **0.7384817257172009×**. Oczekiwana wypłata Scatterów: **0.006048257458847736×**. Ich suma daje RTP podstawowe **0.7445299831760486**.

Średnia suma wypłat linii przy wymuszeniu bębna Wild wynosi:

- bęben 2: 4.281968021262003×;
- bęben 3: 4.281968021262003×;
- bęben 4: 2.4682320244627345×;
- średnia z trzech: 3.6773893556622466×.

Bębny są wybierane równomiernie, ale nie muszą mieć tej samej wartości oczekiwanej: ocena linii od lewej powoduje, że położenie wymuszonego Wilda ma znaczenie.

`E[FS] = 0.75 × 0.7384817257172009 + 0.25 × 3.6773893556622466 + 0.006048257458847736 = 1.47925689066231×`.

`RTP_bonus = E[N] × E[FS] = 0.06088665876641019`.

`RTP_total = RTP_base + RTP_bonus = 0.8054166419424589`.

Dokładny ułamek całkowitego RTP to **448823480141 / 557256278016**. Różnice w ostatnich cyfrach wobec `theory.json` wynikają wyłącznie z sumowania liczb zmiennoprzecinkowych.

Korelacje pomiędzy liniami nie unieważniają sumowania ich wartości oczekiwanych. Mają natomiast znaczenie dla częstości trafień i wariancji. Dokładną częstość trafień obliczono z fizycznych okien, nie zakładając niezależności linii; wynosi **370427/746496 = 49,6221011231%**.

`theory.py` nie uwzględnia obcięcia rozkładu wypłat na 5000×. Dla obecnego modelu jest to matematycznie obojętne, ponieważ fizyczne maksimum jest niższe. Po zwiększeniu wypłat należy tę własność ponownie sprawdzić; obcięty rozkład nie może być zastąpiony samą sumą nieobciętych średnich.

## Odtworzenie wyników i granice audytu

Python: 3.12.14. Użyto kodu z dysku D bez jego modyfikacji i seeda 20261015.

| Płatne rundy | Odtworzone RTP | Odtworzona częstość trafień | Porównanie z zapisanym JSON |
|---|---:|---:|---|
| 10 000 | 77,2715% | 49,4800% | zgodne |
| 100 000 | 80,33105% | 49,5490% | zgodne |
| 1 000 000 | 80,30868% | 49,6463% | zgodne |

Porównano wszystkie zapisane metryki, nie tylko RTP. Wariancja 5,59660465167 i odchylenie standardowe 2,36571440619 z miliona rund również się odtwarzają. To estymatory symulacyjne; **dokładna wariancja teoretyczna nie została niezależnie wyznaczona**. Sam opis „medium-high volatility” nie zawiera liczbowego kryterium akceptacji.

W środowisku nie było pakietu `pytest`. Wszystkie 12 testów są zwykłymi funkcjami z asercjami, bez fixture'ów lub parametryzacji; wykonano je bezpośrednio. Nie przedstawiam tego jako uruchomienia polecenia `pytest`.

W dodatkowej kontroli 100 000 rund porównano wypłaty z niezależnym rozliczeniem w jednostkach całkowitych 0,01×. Nie wykryto różnic kwot po przeliczeniu na te jednostki ani rozbieżności przedziałów wypłat dla tego seeda. Nie jest to pełny dowód braku wszystkich problemów `float` na granicach przedziałów.

Kontrola sum SHA-256 potwierdziła zachowanie wszystkich 16 plików oryginalnego projektu. Audyt nie obejmuje zgodności z aktualnym Stake SDK, certyfikacji, gotowości prawnej, kryptograficznego RNG ani nieistniejącego frontendu.

## Zalecana kolejność dalszej pracy

1. Wzmocnić dokładne testy wypłat, bonusu i agregacji oraz walidację parametrów.
2. Doprecyzować osiągalną maksymalną wygraną i docelowe miary zmienności.
3. Uzupełnić wynik rundy o układy, linie i historię każdego Free Spina.
4. Dopiero na tym fundamencie stroić bonus, tabelę wypłat i bębny do celów 96% RTP oraz 25–30% hit frequency.
5. Po każdej zmianie ponownie przeliczyć niezależne RTP, fizyczne maksimum, częstość trafień, rozkład i symulacje; sprawdzić ponownie wpływ limitu 5000×.

Dowody i skrypty odtwarzające kontrole znajdują się obok tego raportu, w folderze `audyt_v0.1`. Główne pliki dowodowe to `reproduction_summary.json`, `agent_math/independent_math_results.json`, `agent_math/exact_hit_results.json`, `agent_math/maximum_witness_results.json`, `agent_game/game_checks_results.json` i `agent_game/test_strength_results.txt`.
