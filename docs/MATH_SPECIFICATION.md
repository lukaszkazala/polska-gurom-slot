# Specyfikacja matematyczna

**PROTOTYPE / NOT MATH-FROZEN**. Konfiguracja `configs/reconstruction_v0_1.json`, wersja `reconstruction-v0.1-grouped-2026-10-17`. Silnik `0.1.0-reconstruction`.

## Jednostki i linie

B=1 TOTAL BET dla wszystkich analiz; skala100, czyli 1 jednostka=0,01×B. Wypłaty zapisuje się jako nieujemne liczby całkowite. Dodawanie, porównania i cap nie zaokrąglają. Ułamki analityczne wylicza `Fraction`; zapis dziesiętny w raporcie jest tylko prezentacją. Konfiguracja nie przyjmuje podjednostek; zmiana skali wymaga jawnej zmiany konfiguracji i przeglądu adaptera.

Wartość20 w paytable oznacza0,20×B dla jednej linii. Nie dzielimy jej przez20. Dla interfejsu wymagającego mnożników stawki B/20 konwersja wynosi paytable×20; `sdk_adapter.to_line_bet_paytable` używa ułamków i testuje równoważność. Obecny evaluator oficjalnego SDK sumuje bezpośrednio mnożniki TOTAL BET; nie wymaga tej konwersji.

Pełne20 unikalnych tablic5 rzędów jest zapisane w konfiguracji. Indeksy rzędów0/1/2 oznaczają górę/środek/dół. Plansza w Pythonie ma postać `board[reel][row]`. Zatrzymanie wskazuje górny symbol, nie środkowy.

## Evaluator

Dla każdego z8 regularnych targetów policz długość początkowego ciągu pól będących targetem lub WILD. Ciąg kończy każdy inny symbol, w tym SCATTER. Jeżeli długość≥3, kandydat to dokładnie jedna kwota dla tej długości. Wybierz najwyższą kwotę; przy remisie pierwszeństwo ma kolejność L1,L2,L3,L4,P1,P2,P3,P4. Na jednej linii nie sumuje się interpretacji ani kombinacji3/4/5. Suma wszystkich20 linii jest wygraną liniową planszy. Tabela jest niemalejąca w długości.

| Przykład | Wynik brutto jednej linii |
|---|---:|
| W W P3 P3 L1 | P3,4 symbole,5,50× |
| W W W L1 L1 | L1,5 symboli,2,50×; alternatywne3P4 daje2× |
| W W W W L1 | P4,4 symbole,10×; dłuższe5L1 daje2,50× |
| W W W W W | P4,5 symboli,50× |
| W W SCATTER P4 P4 | 0× |

To jawna decyzja robocza nowej implementacji; oryginalny evaluator v0.1 jest nieznany. Brak Wild-only paytable sam w sobie nie oznacza przegranej samych Wildów. Różnicę względem bieżącego SDK opisuje `STAKE_COMPLIANCE.md`.

## Rozkład zatrzymań

Każdy bęben jest niezależny i równomierny na swoich stopach; trzy symbole pochodzą z jednego cyklicznego okna. Dla bębna r długości n, P(symbol w ustalonym rzędzie)=liczność/n. Kolejność wpływa na jednoczesne linie, trafienia i wariancję; liniowość E nie wymaga niezależności linii.

Nowe paski są identyczne w base i FS. Grupowanie po stabilnym ID to jawna, prosta rekonstrukcja przy braku oryginału; nie jest zmianą automatycznie wystrojoną do celu. Tworzy stosy L1..P3, klaster P4,P4,W,W i jeden Scatter. Szczegółowe długości, liczności, marginały i rozkłady okien zapisuje analityka. Nie zakładamy niezależności trzech rzędów.

SCATTER stoi raz na każdym36-stopowym pasku:3 okna go pokazują i żadne nie pokazuje dwóch. Zatem w tej konkretnej konfiguracji q=1/12 i liczbaSC jest Binomial(5,q). Ogólna analityka wylicza oddzielnie histogram okien każdego bębna i splata te rozkłady, bez założenia identyczności pasków.

## Pełna runda i cap

Base: losowanie stopów → naturalna plansza → linie i Scattery → wypłata oraz8/10/12 FS. FS: nowa naturalna plansza → zapis oryginału i liczbySC → los Charge → wybór jednego bębna2/3/4 → ekspansja → linie po ekspansji → Scatter payout z oryginału. Żadnych retriggerów. Koniec rozszerzenia po tym FS.

`raw_total=raw_base+raw_bonus`; `paid_total=min(raw_total,500000)` w jednostkach. `paid_base=min(raw_base,500000)`; `paid_bonus=paid_total-paid_base`. Redukcja=`raw_total-paid_total`, osiągnięcie cap=`raw_total>=500000`. Zdarzenie równe cap jest liczone jako osiągnięcie bez redukcji. Wszystkie FS są rozgrywane. Atrybucja szczegółowych składowych w symulatorze jest chronologiczna: najpierw linie danego spina, potem jego Scatter, base przed FS. To konwencja księgowa, która nie zmienia sumy.

## Analityka i estymacja

EXACT przed cap: E pojedynczej linii przez enumerację wszystkich5-symbolowych kombinacji ważonych licznościami; suma20 linii. Osobno E linii bez Charge i po wymuszeniu każdego z dozwolonych bębnów, następnie mieszanka zgodna z prawdopodobieństwami. Scatter EV z rozkładu okien. EFS/rundę=ΣPk·Nk. EVFS niezależny od triggera dzięki nowym losowaniom. RTPbonus=EFS/rundę·EVFS=Pbonus·E[bonus|bonus].

RTPpoCap=RTPprzedCap−E[redukcja]. Dokładna wartość redukcji nie jest liczona przez pełną enumerację rund. Dowód ograniczenia FS i wypukłość rozkładu dają certyfikowane ograniczenie wpływu cap; Monte Carlo raportuje rzeczywiste przyznane wypłaty. Nie określamy średniej przed cap jako dokładnej średniej po cap.

Hit base oznacza rawbase>0 przed FS i jest roboczą interpretacją celu25–30%. Hit pełnej rundy oznacza paidtotal>0. Osobno: paidtotal>1,0<paidtotal<1,paidtotal=1. Wariancja i SD dotyczą wypłaty brutto pełnej rundy w×B. Wynik netto ma tę samą wariancję i średnią RTP−1.

MONTE CARLO: jednakowe zatrzymania są używane dla wszystkich linii danej planszy. Raport zawiera próbkę wariancji z mianownikiem n−1,95% przedział normalny średniej ±1,96s/√n, histogramy i ogon bonusu. Ten przedział jest asymptotyczny i nie gwarantuje pokrycia skrajnie rzadkich zdarzeń nieobserwowanych w próbce.10k to kontrola działania, nie dowód RTP.

Kategorie wyników: EXACT (także dokładne, udowodnione ograniczenia oznaczone jako EXACT RIGOROUS BOUND), ANALYTICAL APPROXIMATION (przybliżenia), MONTE CARLO, REPORTED / UNVERIFIED, NOT CALCULATED. Dokładne ograniczenie wartości nie jest dokładnym wyznaczeniem tej wartości. Równość deterministycznej symulacji zależy od seedu, backendu RNG, konfiguracji, wersji kodu i bibliotek.
