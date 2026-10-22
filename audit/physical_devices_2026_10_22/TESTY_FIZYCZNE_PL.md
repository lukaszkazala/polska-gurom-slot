# POLSKA GUROM — odbiór na fizycznych urządzeniach

Data: 22.10.2026. Wersja matematyki: **0.5.0-any-start**. Przedmiot: pliki i paczki z `test-interface-any-start` w czasie kontroli; dokładne skróty i ewentualną rozbieżność źródeł z paczkami zapisano w `evidence.json`. W czasie przygotowania protokołu inne prace zmieniły frontend i dodały audio; przed próbami należy wybrać jeden gotowy build.

**Status: testy fizyczne niewykonane.** Użytkownik potwierdził **iPhone 15, Safari i tę samą sieć Wi‑Fi co komputer**, a także brak dostępu do platformy. Wersja iOS/Safari pozostaje do uzupełnienia. Przygotowano osobną kopię demo z audio i lokalny dostęp opisany w [instrukcji dla iPhone’a](IPHONE15_SAFARI_PL.md). Ten dokument jest protokołem do wykonania; nie stanowi wyniku odbioru. Liczba wykonanych testów fizycznych: **0**.

## Potwierdzone przygotowanie i przeszkody

| Zakres | Ustalenie | Znaczenie |
|---|---|---|
| Dotyk i obrót | Brak nowej próby na telefonie | Dotychczasowe zmiany szerokości okna nie zaliczają tych testów. |
| Powrót z tła | W kodzie jest obsługa `visibilitychange`, która odświeża przyciski; odczyt portfela jest pomijany w ukrytej karcie | To obserwacja kodu. Nie dowodzi poprawnego wznowienia po uśpieniu lub usunięciu procesu przez telefon. |
| Dźwięk | Pierwsza kontrola wykazała brak audio w paczkach. W czasie pracy pojawiły się `audio.js`, sześć plików WAV i przycisk wyciszenia w źródłach gry | Nie wykonano odsłuchu ani testu na urządzeniu. A01–A03 wymagają gotowego buildu z audio oraz fizycznej próby. Stan paczek z chwili pomiaru podaje `evidence.json`; cisza w starej paczce nie oznacza zaliczenia. |
| Uruchomienie lokalne na telefonie | Oryginalne serwery są ograniczone do `127.0.0.1`. Osobny serwer testowy udostępnia zamrożoną kopię demo na `192.168.1.19:8785`, z dostępem przez wygenerowany link | Sprawdzono HTTP z komputera. Połączenie z iPhone’a pozostaje do potwierdzenia. Nie zmieniano zabezpieczeń ani adresu nasłuchu oryginalnych serwerów. |
| Osadzenie lokalnego demo | Serwer demo wysyła `X-Frame-Options: DENY` | Nie służy do odbioru gry w ramce platformy. Nie zmieniano tego zabezpieczenia. |
| Platforma | Użytkownik nie ma jeszcze dostępu | P01–P03 pozostają niewykonane do czasu udostępnienia środowiska. Lokalna ramka lub symulator nie zaliczają odbioru platformy. |

Wstępna kontrola plików: `evidence.json`. Aktualna kopia testowa i skróty: `phone_build.json`. Kontrole jej serwera: `launcher_checks.json`. Nie uruchamiano gry na telefonie ani w nowej sesji przeglądarki w ramach tego etapu. Ta praca obejmuje protokół, plan odbioru oraz osobny serwer i kopię do prób przez Wi‑Fi. Nie zmienia kodu oryginalnej gry, matematyki ani paczek wydania.

## Warunki uruchomienia

1. Uzupełnić modele, wersje systemów oraz nazwy i pełne wersje przeglądarek. Każda para urządzenie–przeglądarka ma oddzielny wynik. Dostępne iPhone/Safari i Android/Chrome są odrębnymi próbami; jednej nie wolno zaliczać na podstawie drugiej. Inne przeglądarki wpisać według rzeczywistego zakresu wydania.
2. Na potwierdzonym iPhonie 15 skorzystać z [osobnego lokalnego linku testowego](IPHONE15_SAFARI_PL.md). Kopia `iphone15-safari-20261022T095007` zawiera audio i nie aktualizuje się wraz z równoległymi zmianami projektu. Dla ewentualnych kolejnych urządzeń dobrać dostęp osobno; standardowe uruchamiacze nadal otwierają wyłącznie grę na komputerze.
3. Testy ręczne wykonuje osoba obsługująca telefon. Samo posiadanie telefonów nie zapewnia agentowi ich zdalnego sterowania. Zapisać wykonawcę i czas próby.
4. Przed próbą zapisać skrót paczki lub identyfikator wdrożenia, stawkę, saldo i scenariusz. Używać salda testowego. Po każdej zmianie plików wyznaczyć nowy identyfikator wersji i powtórzyć przypadki zależne od zmiany.
5. Studio `?studio=1` umożliwia powtarzalne próby kaskad i bonusu lokalnego demo. Te scenariusze nie zmieniają salda: służą do oceny prezentacji. Jedno obciążenie i wypłatę sprawdzać osobno w zwykłej rundzie demo, a później w sesji testowej platformy. Liczby wirtualnego portfela nie potwierdzają działania RGS.
6. Bonus 12 FS i maksimum mogą być odtwarzane w lokalnym symulatorze zgodnie z `test-interface-any-start/README_RGS_PL.md`, dopiero po zapewnieniu dostępu z urządzenia. Nie oczekiwać losowego trafienia rzadkiej wygranej w krótkiej sesji ręcznej.

## Karta środowiska — osobna dla każdej pary

| Pole | Do uzupełnienia |
|---|---|
| Identyfikator próby | |
| Data, godzina i wykonawca | |
| Fizyczne urządzenie i model | |
| System i wersja | |
| Przeglądarka i pełna wersja | |
| Paczka SHA-256 / identyfikator wdrożenia | |
| Tryb: demo / symulator / platforma | |
| Sposób połączenia | |
| Pion/poziom, skala tekstu, blokada obrotu | |
| Wyniki i odnośniki do nagrań/zdjęć | |

Nie wpisywać do protokołu tokenów sesji ani pełnego linku uruchomienia z tokenem. Do identyfikacji wystarcza środowisko, wersja i identyfikator próby/rundy.

## Przypadki do wykonania

Wyniki: **ZALICZONY**, **BŁĄD**, **ZABLOKOWANY**, **NIEWYKONANY**, **NIE DOTYCZY** z uzasadnieniem. Poniższe statusy są początkowym planem, a nie zarejestrowanymi próbami.

| ID | Czynności na rzeczywistym urządzeniu | Kryterium odbioru | Status początkowy |
|---|---|---|---|
| T01 | W pionie wykonać 10 pojedynczych dotknięć OBROTU, każde po zakończeniu poprzedniej rundy; sprawdzić stawkę +/−. Powtórzyć w poziomie. | Każdy świadomy gest uruchamia jedną rundę; stawka zmienia się o jeden poziom. Przyciski dają się trafić i nie są zasłonięte. | NIEWYKONANY |
| T02 | Podczas obrotu szybko dotknąć przycisku dwukrotnie, przytrzymać go i spróbować dotknąć dwoma palcami. Powtórzyć w 10 rundach. | Brak dodatkowego niezamierzonego zakładu, podwójnej wypłaty i zmiany stawki opłaconej rundy. Ocenić liczbę rund i zapis transakcji, nie tylko animację. | NIEWYKONANY |
| T03 | Otworzyć i zamknąć ustawienia, zasady, tabelę, historię i szczegóły. Przewijać ich treść i używać natywnych list wyboru. | Treść oraz zamknięcie pozostają dostępne; przewijanie lub zamykanie nie uruchamia obrotu pod oknem; po zamknięciu gra reaguje na dotyk. | NIEWYKONANY |
| T04 | Otworzyć AUTO, anulować, potem potwierdzić 10 rund i nacisnąć STOP w trakcie rundy. | Samo otwarcie/anulowanie nie rozpoczyna serii. STOP kończy ją po bieżącej pełnej rundzie wraz z bonusem. | NIEWYKONANY |
| R01 | Wyłączyć blokadę obrotu telefonu. Obrócić pion→poziom→pion pięć razy na ekranie spoczynkowym, również z paskiem przeglądarki pokazanym i schowanym. | Plansza i przyciski pozostają dostępne, symbole nie są zniekształcone. Saldo, stawka i stan gry się nie zmieniają. | NIEWYKONANY |
| R02 | Obrócić urządzenie podczas opadania kaskady oraz darmowego obrotu. Wykonać co najmniej pięć zmian orientacji w każdej sytuacji. | Brak wiszących symboli i przesuniętych linii po zakończeniu animacji. Ten sam wynik, stawka i licznik FS; brak nowego zakładu. | NIEWYKONANY |
| R03 | Obrócić telefon z otwartymi zasadami, tabelą i historią; sprawdzić również większy tekst ustawiony w systemie. | Treść można przewinąć i zamknąć; kwoty oraz elementy sterowania nie zostają trwale poza ekranem. | NIEWYKONANY |
| B01 | Ze stanu spoczynkowego przejść do innej aplikacji na 5, 30 i 120 s; wrócić. Powtórzyć z blokadą ekranu. | Brak nowej rundy bez gestu, poprawne saldo, działające przyciski i brak zdublowanej obsługi. Wygaśnięcie sesji daje czytelne ponowne uruchomienie/połączenie. | NIEWYKONANY |
| B02 | Wyjść do innej aplikacji lub zablokować telefon podczas kaskady, bonusu i aktywnego AUTO; wrócić po 30 i 120 s. | Ta sama runda i poprawny końcowy wynik; jedna stawka i jedna wypłata. Zapisać rzeczywiste zachowanie AUTO w tle i po powrocie. Akceptowana polityka AUTO w tle wymaga ustalenia przed zaliczeniem tego wariantu. | NIEWYKONANY |
| B03 | Podczas bonusu przeładować stronę, a oddzielnie zamknąć proces przeglądarki i otworzyć grę ponownie. Zapisać, czy karta/pamięć przetrwała. | Nie wysyłać nowego zakładu zamiast odzyskania. Przy dostępnym zapisie wraca właściwy postęp; utrata pamięci w demo ma jawne ograniczenia. Wznowienie z RGS sprawdzić osobno na platformie. AUTO nie rusza samo po przeładowaniu. | NIEWYKONANY |
| B04 | Wyłączyć połączenie podczas rundy, wrócić z tła, przywrócić połączenie i użyć ponownego odczytu. | Nieznany stan blokuje nową rundę. Odzyskanie odczytuje tę samą rundę; brak drugiego obciążenia/wypłaty. Demo/symulator i platforma mają osobne wyniki. | NIEWYKONANY |
| A01 | Na gotowym buildzie z audio: świeże uruchomienie, pierwszy gest, obrót bazowy, kaskada, bonus, częściowy zwrot i duża wygrana. | Brak dźwięku przed gestem; właściwe i słyszalne efekty po geście, bez nakładania wielu kopii muzyki i bez sugerowania zysku przy częściowym zwrocie. | NIEWYKONANY — wymaga buildu z audio |
| A02 | Na gotowym buildzie z audio: włączyć/wyłączyć wyciszenie przed rundą, w trakcie bonusu, po obrocie telefonu i po powrocie z tła. | Wyciszenie obejmuje muzykę i efekty, pozostaje zgodne z ustawieniem; wznowienie nie wymusza dźwięku wbrew wyborowi użytkownika. | NIEWYKONANY — wymaga buildu z audio |
| A03 | Na gotowym buildzie z audio: blokada ekranu, inna aplikacja, przerwanie dźwięku przez system, głośnik i słuchawki dostępne w danym urządzeniu. | Brak niezamierzonego odtwarzania w tle; poprawny powrót zgodnie z wyciszeniem i wymaganiami gestu przeglądarki. Zapisać wpływ trybu cichego i wybranego wyjścia audio. | NIEWYKONANY — wymaga buildu z audio |
| P01 | Na środowisku testowym otworzyć grę z lobby we właściwej ramce, następnie w dostępnych oknach S/M i popout. | Właściwa sesja, gotowe zasoby i portfel; brak blokady osadzenia, błędów połączeń i zasłoniętych przycisków. | ZABLOKOWANY — brak platformy |
| P02 | W rzeczywistym oknie platformy powtórzyć T01–T04, R01–R03, B01–B04 i A01–A03; zmienić rozmiar i tryb pełnoekranowy, jeśli platforma go oferuje. | Wyniki z samodzielnej karty nie są przenoszone automatycznie na ramkę. Działają dotyk, obrót, powrót, audio i sterowanie w docelowym osadzeniu. | ZABLOKOWANY — brak platformy |
| P03 | Wyjść do lobby i wrócić podczas aktywnego bonusu; osobno sprawdzić wygaśniętą sesję oraz publiczny replay. | RGS przywraca właściwą rundę/postęp bez nowego zakładu; nieznany stan blokuje grę. Replay nie obciąża portfela. | ZABLOKOWANY — brak platformy |

B03 rozdziela ponowne wczytanie z zachowaną pamięcią karty od jej całkowitej utraty. Po całkowitej utracie lokalnego identyfikatora demo nie zapewnia odzyskania identycznego postępu prezentacji; tego ograniczenia nie wolno opisywać jako potwierdzonego recovery platformy.

## Zapis pojedynczego wyniku

Skopiować blok dla każdego przypadku i środowiska:

```text
Próba / urządzenie / przeglądarka:
Paczka SHA-256 lub wersja wdrożenia:
Przypadek ID i czas:
Wynik:
Wykonane kroki i długość pobytu w tle:
Scenariusz oraz ID rundy, bez tokenu sesji:
Saldo przed / stawka / wypłata / saldo po:
Licznik FS przed i po, jeśli dotyczy:
Liczba zakładów i rozliczeń, jeśli dostępna w środowisku:
Zaobserwowane zachowanie / numer błędu:
Nagranie lub zdjęcia oraz zapis serwera:
Wykonawca:
```

Nagranie ekranu potwierdza zachowanie interfejsu. Odsłuch audio wymaga fizycznego sprawdzenia wyjścia dźwięku; sam plik nagrania może nie zawierać dźwięku aplikacji. Pojedyncze obciążenie/wypłatę potwierdza zapis portfela lub serwera testowego, nie sam wygląd licznika.

## Kiedy można zamknąć ten punkt

Każda uzgodniona para urządzenie–przeglądarka musi mieć wyniki wymaganych przypadków i dowody. ZABLOKOWANY ani NIEWYKONANY nie są zaliczeniem. Po poprawce powtórzyć przypadek oraz próby zależne. Nowa wersja audio wymaga nowego skrótu paczki i właściwej regresji.

Odbiór lokalny i odbiór platformy mają oddzielne statusy. Do czasu fizycznych prób, w tym gotowego buildu z audio, oraz testów prawdziwego okna platformy cały zakres zlecenia pozostaje **otwarty**, nawet jeśli lokalne próby dotyku, obrotu i powrotu z tła zostaną później zaliczone.
