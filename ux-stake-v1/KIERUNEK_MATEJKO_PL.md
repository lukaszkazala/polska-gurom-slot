# Polska Gurom — kierunek malarski i tarcza

**Najnowsza koncepcja katalogu: `koncepcja-15-symboli-v5.png`.** Użytkownik zlecił dodanie samochodu inspirowanego maluchem, obwarzanka, zamku w stylu Wawelu, oscypka i syrenki. Plansza pokazuje 15 różnych propozycji symboli w siatce 5 × 3, po jednym przykładzie każdego typu, jako przegląd graficzny. Nie jest to zestaw rozkładów losowych ani nowa matematyka. Aktywny silnik i jego tabela wypłat nadal mają 10 typów. Szczegóły praw i kierunku nowych ilustracji: `NOWE_SYMBOLE_I_PRAWA_PL.md`.

**Aktualna pełna makieta: `koncepcja-bez-godla-v4.png`.** Zastępuje wcześniejszą koncepcję v2 jako kierunek do dalszej pracy. Na zlecenie użytkownika usunięto wizerunki orłów z chorągwi w tle i ilustracji SCATTER, uproszczono narożne tarczki oraz zastosowano tarczę z hełmem i skrzydłem husarskim w P4 i prawym panelu. Sprawdzono te obszary wizualnie po edycji. Zachowano 5 kolumn, 3 rzędy, liczbę typów symboli i układ koncepcji. Historyczne wersje pozostają jedynie dokumentacją, nie materiałem do publikacji.

Ustalenia z użytkownikiem: 20.10.2026. Zmieniamy kierunek wizualny z prostych geometrycznych symboli na polskie malarstwo historyczne i ozdobną oprawę obrazu.

Podgląd koncepcji: `koncepcja-matejko-tarcza-v2.png`. Sprawdzono wizualnie obecność 5 kolumn i 3 rzędów oraz wszystkich dziesięciu typów symboli na przykładowej planszy. Ozdobna rama, boczna scena i zbliżenie tarczy są kierunkiem ilustracji; drobne elementy sterowania i ekrany stanów wymagają osobnego opracowania UX.

## Liczba symboli

Aktywny katalog `test-interface/web/assets/symbols.json` zawiera **10 typów symboli**:

| Kod | Nazwa | Rola |
|---|---|---|
| L1 | Diament | Zwykły |
| L2 | Pik | Zwykły |
| L3 | Serce | Zwykły |
| L4 | Trefl | Zwykły |
| P1 | Lilia | Zwykły |
| P2 | Kielich | Zwykły |
| P3 | Korona | Zwykły |
| P4 | Husarz | Zwykły; opracowanie wizualne jako tarcza husarska |
| WILD | Wild | Zastępujący |
| SCATTER | Scatter | Specjalny, uruchamiający bonus zgodnie z zasadami |

To 8 zwykłych i 2 specjalne. Plansza ma 15 pól (5 × 3); symbole mogą się powtarzać. Tarcza nie jest jedenastym typem symbolu. Zmiana grafiki P4 nie zmienia jego wypłat ani prawdopodobieństw.

## Tarcza i rama

Tarcza Husarza: szeroka góra, zwężający się dół, karmazynowe pole, stare złoto na obrzeżu i nitach, srebrne skrzydło husarskie oraz dyskretny motyw kopii. Własna dekoracyjna kompozycja, bez użycia współczesnego urzędowego godła jako gotowego znaku.

Rama planszy: rzeźbione i złocone drewno, dębowe liście i ornament roślinny, bordowe akcenty. W bocznych partiach możliwa malarska scena z chorągwiami, końmi i kopiami. Wnętrze bębnów spokojne, ciemne, zapewniające kontrast. Ozdoby nie zasłaniają symboli, wyniku ani sterowania. Na telefonie rama musi być cieńsza i uproszczona.

Punktem odniesienia jest nastrój „Bitwy pod Grunwaldem” Jana Matejki: ciepłe umbry, czerwień, stare złoto i faktura olejna. To inspiracja stylistyczna; zestawienie husarii z atmosferą tego obrazu nie jest deklaracją rekonstrukcji bitwy z 1410 roku. Koncepcja wygenerowana obrazowo służy ocenie kierunku; przed wdrożeniem trzeba osobno przygotować zasoby, przezroczystość, skalowanie i stany UI.

## Weryfikacja wykorzystania

Portal edukacyjny ZPE oznacza obraz Matejki jako domenę publiczną. [Materiał ZPE](https://zpe.gov.pl/a/wazne-wydarzenia-historyczne-w-malarstwie-polskim---cz-1/DM0RGP31F). [Rekord obrazu w Muzeum Narodowym w Warszawie](https://cyfrowe.mnw.art.pl/pl/katalog/509927).

W tej koncepcji nie pobierano reprodukcji obrazu i nie włączano zdjęcia muzealnej ramy. Inspiracją są opisany nastrój, technika i ornamentyka. Jeśli później użyjemy konkretnego skanu, fotografii lub ich fragmentu, należy zapisać pochodzenie pliku, oznaczenie praw i wymagane informacje o autorze oraz źródle. Nie przenosimy automatycznie oznaczenia praw z jednego pliku na inne wersje.

Koncepcję przygotowano narzędziem imagegen na podstawie opisu tekstowego, bez zewnętrznych obrazów referencyjnych. Prompt znajduje się w historii tej rozmowy. Finalne zasoby wymagają sprawdzenia podobieństw i warunków narzędzia oraz uzupełnienia rejestru praw; samo wygenerowanie obrazu nie stanowi pełnego potwierdzenia praw do publikacji. Nazwa gry pozostaje robocza, zgodnie z wcześniejszym rejestrem.

Nie zmieniono aktywnego testera, kodów symboli ani matematyki.

## Doprecyzowanie: Husarz bez gotowych znaków i herbów

Użytkownik zlecił polski charakter symbolu bez wykorzystania chronionych znaków. Aktualna propozycja P4 to `symbole/P4-husarz-v3.png`: karmazynowa tarcza ze złotymi okuciami, hełm inspirowany szyszakiem i srebrne skrzydło husarskie. Ten wariant zastępuje wcześniejszą propozycję samego skrzydła i kopii jako kierunek P4. Ma przezroczyste tło; to osobny zasób, nie podmiana działającego testera.

Wygenerowano 20.10.2026 narzędziem imagegen wyłącznie z opisu tekstowego, bez dostarczonej fotografii lub grafiki referencyjnej. W poleceniu wykluczono orła, godło, flagę, koronę, krzyże, herby, znaki jednostek wojskowych, logotypy i napisy. Kontrola wizualna: tarcza, hełm, skrzydło i ornamenty; brak tych wskazanych znaków. Nie wykonano przeszukania baz podobnych logotypów i grafik.

Rozróżnienie prawne: historyczny pomysł lub motyw nie jest tym samym co konkretna chroniona ilustracja. Prawo autorskie chroni sposób wyrażenia, nie samą ideę. [WIPO](https://www.wipo.int/en/web/copyright/protection). Symbole państwowe podlegają również odrębnym zasadom, więc ich status nie sprowadza się do prawa autorskiego. [Ustawa o godle, barwach i hymnie](https://eli.gov.pl/api/acts/DU/2024/155/text.html). Ten kierunek wykorzystuje motywy historycznego wyposażenia, a nie gotowe godło lub herb.

Nie jest to gwarancja braku wszelkich roszczeń. Przed publikacją nadal obowiązuje weryfikacja podobieństw, warunków narzędzia i praw wymaganych przez platformę zgodnie z rejestrem projektu.
