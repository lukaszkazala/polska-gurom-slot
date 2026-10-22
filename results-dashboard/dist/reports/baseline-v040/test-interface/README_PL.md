# POLSKA GUROM — tester interfejsu

**Wariant v0.4: kaskady i dokładne RTP 96%.** Po wygranej symbole znikają, pozostałe spadają w dół, a nowe wpadają z góry. Gra sprawdza nowy układ bez kolejnej stawki. Oryginalny model v0.2 pozostaje zachowany osobno.

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

Gra korzysta z dołączonego silnika **v0.4.0-weighted**. Bonus przyznaje **8, 10 lub 12 darmowych obrotów**. Mnożnik **×4 dotyczy tylko wygranych liniowych**, również w kaskadach bonusu. Limit **5000× stawka** obejmuje całą płatną rundę wraz z kaskadami i bonusem; osiągnięcie limitu kończy rundę. Scatter jest liczony tylko na początkowej planszy, przed rozszerzeniem WILD. Nowe symbole uzupełniające kaskadę nie zawierają Scatterów, a bonus nie przyznaje kolejnych darmowych obrotów. Rozwinięcie WILD może nastąpić raz na początku darmowego obrotu. Każde wygrywające pole znika tylko raz, nawet gdy bierze udział w kilku wygrywających liniach. Każdy autoobrót obejmuje wszystkie kaskady i cały bonus.

**Matematyka v0.4 ma dokładne RTP 96%.** Wynika ono z całkowitoliczbowych wag 100 024 różnych, kompletnych rund. Wypłaty mają krok 0,1× stawki. Najwyższa wygrana 5000× występuje średnio raz na 8 mln płatnych rund. Każda kaskada i cały bonus są częścią jednego wyniku, a saldo jest rozliczane jeden raz.

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
