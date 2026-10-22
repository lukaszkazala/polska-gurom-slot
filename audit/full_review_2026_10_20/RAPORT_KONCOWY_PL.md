# POLSKA GUROM — pełny audyt gry i matematyki

**Wersja: 0.5.0-any-start. Domknięcie: 21.10.2026. Badana gra: test-interface-any-start.**

**Wynik: nie wykryto błędów obliczania wypłat w całym aktualnym banku. Wykryto błędy odporności rozliczeń, stanu interfejsu, układu i dokumentacji. Gra jest lokalnym demonstratorem; nie ma kompletnej integracji pozwalającej uznać ją za gotową do publikacji na Stake Engine.**

Przeprowadzono audyt, dopisano izolowane testy reprodukujące luki i utworzono dowody. Kod gry oraz materiały sources nie były zmieniane. Zgodność źródeł z dowodami sprawdzono ponownie 21.10.2026.

## 1. Co faktycznie sprawdzono

| Kontrola | Wynik i zakres |
|---|---|
| Istniejące testy Python | 47/47: HTTP 10, kaskady 10, bonus 12 API 10, network 17 |
| Istniejące testy JavaScript | 53/53: AUTO 13, network 30, bonus 12 frontend 7, any-start 3; rzeczywisty app.js w Node VM z atrapami DOM/API |
| Pełna matematyka | 100 049/100 049 rund, 212 009 etapów, 107 598 przejść, 367 959 wypłat linii; 6 582 479 asercji |
| Wszystkie ciągi jednej linii |100000 kombinacji 10 symboli na 5 polach; 0 rozbieżności |
| Selekcja według wag |200098 skrajnych biletów dla 100 049 przedziałów; 0 rozbieżności |
| Testy dodatkowe |14 prób serwera i 5 prób frontendu; część celowo potwierdza błędy, więc PASS reprodukcji nie oznacza poprawności gry |
| Limit i kaskady |Wymuszone częściowe wypłaty, cap bazy i cap bonusu oraz 10 000 naturalnych rund kontrolnych: PASS |
| Symulacje |100000 pełnych rund faktycznego selektora oraz 1 000 000 dodatkowych losowań wag |
| Publiczny walidator |PASS, bez ostrzeżeń; niezmodyfikowany SDK commit a6dccd86de740cc5d318079483cb6204cc5c19bc |
| Odtworzenie eksportu |Books, CSV, index, selection identyczne bajtowo; mathematics.json identyczny po pominięciu czasu budowania |
| Paczka przenośna |Nowy audytowy ZIP: 29 plików, CRC i zgodność źródeł poprawne, 27/27 smoke checks |
| Przeglądarka |Rzeczywista gra: 320×568,390×700,600×400, 802×829,1280×720; tabela, ustawienia, AUTO, scenariusz 0,60PLN, reload oraz parametry adresu |

Nie uruchamiano historycznych testów v0.2/v0.4 jako dowodu poprawności v0.5. Nie symulowano fizycznego telefonu, rzeczywistego portfela, prywatnego uploadera ani oceny ACP.

## 2. Matematyka końcowego rozkładu

Dla wag wᵢ i wypłat pᵢ zapisanych w skali 100: RTP=Σ(wᵢpᵢ)/(100·Σwᵢ·koszt). Tutaj suma wag=1000000000000, suma ważonych wypłat=96000000000000, koszt=1, zatem **RTP=24/25=96% dokładnie**. Wartość nie pochodzi z oszacowania Monte Carlo.

| Parametr | Dokładny wynik / wartość |
|---|---:|
| Rekordy z dodatnią wagą |100049 |
| Różne całkowite wypłaty |818 |
| Dodatnia wypłata |>0: 15,622691917%, średnio1: 6,40095 |
| Brak wypłaty |84,377308083% |
| Częściowy zwrot, 0<wygrana<stawka |5,2029732632% |
| Zwrot równy stawce |0,6133185822% |
| Zysk, wygrana>stawka |9,8064000716%, około1: 10,20 |
| Bonus dowolny |0,496993554%, średnio1: 201,20985 |
| 8 FS |473 rekordy; 0,4679041094%, 1: 213,719 |
| 10 FS |29 rekordów; 0,028687567%, 1: 3485,831 |
| 12 FS |24 rekordy; 0,0004018776%, 1: 248831,983 |
| Maksimum 5000× |4 rekordy, łączna szansa1: 8000000 |
| Wariancja / odchylenie standardowe |99,023619919066 /9,95106124587 stawki |
| Największa szansa pojedynczego rekordu |0,0022017407% |
| Ekspansje na wykonany FS |25,4510664211% |

RTP bazy wynosi 45,60774143986 punktu procentowego, a bonusu 50,39225856014 punktu. W tych liczbach bazy i bonusu zawarte są odpowiednio wypłaty Scatterów 0,6193794964 i 0,0187953025 punktu. Suma daje 96%. Średnia wypłata całej części bonusowej po wyzwoleniu to 101,39418943×.

Bank zawiera 61 726 płatnych rekordów, czyli 61,6958% liczby rekordów, ale po uwzględnieniu wag dodatni wynik trafia tylko w 15,6227% rund. Liczba rekordów i prawdopodobieństwo ich trafienia są różnymi miarami.

Generator kandydatów ma inne prawdopodobieństwa niż bank. Nieważona próbka 100 000 kandydatów ma zwrot 223,8389%; nie wolno używać tego generatora bez końcowych wag jako produkcyjnego modelu 96%. Obecny selektor korzysta z końcowych wag. 25% ekspansji dotyczy generatora, końcowy rozkład daje 25,4511%. Wybór bębnów 2/3/4 po ekspansji ma udziały 32,5964%/31,9140%/35,4896%.

### Rozkład wysokości wypłat

| Wypłata | Prawdopodobieństwo | Wkład w RTP, p.p. |
|---|---:|---:|
| 0× | 84.37730808% | 0 |
| (0,1)× | 5.202973263% | 2.220559286 |
| 1× | 0.6133185822% | 0.6133185822 |
| (1,5)× | 6.881726196% | 17.35686644 |
| [5,20)× | 2.333135329% | 19.46040418 |
| [20,100)× | 0.3719755576% | 20.75087469 |
| [100,500)× | 0.2159862632% | 33.15442141 |
| [500,1000)× | 0.0033892264% | 1.93034292 |
| [1000,2000)× | 2.5e-05% | 0.0496725 |
| [2000,3000)× | 0.0001% | 0.22516 |
| [3000,4000)× | 2.5e-05% | 0.07517875 |
| [4000,5000)× | 2.5e-05% | 0.10070125 |
| 5000× | 1.25e-05% | 0.0625 |

Wyniki≥100× występują w0,2195629896% rund i dostarczają37,0812% całego oczekiwanego zwrotu. Wyniki≥20× dostarczają58,6967% zwrotu. To wyjaśnia, dlaczego krótka sesja może znacznie odbiegać od96%. Samo maksimum dostarcza0,0625 punktu RTP, czyli0,0651042% oczekiwanego zwrotu.

### Symulacje i niepewność

100000 pełnych rund dało92,9898% zwrotu; przybliżony przedział normalny z próbki:87,6303–98,3493%. Dodatkowy milion losowań końcowych wag dał95,74338%; dokładne odchylenie rozkładu daje błąd standardowy około0,9951 punktu procentowego dla miliona rund. Rozkład ma ciężki rzadki ogon, więc normalne przedziały są przybliżeniem. Dokładne RTP wyznaczają wagi.

Przy częstości maksimum1:8mln brak trafienia w milionie losowań ma prawdopodobieństwo około88,25%. Brak maksimum w tej próbce nie jest niezaliczonym testem; jego częstość sprawdzono analitycznie.

## 3. Znalezione błędy i luki

P1 oznacza ryzyko błędnego rozliczenia przy opisanej awarii;P2 błąd zachowania/komunikacji lub odporności;P3 problem instrukcji/paczki. Próby z celową awarią są oznaczone osobno.

### B01 — P2: Wyjątek podczas serializacji może spowodować dwukrotne obciążenie tego samego żądania

**Odtworzenie.** W izolowanym teście asdict(result) zgłasza jednokrotnie MemoryError po zmianie salda. Pierwsza odpowiedź: HTTP 500; saldo 1 000 000 → 999 900 groszy, rounds=1, brak zapisanego wyniku. Ponowienie request_id=commit-gap obciąża kolejne 100 groszy: saldo 999 800, rounds=2.

**Skutek i granice dowodu.** To błąd atomowości lokalnego serwera. Został dowiedziony przez wymuszenie awarii; nie zaobserwowano go podczas zwykłych rund z poprawnymi wynikami. Nie dotyczy dowiedzionego działania portfela RGS, którego tutaj nie ma.

**Naprawa.** Przygotować pełny wynik i odpowiedź przed zmianą portfela, a zmianę salda, statystyk oraz wpis idempotencji zatwierdzać razem lub wycofywać razem.

[Miejsce w kodzie](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface-any-start/server.py:342) · [Dowód](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/server/extended_server_results.json)

### B02 — P2: Retry starej rundy cofa wyświetlane saldo i statystyki po grze w drugiej karcie

**Odtworzenie.** Karta A traci odpowiedź po rozliczeniu. Karta B gra kolejną rundę w tej samej sesji. A ponawia odczyt poprzedniego ID. Serwer poprawnie zwraca ten sam wynik, ale również historyczny portfel. UI A pokazuje 999 800 groszy i 1 rundę, podczas gdy faktyczny portfel ma 999 300 groszy i 2 rundy.

**Skutek i granice dowodu.** Brak podwójnej wypłaty w tym przypadku; gracz widzi nieaktualne saldo. Przy dalszej grze decyzja interfejsu o dostępnych środkach też może być oparta na starym stanie.

**Naprawa.** Oddzielić niezmienny wynik rundy od aktualnego portfela. Po recovery odczytać bieżący stan sesji i stosować monotoniczną wersję portfela.

[Miejsce w kodzie](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface-any-start/web/app.js:419) · [Dowód](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/frontend/extended_frontend_results.json)

### B03 — P2: Odświeżenie podczas animacji przywraca domyślną stawkę

**Odtworzenie.** Rozpocząć rundę za 100 PLN; po otrzymaniu odpowiedzi, gdy animacja nadal trwa, odświeżyć stronę. state.pending jest już skasowane. init ustawia currentBet na 10 000 groszy z historii, ale state.bet pozostaje 200 groszy. W przeglądarce potwierdzono analogicznie zmianę widocznej stawki 10 PLN → 2 PLN.

**Skutek i granice dowodu.** Rozliczenie starej rundy pozostaje prawidłowe. Wskaźnik stawki nie odpowiada ostatnio rozegranej rundzie; przebieg animacji nie jest wznawiany od przerwanego miejsca.

**Naprawa.** Zachowywać wybraną stawkę i etap prezentacji do zakończenia rundy; przy inicjalizacji uzgodnić state.bet, currentBet oraz wynik historyczny.

[Miejsce w kodzie](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface-any-start/web/app.js:378) · [Dowód](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/frontend/extended_frontend_results.json)

### B04 — P2: Karty bonusu są ucinane na pośrednich szerokościach

**Odtworzenie.** Otworzyć grę przy viewport 802×829. .feature-rail ma 108 px, ale odziedziczone grid-template-columns tworzy trzy kolumny po 28 px. Każda karta ma clientWidth 24 px; zawartość wymaga 38/38/72 px. Widać ucięte FREE SPINS, HUSSAR CHARGE i 5,000×.

**Skutek i granice dowodu.** Gracz nie może czytelnie odczytać opisu bonusu i maksimum. Przyczyną jest konflikt responsywnych reguł style.css: 108–109 z player-layout.css; obecne testy Node nie uruchamiają tych stylów.

**Naprawa.** Zresetować grid-template-columns na jedną kolumnę w pionowym rail albo zastosować wspólny breakpoint ukrywający/przenoszący cały panel.

[Miejsce w kodzie](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface-any-start/web/player-layout.css:18) · [Dowód](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/frontend/browser_checks_2026_10_21.json)

### B05 — P2: Nieprawidłowe współrzędne kaskady przechodzą walidację i przerywają animację

**Odtworzenie.** W odpowiedzi z prawdziwą rundą maksimum podmienić wyłącznie removed_positions pierwszego etapu na [[999,0]]. validateSpinResponse akceptuje tablicę, a tumbleTransition próbuje użyć nieistniejącego pola i zgłasza TypeError. pending jest już usunięte; rekord trafia do historii.

**Skutek i granice dowodu.** To luka wykazana przez podmianę odpowiedzi testowej. Wszystkie niezmienione rekordy finalnego banku mają poprawne współrzędne, więc nie jest to dowód uszkodzenia obecnego eksportu.

**Naprawa.** Przed zaakceptowaniem wyniku sprawdzać zakres i unikalność usunięć, strukturę/przesunięcia movements, zgodność plansz i sum etapów; odrzucić wadliwy wynik z zachowaniem możliwości recovery.

[Miejsce w kodzie](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface-any-start/web/app.js:281) · [Dowód](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/frontend/extended_frontend_results.json)

### B06 — P2: Zawieszone pobieranie ilustracji nie ma limitu czasu aplikacji

**Odtworzenie.** W teście pozostawić Image bez onload i onerror, przy poprawnych odpowiedziach API. Promise.all ilustracji nie rozwiązuje się i nie ma aktywnego timera kończącego inicjalizację. Osobny limit 15 sekund w api() nie obejmuje obrazów.

**Skutek i granice dowodu.** Fault injection potwierdza możliwość utknięcia przy ładowaniu. Przy prawidłowym pobieraniu lokalnych ilustracji ekrany załadowały się poprawnie; przeglądarka może niezależnie zakończyć rzeczywistą awarię własnym timeoutem.

**Naprawa.** Dodać limit czasu obrazów oraz bezpieczne przejście do symboli zastępczych z możliwością ponowienia.

[Miejsce w kodzie](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface-any-start/web/app.js:575) · [Dowód](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/frontend/extended_frontend_results.json)

### B07 — P2: Zasady nie określają remisów i interpretacji układu samych Wildów

**Odtworzenie.** Dla L1 L1 WILD WILD P2 dwa układy płacą po 0,6×: L1 od bębna 1 (cztery symbole) i P2 od bębna 3 (trzy symbole). Silnik wybiera lewy początek. Z kolei pięć Wildów interpretuje jako P4 i płaci 40× na linię. Odczytane zasady mówią tylko o najwyższej wypłacie i zastępowaniu symboli.

**Skutek i granice dowodu.** Nie znaleziono błędu algorytmu. Brakuje jawnego kontraktu dla gracza; rozstrzygnięcie remisu zmienia pola usuwane w następnej kaskadzie. Remisy odmiennych przedziałów występują w 50 z 100 000 możliwych ciągów.

**Naprawa.** Dopisać wybór najbardziej lewego początku przy równych wypłatach, regułę samych Wildów oraz jawne wykluczenie zastępowania Scattera.

[Miejsce w kodzie](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface-any-start/web/app.js:49) · [Dowód](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/math/independent_full_bank_results.json)

### B08 — P3: README wciąż zawiera nieaktualne instrukcje i liczby

**Odtworzenie.** Obok aktualnego nagłówka v0.5 pozostaje aktywne zdanie o dołączonym silniku v0.4.1, 100 048 rundach i polecenie przebudowy test-interface/build_math.py. Aktualna gra ma 100 049 rund i własny test-interface-any-start/build_math.py.

**Skutek i granice dowodu.** Osoba odtwarzająca matematykę może uruchomić kompilator innej wersji. Część README oznaczono historycznie, ale późniejsze bieżące instrukcje nadal są sprzeczne.

**Naprawa.** Przenieść opis v0.4 do wyraźnej historii; w części uruchomieniowej zostawić wyłącznie dane i polecenia v0.5.

[Miejsce w kodzie](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface-any-start/README_PL.md:60) · [Dowód](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/release/source_manifest.json)

### B09 — P3: ZIP nie zawiera START_UX.cmd polecanego na początku instrukcji

**Odtworzenie.** Zbudować ZIP oficjalnym lokalnym package_demo.py i porównać spis. Archiwum ma 29 plików; zawiera START.cmd, lecz nie START_UX.cmd. README rozpoczyna instrukcję od uruchomienia START_UX.cmd.

**Skutek i granice dowodu.** Polecona ścieżka startu z rozpakowanego ZIP nie istnieje. Alternatywny START.cmd jest obecny, a paczka przeszła 27 kontroli przenośnego uruchomienia.

**Naprawa.** Dołączyć uruchamiacz UX do ZIP albo dostosować pierwszą instrukcję do faktycznie dostarczonego START.cmd.

[Miejsce w kodzie](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface-any-start/package_demo.py:28) · [Dowód](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/release/release_results.json)

## 4. Ograniczenia projektu matematycznego wymagające decyzji

**Znaczne przerwy między wysokimi wygranymi.** W finalnym banku nie ma wyników pomiędzy995,3 a1986,9×, 2018,4 a2968,3×, 3010,9 a4027,4× oraz4029,6 a5000×. Pomiędzy wysokimi progami występują małe grupy kilku scenariuszy. To rzeczywiste ograniczenie różnorodności banku; nie błąd sumowania. Publiczna dokumentacja zaleca kontrolę takich luk. [Wymagania matematyki](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/math-requirements/%2Bpage.svx).

**Maksimum jest osiągalne tylko w bazie.** Wszystkie cztery rekordy5000× pochodzą z bazowych receptur. Dodatnia szansa maksimum w bonusie wynosi0. Najwyższa cała runda z 8 FS ma528,8×, z 10 FS237×, z 12 FS328,9×. Ogólny limit5000× jest poprawny; wymuszone testy silnika potwierdzają jego działanie w bonusie. Nie należy jednak przedstawiać bonus-cap jako scenariusza dostępnego w obecnym banku. Jeżeli taka ścieżka ma być częścią projektu, potrzebne są nowe poprawne pełne rundy z dodatnią wagą oraz ponowna kalibracja.

**Mała liczba wariantów rzadkich funkcji.**12 FS ma 24 kompletne realizacje, a maksimum 4. Wagi nie zwiększają różnorodności ich przebiegu. Nie stwierdzono dominacji pojedynczego wyniku w całej grze, ale rzadkie funkcje mogą powtarzać te same sekwencje przy dużej liczbie odtworzeń.

## 5. Brakujące elementy wersji produkcyjnej

Obecny frontend wysyła /api/config,/api/state,/api/spin do lokalnego serwera. Nie ma uruchomienia według sessionID/rgs_url, uwierzytelnienia, portfela produkcyjnego ani kończenia rundy przez RGS. Są to brakujące implementacje, a nie zaliczone integracje. [Przepływ RGS](https://stakeengine.org/docs/rgs).

Parametr replay=true jest ignorowany: nadal dostępne są zwykłe SPIN, AUTO i saldo demo. Brakuje odczytu konkretnego wyniku z endpointu replay, trybu bez portfela i odtwarzania wersji historycznej. [Wymagania replay](https://github.com/engineio/docs/blob/main/src/routes/docs/api/bet-replay/%2Bpage.svx).

Parametry lang i social z adresu również nie tworzą wymaganego kontraktu uruchomieniowego. Język wybrany w ustawieniach działa, lecz waluta jest stale PLN; brak wielowalutowych stawek z auth, SC/GC i słownika social. W teście z social=true pozostał angielski napis Bet; ustawiony w URL lang=de nie zmienił zapisanej wersji EN. [Social mode](https://github.com/engineio/docs/blob/main/src/routes/docs/reference/social-mode/%2Bpage.svx).

Docelowe audio/wyciszenie, pełny disclaimer, prawa do finalnych zasobów, kafelek, hosting/CDN i statusy ACP pozostają do wdrożenia lub potwierdzenia. Lokalna walidacja formatu nie nadaje Approved/Active. Review dotyczy konkretnej finalnej wersji. [Core Requirements](https://stakeengine.org/docs/approval-guidelines).

## 6. Dowody, checklista i kolejność dalszych prac

[Pełna checklista81 punktów](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/CHECKLISTA_81_PL.md) · [Matematyka — niezależny raport](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/math/RAPORT_MATEMATYKA_PL.md) · [Serwer — raport](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/server/RAPORT_SERWER_PL.md) · [10 przykładów do inspekcji](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/math/DZIESIEC_PRZYKLADOW.md) · [Lista błędów JSON](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/BLEDY.json)

1. Naprawić atomowość zapisu rundy i dodać regresję oczekującą braku drugiego obciążenia po awarii.
2. Uzgodnić aktualny portfel po recovery i zachować stawkę/etap prezentacji przy reload.
3. Poprawić panel przy 802px, walidację współrzędnych i timeout ładowania ilustracji.
4. Uzupełnić jednoznaczne zasady, instrukcję i zawartość ZIP.
5. Podjąć decyzję o rozkładzie wysokich wygranych i możliwości maksimum w bonusie przed zamrożeniem matematyki.
6. Wdrożyć i przetestować prawdziwe RGS, replay, waluty i wymagane tryby jurysdykcyjne; dopiero na tej samej finalnej paczce wykonać upload oraz review ACP.

Nie wykonano napraw produkcyjnego kodu w ramach tego audytu. Gdy powstaną poprawki wpływające na matematykę lub kontrakt zdarzeń, konieczne będzie ponowne sprawdzenie zmienionej paczki; wyniki tego raportu dotyczą wyłącznie wskazanych skrótów.

## 7. Zrzuty ekranu

Błąd panelu przy pośredniej szerokości:

![Ucięty panel bonusu](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/frontend/browser_initial.png)

Prawdziwy telefoniczny viewport390×700 — przewijalna tabela wypłat:

![Tabela wypłat w390×700](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/frontend/real_paytable_390x700.png)

