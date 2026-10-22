# Niezależne testy matematyki v0.2

Oryginał jest referencją tylko do odczytu. Testy docelowo trafiają do kopii v0.2.

## Słabości dotychczasowych testów

- `three_four_five_kind` i `wild_substitution` dopuszczają dowolnie zawyżoną wypłatę (`>=` zamiast konkretnej kwoty).
- `multiple_paylines` wymaga tylko kwoty większej od jednej linii; nie wykrywa utraty części linii ani mnożenia całej wygranej.
- `bonus_with_expanding_wild` weryfikuje wyłącznie indeks; przechodzi nawet po wyłączeniu zmiany pól.
- `scatter_3_4_5` nie sprawdza nagrody Scatter. Mutacja nagrody do zera przechodzi.
- `max_win_cap` nie wymusza przekroczenia limitu przez prawdziwą rundę. Test samego `min` nie sprawdza księgowania rundy.
- Brak zachowanej planszy i historii FS uniemożliwia sprawdzenie prezentacji i odtworzenie płatności.
- Mutacje `double_line_payout`, `zero_scatter_payout`, `expansion_does_nothing` przechodzą wszystkie 12 istniejących funkcji testowych.

## Zasada niezależności

Oracle w `independent_oracle.py` nie importuje funkcji gry. Przecina zbiór dozwolonych interpretacji każdego kolejnego prefiksu. Kontrola starej wersji obejmuje wszystkie 10^5 sekwencji bez różnic. Samodzielny docelowy test `polska_gurom_v0_2/tests/test_game.py` stosuje tę niezależną metodę dla nowej tabeli i wszystkich 10^5 sekwencji. Tabela zapisana oddzielnie wykrywa przypadkową zmianę wartości, a nie tylko błąd algorytmu. W v0.2 kwoty są całkowite: 100 jednostek = 1× całkowitej stawki. Kwot nie dzielimy ponownie przez 20. Starszy oracle audytowy stosuje skalę 1 000 000 wyłącznie do porównania z v0.1.

## Przypadki obowiązkowe

1. **Konfiguracja:** dokładnie 20 różnych ścieżek po 5 pól; wszystkie współrzędne 0–2, trzy poziome i obie ścieżki V; zgodność całej zamrożonej tabeli i całego zestawu linii ze specyfikacją. Stała liczba aktywnych linii.
2. **Okno:** cykliczne zawijanie ostatnich dwóch stopów; dokładnie pięć niezależnych indeksów zatrzymania. Trzy pola kolumny odpowiadają kolejnym symbolom bębna, a nie trzem losowaniom.
3. **Linie:** pełne 10^5 symbolowych sekwencji wobec oracle, w tym ciąg zaczynający się od bębna 2, przerwany ciąg, Scatter jako przeszkoda, 3/4/5 symboli i wszystkie Wild. P4×3 po trzech Wild może przewyższać L1×4 — nie wolno zawsze wybierać dłuższego ciągu.
4. **Każdy szlaczek:** dla każdej ścieżki skonstruować 5×P4 na jej polach i Scatter na pozostałych. Porównać cały zbiór zdarzeń i kwoty oracle. Linie współdzielące prefiks mogą prawidłowo zapłacić równocześnie; nie zakładać jednej wygranej.
5. **Jednostki:** cała plansza L1 wypłaca dokładnie 20×2,5 = 50× stawki. Bez błędu dzielenia przez liczbę linii i bez akumulacji błędów zmiennoprzecinkowych.
6. **Zdarzenia:** unikalny identyfikator każdej płatnej linii, właściwy symbol i długość, dokładnie opłacone pola oraz pełna ścieżka do rysowania. Suma jednostek zdarzeń równa line_payout, osobno Scatter i ewentualny jawny mnożnik bonusu. Brak podświetlania nieopłaconych pól.
7. **Scatter:** 0/1/2 bez nagrody, 3/4/5 = 1×/5×/20× i 8/10/12 FS; rozrzucone po różnych rzędach i bębnach, także >5 na sztucznej planszy zgodnie z ustaloną regułą nasycenia. Wild nie zwiększa liczby Scatterów.
8. **Kolejność:** trzy Scattery, w tym jeden na rozwijanym bębnie; wynik zachowuje 3 Scattery i ich płatność mimo usunięcia ikony przez rozwinięcie. Oryginalna plansza niezmieniona. Linie liczone na zmodyfikowanej planszy.
9. **Rozwinięcie:** p=0 bez rozwinięcia i p=1 dokładnie jedna kolumna; test każdego z indeksów 1/2/3. Wszystkie trzy jej pola stają się Wild, pozostałe nie zmieniają się. Indeksy 0/4 nigdy nie występują.
10. **FS:** 8/10/12 zapisanych zdarzeń, Scattery w FS płacą, ale nie uruchamiają kolejnych FS. Historia zachowuje oba widoki planszy i indeks rozwinięcia. Porównać wymuszone dwie różne kolumny przy jednakowej wypłacie: historie muszą być różne.
11. **Limit:** wymusić bazową wygraną i kolejne bonusy przekraczające 5000×. Suma faktycznie przypisanych kwot jest dokładnie 5000×; bonus przypisany = 5000× minus przypisana baza. Surowa suma i obcięcie mają być jawne; animowane zdarzenia nie mogą udawać zaksięgowania całości surowej kwoty.
12. **Deterministyczność:** identyczny seed i konfiguracja dają identyczny wynik wraz z historią i stopami; inne seedy dają zróżnicowane wyniki. RNG podany przez użytkownika, bez globalnego RNG i zegara.
13. **Teoria:** niezależne oczekiwania linii, Scatter i liczby FS. Kalibracja całkowitego RTP ma uwzględniać maksymalną wypłatę; wartości przed limitem nie mogą być opisane jako końcowe RTP bez dowodu, że limit nie obcina.

## Rozdzielenie integracji od jednostek

Jednostkowe oracle 10^5 sekwencji obejmuje wyłącznie symbolikę jednej linii. Testy RNG sprawdzają proces generacji planszy. Testy wymuszonych plansz w `play_round` obejmują księgowanie i zdarzenia. Symulacja z przedziałem ufności sprawdza pełny proces, ale nie zastępuje dokładnego dowodu wypłaty ani deterministycznych testów rzadkich zdarzeń.
