# Polska Gurom v0.5 — naliczanie i nowy ekran gry

Data: 20.10.2026. Aktywna wersja: `test-interface`, adres http://127.0.0.1:8772 . Scenariusze testowe: http://127.0.0.1:8772/?studio=1 . Paczka: `test-interface/POLSKA_GUROM_v0_5_PODGLAD.zip`. Zawiera lokalny tester i podgląd PNG.

## Efekt dla gracza

Ekran jest zintegrowaną planszą gry: bębny zajmują większość obszaru, informacje o bonusie są po lewej, a saldo, stawka i sterowanie mieszczą się w jednym dolnym pasku. Tabela wypłat, zasady i ustawienia otwierają się w oknach. Usunięto główny nagłówek i stale widoczne panele studia. Zachowano własne grafiki, 5 bębnów × 3 rzędy i 20 aktywnych linii; nie wprowadzono zakupu bonusu ani funkcji Double Chance z przykładu innej gry. WILD i SCATTER mają nowe grafiki z przezroczystością. Nie użyto brandingu Stake ani Pragmatic Play z referencji użytkownika.

Zwykłe symbole płacą teraz za ciąg co najmniej trzech pasujących pól na aktywnej linii, zaczynając od dowolnego bębna. Nowy parametr `start_reel` określa początek nagrodzonego ciągu. Na jednej linii pozostaje jedna najwyższa wypłata. Nakładające się krótsze fragmenty tego samego ciągu nie są dodatkowo sumowane. Każda aktywna linia jest rozliczana osobno, tak jak wcześniej; symbol może być częścią kilku wygrywających linii. Usuwanie symboli, kaskady, wyróżnienia i rysowanie linii uwzględniają rzeczywiste przesunięcie.

Plansza ze zgłoszenia jest osiągalna na rzeczywistych paskach bębnów. Scenariusz „3 obwarzanki na bębnach 2–4” odtwarza ją dokładnie. Przy stawce 2 zł pozioma linia 4 płaci 0,20 zł; linie 12 i 20 przez inne obwarzanki na tej planszy dają kolejne 0,40 zł, łącznie **0,60 zł**. W kaskadzie każde wygrywające pole znika tylko raz. Scenariusz jest podglądem bez zmiany salda; odpowiada mu również wynik o dodatniej wadze w zwykłej grze.

## Matematyka i weryfikacja

- Wersja `0.5.0-any-start`. Nowy bank: **100 049 pełnych rund**, dodatnie całkowite wagi o sumie 10^12.
- Dokładny ważony RTP: **24/25 = 96%**. Limit 5000×, częstość limitu 1:8 000 000. Wszystkie bonusy 8/10/12 mają dodatnią masę.
- Niezależny algorytm sprawdził wszystkie **100 000 możliwych pięcioelementowych sekwencji** symboli. Wyniki i przesunięcia zgadzają się z silnikiem.
- Niezależnie sprawdzono wszystkie **100 049 wyeksportowanych rund**, **212 009 etapów kaskad** i **367 959 wypłat liniowych**, ruchy symboli i rozliczenia. Szczegóły: `independent_audit.json`.
- Istniejące testy HTTP: 10/10. Testy kaskad: 10/10. Testy bonusu 12 FS wraz z rzeczywistym eksportem: 10/10. Prezentacja prawdziwego bonusu 12 FS: 7 scenariuszy, w tym 100 autoobrotów zawierających po 12 FS.
- Regresja autoobrotów: 13 scenariuszy, w tym po 100 rund w czterech szybkościach, zatrzymanie i powtórzenie odczytu bez kolejnej stawki.
- Nowy test frontendu potwierdza wyróżnienie wyłącznie pól (0,1), (0,2), (0,3), poprawny przebieg linii od bębna 2, jedno rozliczenie pełnej rundy oraz odrzucenie przesunięcia wychodzącego poza planszę. Raport: `any_start_frontend.json`.
- W rzeczywistej przeglądarce odtworzono scenariusz i zapisano `middle-win.png` oraz `middle_browser.json`. Wyróżnienie i kwota 0,60 zł zgadzają się z danymi serwera.
- Ekran 1280 × 720 mieści planszę, boczny panel i sterowanie bez przewijania. Telefony 390 × 844 oraz 320 × 568 nie mają przewijania poziomego; przycisk obrotu jest na ekranie. Dolne przyciski informacji, tabeli i ustawień mają 44 × 44 px. Menu zasad i tabela działają również na małym ekranie.
- Aktywna wersja po wdrożeniu wczytała 15 ilustracji, bez błędów konsoli. Podgląd: `player-desktop.png`. Kontrola integralności paczki i jej parametrów: `release.json`.

Diagnostyczna symulacja naturalnego generatora kandydatów nie opisuje rozkładu publikowanego: grę losową testera rozlicza bank pełnych rund z wagami, którego RTP policzono dokładnie. Nie przedstawiamy wyniku naturalnej próby jako RTP 96%.

## Zgodność i zakres dostawy

[Wytyczne Stake](https://stake-engine.com/docs/approval-guidelines/front-end-communication) wymagają jasnych zasad, opisu wypłat oraz zgodnego działania gry. Nie stwierdzono w nich nakazu wypłacania od dowolnego bębna; zmiana wynika z decyzji użytkownika o konstrukcji gry. [Dokumentacja linii](https://stake-engine.com/docs/math/source-files/calculations/lines) opisuje własne tabele i wzorce linii. Układ graficzny przyjęto z ogólnego rozmieszczenia elementów referencji, z własnym stylem i zasobami.

To dopracowana lokalna wersja demonstracyjna do oceny wyglądu i mechaniki, nie zatwierdzony upload do Stake. Przed publikacją pozostają integracja RGS/portfela i obsługa replay, wymagania jurysdykcji i dźwięku, końcowa kontrola praw do zasobów oraz odbiór platformy. Nie wprowadzono pozornych przycisków funkcji, których gra nie obsługuje.

Wcześniejszy tester zachowano w `before_change.zip`. Zmiany najpierw wykonano w oddzielnym `test-interface-any-start`, przebudowano i sprawdzono, a następnie przeniesiono do aktywnego `test-interface`. Wdrożenie rozpoczęło nową sesję demonstracyjną. Materiałów w `sources/` nie zmieniono.
