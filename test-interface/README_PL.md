# POLSKA GUROM — tester interfejsu

## Aktualna matematyka 0.6.0-high-wins — 22.10.2026

Ten wariant korzysta z nowego banku **100 343 pełnych rund** i tych samych wag co `test-interface-any-start`. Zachowano dokładne RTP 96%, limit 5000×, łączną częstość maksimum 1:8 000 000 i masy wejścia do 8/10/12 FS. Maksimum występuje teraz w bazie i we wszystkich wariantach FS. Wysokie wygrane mają 297 różnych kwot; największa luka w zakresie 500×–5000×, z brzegami, wynosi 98,6×.

Budżet RTP wypłat ≥500× pozostaje dokładnie 2,44355542032 p.p. Ich łączna częstość maleje z około 1:27 959 do około 1:47 374, ponieważ większa część budżetu trafia do wyższych pasm. Pełne porównanie i weryfikacja: [raport przebudowy](../audit/high_wins_rebuild_2026_10_22/RAPORT_PL.md). Po zmianie uruchom serwer ponownie. Wersja `test-interface-any-start` zawiera także aktualną obsługę RGS, replay i języków.

## Historia v0.5 — ekran gry i układy od dowolnego bębna

Uruchom **START_UX.cmd** i otwórz **http://127.0.0.1:8772**. Wersja do testów scenariuszy: **http://127.0.0.1:8772/?studio=1**. Domyślny ekran prezentuje samą grę: duże bębny, informacje o bonusie po lewej oraz jeden dolny pasek z saldem, stawką, wygraną i sterowaniem. Ikony i, tabeli i koła zębatego otwierają odpowiednio zasady, wypłaty i ustawienia. Bez dodatkowych paneli testera na głównym ekranie.

**Nowa zasada:** co najmniej 3 kolejne pasujące symbole na aktywnej linii mogą zaczynać się od dowolnego bębna. Układy na bębnach 1–2–3, 2–3–4 i 3–4–5 są zaliczane. Dłuższy ciąg wypłaca według tabeli. Na każdej z 20 aktywnych linii wypłacany jest jeden najwyższy wynik; ten sam symbol może wygrywać na kilku liniach. Usuwane podczas kaskady są rzeczywiste wygrywające pozycje, także przesunięte w prawo.

Przebudowano bank 100 049 pełnych rund i wagi. Dokładne RTP opublikowanego zestawu wynosi **96%**, limit rundy to **5000×**, a częstość maksymalnej wygranej wynosi **1:8 000 000**. To parametry lokalnego eksportu, nie zatwierdzenie platformy. Zestaw wyników i frontend mają wersję `0.5.0-any-start`.

W trybie `?studio=1` wybierz koło zębate → Narzędzia do testów → **3 obwarzanki na bębnach 2–4**, zamknij ustawienia i kliknij obrót. Ten scenariusz dokładnie odtwarza zgłoszoną planszę i nie zmienia salda. Przy stawce 2 zł pozioma linia z trzema obwarzankami płaci 0,20 zł; dodatkowe aktywne linie przez obwarzanki na tej planszy dają łącznie **0,60 zł**. W zwykłej grze te same zasady obowiązują i wygrane są normalnie rozliczane z saldem demonstracyjnym. Scenariusz ma również dodatnią wagę w nowym banku wyników.

Poniższy opis aktualizacji samych grafik odnosi się do poprzedniego etapu v0.4.1. W v0.5 zmieniono również matematykę zgodnie z regułą powyżej.

## Nowy wygląd — 18 ilustracji, 3 zestawy (20.10.2026)

Uruchom **START_UX.cmd**, aby otworzyć tester pod **http://127.0.0.1:8772**. Jeżeli tester działa już na tym porcie, otwórz ten adres w przeglądarce. W paczce przenośnej możesz też użyć zwykłego **START.cmd** (port 8765).

- **Polska:** obwarzanek, pierogi, oscypek, maluch, bocian, zamek królewski, syrenka i Husarz.
- **Legendy:** diament, pik, serce, trefl, lilia, zamek królewski, smok wawelski i Husarz.
- **Klasyczny:** diament, pik, serce, trefl, lilia, kielich, korona i Husarz.

Każdy zestaw zawiera ponadto WILD i SCATTER. Przycisk **Wszystkie symbole · 18** otwiera pełny katalog i wskazuje, które ilustracje występują w bieżącym zestawie. Zestaw można przełączyć między rundami, poza aktywną serią autoobrotów. Nazwy w tabeli wypłat i na bębnach zmieniają się razem z grafiką. Wybór jest zapamiętany lokalnie. Zmiana zestawu usuwa tymczasowo wgrane własne grafiki, przywracając ilustracje zestawu.

To aktualizacja prezentacji: **silnik, bank wyników, wagi, stawki i wypłaty nie zostały zmienione**. Każdy zestaw przedstawia te same 8 kodów zwykłych symboli i 2 kody specjalne. Katalog ma 18 ilustracji łącznie; nie losujemy 18 niezależnych typów jednocześnie.

Dodano złoconą ramę i układ telefonu z przyciskiem obrotu dostępnym bez długiego przewijania. Grafiki powstały narzędziem imagegen i są przechowywane lokalnie. Zasoby atlasowe są wycinane podczas wyświetlania przez SVG; nie potrzebują sieci ani zewnętrznego CDN do lokalnych testów. To lokalny tester z wirtualnym saldem, nie opublikowana lub prawnie zatwierdzona gra. Weryfikacja finalnych praw, znaków i warunków publikacji pozostaje osobnym etapem.

**Historia wariantu v0.4.1: kaskady i dokładne RTP 96%.** Po wygranej symbole znikają, pozostałe spadają w dół, a nowe wpadają z góry. Gra sprawdza nowy układ bez kolejnej stawki. Oryginalny model v0.2 pozostaje zachowany osobno.

**Kaskady działają automatycznie w zwykłej grze.** Po uruchomieniu kliknij **ZAKRĘĆ**. Gdy padnie wygrana liniowa, symbole znikną, pozostałe spadną w dół, a nowe wpadną z góry. Start zawsze odbywa się z widoczną animacją i zwykłą losową grą. Zapisane wcześniej ustawienia szybkości nie ukrywają opadania.

Opcja **Pokaż kaskadę** w zwiniętych narzędziach testowych jest dodatkowym, powtarzalnym podglądem trzech kaskad. W zwykłej grze nie trzeba jej wybierać. Tryb błyskawiczny można włączyć ręcznie w oknie AUTO na czas bieżącej wizyty; wtedy pomija także animacje kaskad.

## Uruchomienie

1. Wypakuj **całe archiwum ZIP** do własnego folderu. Silnik gry jest już w paczce.
2. Potrzebny jest **Python 3.12 lub nowszy**. Nie trzeba instalować dodatkowych pakietów. Na tym komputerze uruchamiacz może też użyć Pythona dołączonego do aplikacji Codex.
3. Kliknij dwukrotnie **START.cmd**. Otworzy się przeglądarka z adresem **http://127.0.0.1:8765**. Jeśli nie otworzy się automatycznie, wpisz ten adres samodzielnie.
4. Pozostaw otwarte okno uruchamiacza podczas testów. Aby zakończyć, naciśnij w nim **Ctrl+C**.

Gdy brakuje Pythona, zainstaluj go z [python.org](https://www.python.org/downloads/) i zaznacz opcję **Add python.exe to PATH**. Gdy port jest zajęty, zamknij wcześniejsze okno testera. Możesz też uruchomić w tym folderze `python server.py --port 8766` i otworzyć wskazany adres. Opcja `--no-browser` wyłącza automatyczne otwarcie przeglądarki.

## Co można testować

- Ręczne obroty, zmianę stawki, saldo, historię wyników, darmowe obroty, tabelę wypłat i wybór języka.
- Stawki podaje się w **pełnych złotych**. Saldo jest fikcyjne; tester nie obsługuje wpłat ani prawdziwych pieniędzy.
- Przycisk **ZAKRĘĆ / SPIN** lub **spacja** uruchamia obrót. Spacja jest pomijana podczas wpisywania w pola i wyboru ustawień.
- Przycisk **AUTO** otwiera okno ustawień autoplay. Wybierz **10, 25, 50, 100, 250 lub 500 płatnych rund** i uruchom serię. Jedna runda obejmuje płatny obrót oraz wszystkie przyznane mu darmowe obroty; bonus nie pomniejsza osobno licznika serii.
- **STOP AUTO** kończy serię po bieżącej rundzie, razem z jej bonusem. Zmiana karty lub ukrycie okna nie anuluje serii; przeglądarka może wtedy spowolnić obroty. Licznik pokazuje wykonane rundy, np. **80 / 100**, a po pełnej serii **100 / 100**.
- Przejściowy błąd połączenia powoduje maksymalnie trzy próby odczytu tej samej rundy, bez ponownego pobrania stawki. Gdy brakuje salda lub odczyt nadal się nie udaje, przy liczniku pozostaje powód przerwania serii.
- Po dłuższej awarii przycisk **PONÓW ODCZYT** odzyskuje tę samą rundę. Oczekujący identyfikator jest zachowany także po odświeżeniu tej samej karty (jeśli przeglądarka udostępnia pamięć sesji). Odczyt nie uruchamia od nowa przerwanej serii AUTO.
- Zerwana lub błędna odpowiedź, timeout, błąd 408/429/5xx nie tworzą nowego obrotu podczas ponawiania. Limit oczekiwania wynosi 15 sekund na próbę, również dla niedokończonej treści odpowiedzi.
- Restart lokalnego serwera usuwa wirtualne saldo i historię z pamięci. Stara runda jest wtedy blokowana przed ponownym rozliczeniem; trzeba odświeżyć stronę i rozpocząć nową sesję testową. Reset sesji w drugiej karcie również blokuje stare żądania.
- Historia przechowuje szczegóły 100 ostatnich wyników. Starszy identyfikator pozostaje oznaczony jako rozliczony i nie może drugi raz pobrać stawki, choć jego pełny wynik nie jest już odtwarzany.
- Dostępne tempa to **normalne, szybkie i turbo**. Przycisk szybkości przełącza tempo, a opcje w oknie AUTO pozwalają wybrać szybkie animacje lub turbo. Opcja **Pomijaj ekrany** pomija wejście do bonusu i jego ekran końcowy.
- **Tryb błyskawiczny** w oknie AUTO pokazuje od razu wynik całej rundy, razem z bonusem. Szybkość, pomijanie ekranów i tryb błyskawiczny zmieniają wyłącznie prezentację; nie zmieniają losowań, prawdopodobieństw ani rozliczenia wygranej.
- Przygotowane scenariusze służą do sprawdzania wyglądu wygranych i bonusów. **Nie zmieniają salda ani statystyk normalnej gry.**

Gra korzysta z dołączonego silnika **v0.4.1-weighted-12fs**. Bonus przyznaje **8, 10 lub 12 darmowych obrotów**. Mnożnik **×4 dotyczy tylko wygranych liniowych**, również w kaskadach bonusu. Limit **5000× stawka** obejmuje całą płatną rundę wraz z kaskadami i bonusem; osiągnięcie limitu kończy rundę. Scatter jest liczony tylko na początkowej planszy, przed rozszerzeniem WILD. Nowe symbole uzupełniające kaskadę nie zawierają Scatterów, a bonus nie przyznaje kolejnych darmowych obrotów. Rozwinięcie WILD może nastąpić raz na początku darmowego obrotu. Każde wygrywające pole znika tylko raz, nawet gdy bierze udział w kilku wygrywających liniach. Każdy autoobrót obejmuje wszystkie kaskady i cały bonus.

**Matematyka v0.4.1 ma dokładne RTP 96%.** Wynika ono z całkowitoliczbowych wag 100 048 różnych, kompletnych rund. Wypłaty mają krok 0,1× stawki. Najwyższa wygrana 5000× występuje średnio raz na 8 mln płatnych rund. Każda kaskada i cały bonus są częścią jednego wyniku, a saldo jest rozliczane jeden raz.

**Poprawka 12 obrotów (20.10.2026):** końcowy bank obejmuje 24 różne pełne rundy z 5 Scatterami i 12 wykonanymi darmowymi obrotami. Ich łączna szansa to 4 018 776 / 1 000 000 000 000, czyli około 1:248 832. Ogólna częstość bonusu pozostaje bez zmian. Kompilator i selektor sprawdzają dodatnie pokrycie wszystkich wariantów 8/10/12; brak któregokolwiek blokuje użycie zestawu. Aktualny kompilator: `python test-interface/build_math.py` z katalogu projektu. Odtworzenie eksportu wymaga pakietu zstandard; uruchomienie zapakowanej gry nie wymaga dodatkowych pakietów.

Folder **stake_math/** zawiera `index.json`, skompresowane książki wyników `books_base.jsonl.zst` oraz wagi `lookUpTable_base_0.csv` w formacie Stake Engine. Lokalna gra wybiera wynik według dokładnie tych samych wag i odtwarza go z `selection.json`. Pliki `mathematics.json` i `selection.json` opisują model i kontrolują zgodność z silnikiem. Po zmianie reguł trzeba przebudować i ponownie sprawdzić zestaw wyników. Losowania generatora kandydatów (np. 25% szansy rozszerzenia w generatorze bonusu) nie są końcowym rozkładem RGS.

Pliki przeszły lokalne sprawdzenie publicznym walidatorem Stake SDK. Nie oznacza to zatwierdzenia platformy. Integracja z rzeczywistym portfelem RGS, odtwarzaniem rund i proces publikacji pozostają osobnym etapem.

W tym wariancie **nie ma zakupu darmowych obrotów ani opcji Double Chance**. Bonus jest przyznawany przez Scattery w początkowym układzie zwykłej gry; podgląd scenariusza bonusowego służy wyłącznie testowaniu.

## Dodawanie własnych grafik

Najprościej użyj przycisku wgrywania grafik w interfejsie i wybierz pliki nazwane dokładnie:

`L1.png`, `L2.png`, `L3.png`, `L4.png`, `P1.png`, `P2.png`, `P3.png`, `P4.png`, `WILD.png`, `SCATTER.png`.

Grafiki wgrane w przeglądarce działają **do odświeżenia strony**. Można wgrać dowolny podzbiór symboli; pozostałe zachowają wygląd zastępczy.

Aby zachować grafiki na stałe, skopiuj je do folderu **web/assets/**. Następnie w pliku **web/assets/symbols.json** ustaw dla danego symbolu pole `image` na nazwę pliku, np. `"image": "L1.png"`. Możesz też użyć podfolderu, np. `"image": "symbols/diament.png"` — ścieżka jest liczona od folderu **assets**. Zapisz plik i odśwież stronę. W tym samym pliku można zmienić nazwy symboli po polsku, angielsku i niemiecku.

| Kod | Symbol |
| --- | --- |
| L1 | Diament |
| L2 | Pik |
| L3 | Serce |
| L4 | Trefl |
| P1 | Lilia |
| P2 | Kielich |
| P3 | Korona |
| P4 | Husarz |
| WILD | Wild |
| SCATTER | Scatter |
# Grafika v2 — 20.10.2026

## Efekty bonusów — zapisane w projekcie

Wejście i zakończenie darmowych obrotów korzystają z tej samej malarskiej sceny husarii, rzeźbionej złotej ramy i tarczy husarza co gra. Bordowa tkanina, ciepła poświata oraz postarzone drobiny złota zastępują abstrakcyjne promienie. Podczas free spinów rama ma złotą poświatę. Końcowa wygrana całej rundy od 20× stawki wyświetla WIELKĄ WYGRANĄ, od 50× MEGA, od 100× EPICKĄ. Plansza pokazuje kwotę wyniku zatwierdzonego przez silnik; efekty nie zmieniają wypłat, prawdopodobieństw ani RTP.

Przycisk „Pomiń animację” skraca oprawę bez przerywania rundy. Opcja „Pomijaj ekrany” i tryb błyskawiczny wyłączają celebracje. Dla nowych ustawień ekrany są domyślnie włączone; wcześniejszy zapisany wybór użytkownika jest respektowany. Systemowe ograniczenie ruchu usuwa monety i ruch promieni. Ukrycie strony sprząta efekt i pozwala zakończyć bieżącą rundę.

Podgląd samych efektów: http://127.0.0.1:8772/effects-preview.html — przykładowe kwoty, bez losowania i bez zmiany salda. Implementacja lokalna: `web/celebrations.js`, `web/celebrations.css`; integracja w `web/app.js`. Paczka z grafiką i efektami: `POLSKA_GUROM_v0_5_GRAFIKA_EFEKTY_STYL.zip`.

Malarskie tło z husarią i gładkimi bordowymi chorągwiami, bordowo-złote wykończenie oraz siedem nowych przezroczystych symboli skarbca w zestawach Legendy i Klasyczny. Polski zestaw zachowuje dotychczasowe ilustracje. Wszystkie 18 symboli są dostępne w galerii w ustawieniach. Ta aktualizacja zmienia wyłącznie grafikę; układ i matematyka v0.5 pozostają takie same.

Podgląd lokalny: http://127.0.0.1:8772/ (uruchom `START_UX.cmd`). Źródła grafik i prompty: `web/assets/art/PROVENANCE.md` oraz `GRAPHICS_V2_PROMPTS.json`.

