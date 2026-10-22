# Specyfikacja matematyczna v0.2

## Model i jednostki

Każdy z pięciu bębnów ma 36 pozycji. Stopy są losowane niezależnie i jednostajnie; okno pokazuje trzy kolejne symbole cyklicznego bębna. Nie są to trzy niezależne losowania pól w jednej kolumnie. Bębny są obrotami tego samego paska, ze składem L1:7, L2:5, L3:5, L4:4, P1:4, P2:3, P3:3, P4:2, Wild:2, Scatter:1.

Wypłaty są całkowitymi jednostkami 0,01× całkowitej stawki (`PAYOUT_SCALE=100`). Stan rozliczeniowy nie korzysta z sumowania zmiennoprzecinkowego. Pola float służą do prezentacji. Kwoty w walucie i zasady ich ewentualnego zaokrąglania należą do przyszłej integracji; nie można dodawać zaokrągleń bez oceny wpływu na RTP.

## Tabela podstawowa

| Symbol | 3 | 4 | 5 |
|---|---:|---:|---:|
| L1 | 0,16 | 0,80 | 2,50 |
| L2 | 0,25 | 1,00 | 3,50 |
| L3 | 0,30 | 1,20 | 4,50 |
| L4 | 0,40 | 1,60 | 6,00 |
| P1 | 0,60 | 2,50 | 10,00 |
| P2 | 0,80 | 3,50 | 15,00 |
| P3 | 1,20 | 5,50 | 25,00 |
| P4 | 2,00 | 10,00 | 50,00 |

Jednostka tabeli: mnożnik całkowitej stawki. Nie dzielić ponownie przez liczbę linii. Scatter: 3=1×, 4=5×, 5=20×. FS: 8/10/12 za 3/4/5 Scatterów w grze podstawowej.

## Linie

Indeksy rzędów: 0=góra, 1=środek, 2=dół. Odczyt od pierwszego do piątego bębna. Wszystkie 20 linii jest zawsze aktywnych:

```text
01  11111    02  11100    03  11122    04  00000    05  22222
06  00011    07  22211    08  01110    09  21112    10  01122
11  21100    12  11001    13  11221    14  11012    15  11210
16  00012    17  01210    18  21012    19  01221    20  21001
```

Minimum 3 symbole kolejno od lewego bębna. Każda linia płaci raz według najwyższej należnej interpretacji symbolu zwykłego z Wild. Różne linie mogą płacić za wspólne trzy pola, ponieważ różnią się pełnymi ścieżkami. Nie należy sumować wielu interpretacji Wild w ramach jednej linii.

## Bonus

Mnożnik wyłącznie linii `m=4`. Scattery są liczone i opłacane na planszy przed ekspansją. Na FS rozwija się najwyżej jeden bęben z 2/3/4, wybrany jednostajnie i niezależnie od planszy. Prawdopodobieństwo ekspansji:

`p=216905037/1000000000=0,216905037`.

Silnik stosuje porównanie całkowitego losowania `randrange(1000000000)<216905037`. Testowe nadpisanie prawdopodobieństwa jest jawne i nie zmienia domyślnej kalibracji. Nie ma retriggerów; kolejne FS są niezależne i identycznie rozłożone.

## Dokładne momenty i kalibracja

Niech L będzie średnią wypłatą wszystkich linii przed mnożnikiem, E średnią po rozwinięciu jednego z trzech dopuszczalnych bębnów, S średnią wypłatą Scatter, a N średnią liczbą FS na płatną rundę.

```text
L = 110231291 / 151165440 = 0,7292096063756371
E = 15341713 / 4199040    = 3,6536239235634813
S = 1505 / 248832        = 0,006048257458847736
N = 569 / 13824
Q = 211 / 41472         = prawdopodobieństwo bonusu
μFS = 4*((1-p)*L+p*E)+S = 5,460167465653233
RTP przed limitem = L+S+N*μFS = 0,9599999998267222
```

Prawdopodobieństwo widocznego Scattera na jednym bębnie wynosi 3/36=1/12. Liczba Scatterów ma rozkład Binomial(5,1/12). Średnia liczba FS po aktywacji to 1707/211≈8,0900474, a średnia wypłata bonusu 44,1730136×.

Dokładne rozwiązanie dla p przy idealnych 96% przed limitem to `2182394757701/10061521780520`. Wybrane p z mianownikiem miliard daje odchylenie od celu tylko około −0,0000000173 punktu procentowego i prosty, bezstronny los całkowity. Nie należy przedstawiać nominalnego 96% jako gwarancji wyniku pojedynczej sesji.

## Korelacje i pełna runda

Każda ustalona linia ma to samo marginalne EV, ale linie nie są niezależne. Wspólne początki grupują wygrane; dokładna częstość dodatnich wypłat to `31187/104976=29,7086953208%`.

Dla wypłaty podstawowej X, liczby FS K oraz niezależnych wypłat FS Z:

```text
E[T]  = E[X] + E[K]*E[Z]
E[T²] = E[X²] + 2*E[XK]*E[Z] + E[K]*E[Z²] + E[K(K-1)]*E[Z]²
```

Zależność X i K przez Scattery nie jest pomijana. Wariancja pełnej rundy przed limitem wynosi 26,3993498429, SD=5,1380297628×. Etykieta projektowa „średnio wysoka” jest oceniana razem z tymi liczbami i kwantylami, bez arbitralnego uniwersalnego progu.

## Limit 5000×

Ostateczna wypłata to `min(5000,T)`. Maksymalny FS to 714×, a osiągalna runda przed limitem to 50,22+12*714=8618,22×. Limit jest aktywny dla takiej rundy; regresyjny test potwierdza dokładnie 5000× zaksięgowanej wypłaty z pełną historią i redukcją.

Funkcje tworzące momenty i nierówność Chernoffa ograniczają utratę RTP przez limit do mniej niż 5,21·10⁻⁴⁶ stawki. Obliczenie wykonano arytmetyką Decimal o precyzji 60 cyfr z zaokrągleniem na zewnątrz. Do tak rzadkich zdarzeń nie używa się ogona numerycznego FFT. W rezultacie RTP po limicie i przed limitem mają tę samą prezentowaną wartość 96,00%.

## Odtwarzanie i kontrola zmian

`tools/build_distribution.py` enumeruje pełne 36⁵=60 466 176 plansz oraz dokładne stany rozwinięcia Wild, zachowując oryginalną liczbę Scatterów. `tools/verify_math.py` porównuje histogramy z niezależnymi wartościami oczekiwanymi, używa ułamków wymiernych dla momentów i sprawdza założenia modelu. FFT służy wyłącznie do opisowych kwantyli i prawdopodobieństw ogona o jawnej dokładności numerycznej.

Histogramy i raporty są powiązane z wartościami konfiguracji i założeniami przez SHA-256. Zmiana bębnów, linii, tabel, mnożników, ekspansji, limitu lub założeń wymaga ponownej enumeracji i walidacji. Integracja generatora i rozliczenia platformy musi zachować ten model lub ponownie przeliczyć wyniki.
