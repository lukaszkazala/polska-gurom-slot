# POLSKA GUROM — tester v0.6.0-high-wins

Aktualna matematyka: **0.6.0-high-wins**, przebudowa wysokich wygranych **22.10.2026**. Standardowe uruchomienie to lokalne demo z wirtualnym saldem. Dodano klienta integracji Stake Engine RGS, replay zapisanych rund i osobne paczki do testów oraz wdrożenia interfejsu — szczegóły w **README_RGS_PL.md** w projekcie i paczce RGS_TEST. Integracja z rzeczywistym środowiskiem i zatwierdzenie ACP pozostają do potwierdzenia.

Język uruchomienia (`lang`), komunikaty PL/EN/DE i precyzja kwot: [instrukcja języków](README_JEZYKI_PL.md).

## Uruchomienie

Wypakuj całe archiwum. Uruchom **START_UX.cmd**, aby otworzyć grę pod **http://127.0.0.1:8772**. Alternatywny **START.cmd** używa portu **8765**. Oba uruchamiacze są w paczce ZIP.

Po aktualizacji zamknij poprzedni serwer przez Ctrl+C i uruchom grę ponownie z nowego folderu. Stary proces serwera nie wczytuje automatycznie poprawek Pythona.

Potrzebny jest Python 3.12 lub nowszy. Do uruchomienia demo nie trzeba instalować dodatkowych pakietów. Uruchamiacz może skorzystać z Pythona dołączonego do aplikacji Codex na tym komputerze. Pozostaw proces serwera aktywny; zakończ go przez Ctrl+C. Jeśli port jest zajęty, zamknij poprzedni serwer albo uruchom `python server.py --port 8766` z katalogu gry. `--no-browser` wyłącza automatyczne otwarcie strony.

Domyślny ekran pokazuje grę. Historia jest dostępna przez **Ustawienia → Historia rund**. **?studio=1** udostępnia dodatkowo scenariusze testowe. Scenariusze są wyraźnie oznaczone i nie zmieniają salda ani statystyk zwykłej gry.

## Obowiązujące zasady

- Plansza ma 5 bębnów, 3 rzędy i 20 zawsze aktywnych linii.
- Co najmniej 3 kolejne pasujące symbole mogą zaczynać się od dowolnego bębna. Wygrywają układy 1–3, 2–4 i 3–5; 4 i 5 symboli płaci według tabeli.
- Każda linia wypłaca jeden najwyższy wynik. Gdy kilka układów ma tę samą najwyższą wypłatę, wybierany jest początek najbardziej z lewej. Usuwane są tylko pola wybranego układu tej linii; pozostałe linie są oceniane osobno.
- Tabela pokazuje mnożniki całej stawki. Przy stawce 2 PLN trzy obwarzanki na jednej linii płacą 0,20 PLN. Scenariusz „3 obwarzanki na bębnach 2–4” zawiera dodatkowe wygrywające linie i daje łącznie 0,60 PLN.
- WILD zastępuje osiem zwykłych symboli, nigdy Scattera. Nie ma osobnej wypłaty własnej. Ciąg samych Wildów jest interpretowany jako P4 (Husarz), najwyżej płatny pasujący symbol: 3/4/5 Wildów płaci 1,6×/8×/40× całej stawki przed mnożnikiem bonusu.
- 3/4/5 Scatterów płaci 1×/5×/20× i w bazie przyznaje 8/10/12 darmowych obrotów. Scatter liczy się tylko na początkowej planszy danego obrotu, przed ekspansją Wilda. W bonusie płaci, ale nie przyznaje kolejnych obrotów.
- Po wygranej liniowej wygrywające pola znikają, pozostałe spadają w swoich kolumnach, a nowe wpadają od góry. Wspólne pole znika tylko raz. Uzupełnienia nie zawierają Scatterów. Kaskady nie pobierają następnej stawki.
- W darmowym obrocie ekspansja może zastąpić cały bęben 2, 3 lub 4 Wildami raz, na początku obrotu. Później obowiązują zwykłe zasady usuwania i opadania.
- Mnożnik ×4 dotyczy tylko linii w bonusie, również jego kaskad. Scatter nie jest mnożony.
- Limit 5000× obejmuje całą płatną rundę z kaskadami i bonusem. Osiągnięcie limitu kończy rundę, nawet gdy pozostały przydzielone darmowe obroty. Saldo dostaje wyłącznie wypłatę uznaną w tym limicie.
- Komunikat limitu pokazuje faktycznie przyznaną kwotę w walucie rundy. Bonus zakończony limitem wyjaśnia pominięcie pozostałych darmowych obrotów; licznik zachowuje pierwotny przydział, np. 2/8. Szczegóły ograniczonej wygranej rozróżniają wynik linii przed limitem i przyznaną wypłatę całego etapu. Dotyczy to także replay i osiągnięcia dokładnie 5000× bez redukcji.
- Nie ma zakupu bonusu ani Double Chance.

## Matematyka i eksport

Bank zawiera **100 343 różne pełne rundy**, wszystkie z dodatnimi wagami całkowitymi. Suma wag wynosi **1 000 000 000 000**. Dokładny zwrot wynosi **96%**, a maksimum **5000×** ma częstość **1:8 000 000**. Wypłaty mają krok 0,1× całej stawki. Są to parametry lokalnego eksportu, nie akceptacja platformy.

Maksimum występuje w bazie oraz w każdym wariancie 8/10/12 FS. Połowa łącznej masy maksimum pozostaje w bazie, a 25%/15%/10% trafia do 8/10/12 FS. Zachowano dokładne masy wejścia do bonusów. W zakresie 500×–5000× bank ma **297 różnych kwot**, a największa luka z brzegami wynosi **98,6×**.

Budżet RTP wypłat ≥500× pozostaje dokładnie **2,44355542032 p.p.** Część tego budżetu przesunięto do wyższych pasm, dlatego łączna częstość ≥500× wynosi około **1:47 374** zamiast wcześniejszego około **1:27 959**. Przebudowa nie zwiększa częstości wysokich wygranych ani nie gwarantuje lepszych krótkich sesji. Szczegółowy plan, porównanie i odbiór: `audit/high_wins_rebuild_2026_10_22/RAPORT_PL.md` w projekcie developerskim.

Losowania generatora kandydatów nie są finalnym rozkładem gry. Prawdopodobieństwa i RTP określają końcowe wagi kompletnych rund. Wybór skina, szybkości, języka lub urządzenia nie zmienia tych wag.

Folder **stake_math/** zawiera `index.json`, `books_base.jsonl.zst`, `lookUpTable_base_0.csv`, `selection.json` i `mathematics.json`. Lokalne demo losuje według tych samych wag i odtwarza wynik z `selection.json`; nie wymaga zstandard podczas zwykłej gry.

W repozytorium developerskim aktualny kompilator to **test-interface-any-start/build_math.py**. Z katalogu projektu uruchom `python test-interface-any-start/build_math.py`, a z katalogu tej gry `python build_math.py`. Odtworzenie eksportu wymaga pakietu zstandard i danych świadków wskazanych przez kompilator. Kompilator i testy nie są częścią przenośnego ZIP demo. Zmiana reguł wymaga ponownego zbudowania i sprawdzenia banku.

## Sterowanie i odzyskiwanie rund

### Dźwięk i czytelność wyników — 22.10.2026

Przycisk głośnika w prawym górnym rogu wycisza muzykę i wszystkie efekty, również podczas obrotu. Wybór jest zapamiętywany po odświeżeniu. Muzyka folk/disco startuje po pierwszym obrocie lub włączeniu dźwięku; bonus ma własną pętlę i sygnał wejścia. Częściowy i równy zwrot stawki mają neutralny sygnał. Fanfary dotyczą dodatniego wyniku netto, z mocniejszym sygnałem od 20× stawki. Ukryta karta milczy. W trybie błyskawicznym słychać tylko wynik całej rundy.

AUTO zachowuje wynik na ekranie przed kolejną rundą przez minimum 0,9 s dla zwrotu do wysokości stawki, 1,2 s dla wygranej netto, 1,8 s od 20× i 2,4 s dla maksimum. Dotyczy to turbo, trybu błyskawicznego i ograniczonych animacji. Wygrywająca kaskada ma minimum 450 ms na odczyt; dodatni wynik darmowego obrotu — 700 ms. Kwota końcowa jest większa i ma ciemne tło. Ręczne kliknięcie kolejnego obrotu pozostaje dostępne po ukończeniu rundy.

Szczegóły zasobów: `web/assets/audio/README.md`. Regresja dźwięku i czasu odczytu: `node qa/test_audio_readability.cjs`.

### Obroty i odzyskiwanie

- Przycisk obrotu lub spacja rozpoczyna rundę. Spacja jest pomijana w polach i otwartych oknach ustawień.
- Stawki demo: 1, 2, 5, 10, 20, 50 i 100 PLN. Saldo jest wirtualne; nie obsługuje wpłat ani prawdziwych pieniędzy.
- AUTO najpierw otwiera ustawienia. Po potwierdzeniu można wykonać 10, 25, 50, 100, 250 lub 500 płatnych rund. Każda obejmuje wszystkie swoje kaskady i cały bonus. STOP AUTO kończy serię po bieżącej pełnej rundzie.
- Normalna, szybka i turbo zmieniają tempo prezentacji. Tryb błyskawiczny pokazuje wynik całej rundy od razu. Ustawienia nie wpływają na wygrane.
- Po utracie odpowiedzi PONÓW ODCZYT korzysta z tego samego identyfikatora rundy. AUTO ma maksymalnie trzy próby odczytu. Ponowienie nie rozpoczyna drugiego płatnego obrotu.
- Wybrana stawka jest zapamiętywana. Oczekujący identyfikator i postęp prezentacji są przechowywane w pamięci tej karty do zakończenia animacji. Po odświeżeniu można ponowić odczyt i dokończyć ten sam wynik, z pominięciem w pełni pokazanych darmowych obrotów. Częściowo pokazany obrót może zostać odtworzony od początku. Przerwana seria AUTO nie startuje samoczynnie.
- Po odzyskaniu wyniku interfejs odczytuje bieżące saldo osobno, dzięki czemu historyczna odpowiedź rundy nie przywraca starego portfela po grze w drugiej karcie.
- Jeśli ilustracje nie załadują się w ciągu 15 sekund, gra przechodzi do symboli zastępczych. Odświeżenie pozwala ponowić ładowanie grafik.
- Saldo i historia są w pamięci serwera. Restart usuwa sesje. Stare żądania są odrzucane; należy rozpocząć nową sesję testową. Zapis w przeglądarce nie rozstrzyga rozliczenia.
- Historia przechowuje pełne szczegóły 100 ostatnich wyników. Starszy identyfikator nadal nie może ponownie pobrać stawki, choć szczegóły jego wyniku mogą już nie być dostępne.

## Odtwarzanie zapisanej rundy — replay

Wybierz **Ustawienia → Historia rund → wybrany wynik → Odtwórz rundę**. Zapisana runda jest pokazywana od początku z pełnymi animacjami bazy, kaskad, bonusu i maksymalnej wygranej. Replay nie pobiera stawki, nie dodaje wypłaty i nie zmienia salda, statystyk ani historii. Przycisk ponownego odtworzenia umożliwia obejrzenie tego samego wyniku jeszcze raz. Podczas bieżącej rundy, oczekującego odczytu i AUTO odtwarzanie jest zablokowane.

W RGS zapis do 100 ukończonych rund jest zachowywany po odświeżeniu tej samej karty, jeśli dostępne jest `sessionStorage`. To pamięć pomocnicza; jej usunięcie nie zmienia rozliczenia serwera. W lokalnym demo historia pozostaje w pamięci serwera do zakończenia sesji lub restartu.

Obsługiwany jest również publiczny link `?replay=true&game=UUID_GRY&version=WERSJA&mode=base&event=ID_SYMULACJI&rgs_url=HOST_RGS`, bez sesji gracza. Opcjonalne `amount`, `currency` i `lang` ustalają stawkę, walutę oraz język; 1000000 oznacza 1,00. Domyślne wartości to 1,00 USD i EN. Link pobiera zapis przez publiczny endpoint replay i czeka na kliknięcie **Odtwórz**. Nie pozwala rozpocząć zwykłej gry.

Lokalny bonus bez zakładu: `python qa/rgs_mock_server.py --replay --scenario bonus12 --port 8805`. Maksimum: `python qa/rgs_mock_server.py --replay --scenario cap --port 8806`. Polecenia wymagają plików deweloperskich lub paczki **RGS_TEST**. Szczegóły kontraktu i pozostałych scenariuszy opisuje **README_RGS_PL.md**. Testy lokalne nie potwierdzają jeszcze działania na rzeczywistym środowisku platformy.

## Trzy zestawy wyglądu

Zestawy **Polska**, **Legendy** i **Klasyczny** przedstawiają te same kody o tych samych wypłatach. Każdy zawiera 8 zwykłych symboli, WILD i SCATTER. Katalog 18 ilustracji nie oznacza 18 równocześnie losowanych typów. Zestaw można zmienić między rundami, poza aktywną serią AUTO.

Polska: obwarzanek, pierogi, oscypek, maluch, bocian, zamek królewski, syrenka, Husarz. Nazwy i grafiki pozostałych zestawów są widoczne w katalogu i tabeli. Opis pochodzenia obrazów znajduje się w `web/assets/art/PROVENANCE.md`; nie stanowi prawnego zatwierdzenia finalnej publikacji.

W studiu można dodać własne ilustracje: `L1.png`, `L2.png`, `L3.png`, `L4.png`, `P1.png`, `P2.png`, `P3.png`, `P4.png`, `WILD.png`, `SCATTER.png`. Działają do odświeżenia. Aby zachować je na stałe, umieść pliki w **web/assets/** i ustaw odpowiednie pola `image` w **web/assets/symbols.json**. Zmiana zestawu przywraca jego ilustracje.
