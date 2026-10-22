# Linie wygrywające: matematyka prototypu

Odczytano oryginał `D:\Kazaluka_slots\polska_gurom_phase2_v0.1`. Nie zmieniono oryginalnego kodu. Wyniki są analizą istniejącego prototypu, a nie zatwierdzoną tabelą końcową.

## Co jest już zaimplementowane

20 stałych linii na planszy 5×3. Tylko pierwsze trzy linie są poziome; pozostałe 17 zawierają zmianę rzędu. Każda linia wybiera dokładnie jeden symbol na każdym z pięciu bębnów. Wygrywa co najmniej trzy pasujące symbole kolejno od lewego bębna. Najlepsza interpretacja z Wild jest płacona raz na linię. Kilka różnych linii może płacić w jednym obrocie.

## Oczekiwana wypłata

Niech `g(s1,…,s5)` będzie wypłatą jednej linii, z najwyższą dozwoloną interpretacją Wild. Dokładny wzór to:

`μ = Σ_(s1,…,s5) g(s1,…,s5) · Π_j p_j(sj)`.

Nie należy niezależnie sumować wypłat dla wszystkich interpretacji Wild. Przykładowo prefiks z samych Wild spełnia wiele interpretacji, ale bieżący projekt płaci najlepszą tylko raz.

Przy jednostajnych, niezależnych stopach cyklicznych bębnów każdy wiersz ma tę samą marginalną częstość symbolu. Dlatego każda stała linia ma to samo EV, niezależnie od jej kształtu. Dla L linii `EV_linii = L·μ`; korelacje między liniami nie zmieniają tej równości. Bieżący bonus rozwija całą niezależnie wylosowaną kolumnę i zachowuje tę własność.

Ta niezmienność dotyczy nieobciętych wypłat. Przy aktywnym limicie całej rundy kształty linii mogą zmienić RTP przez zmianę prawdopodobieństwa dużych skumulowanych wypłat. Nie dotyczy też dowolnego modelu z nierównomiernymi wagami stopów, warunkowym wyborem expanding Wild zależnym od planszy lub dodatkowymi zależnościami losowania bębnów.

## Dokładne wyniki istniejącego prototypu

| Wielkość | Wartość |
|---|---:|
| Linie podstawowe RTP, L | 73,84817257172009% |
| Scatter podstawowy RTP, S | 0,6048257458847736% |
| Cała gra podstawowa RTP, B=L+S | 74,45299831760487% |
| Średnia wypłata linii przy jednym rozwiniętym bębnie, E | 3,6773893556622466× |
| Częstość bonusu, q | 0,5087770061728395% |
| Średnia liczba FS na bonus | 8,090047393364928 |
| Średnia liczba FS na płatny obrót, N | 0,04116030092592592 |
| Średnia wypłata jednego FS przy 25% rozwinięcia | 1,47925689066231× |
| Średnia wypłata bonusu po jego uruchomieniu | 11,967258352419732× |
| Bonus RTP | 6,088665876641019% |
| Całkowite RTP | 80,54166419424589% |

Każdy bęben ma jeden Scatter na 36 pozycjach; trzywidokowe okno pokazuje go z prawdopodobieństwem `3/36=1/12`. Maksymalnie jeden Scatter na bęben. Rozkład liczby Scatterów to dokładnie `Binomial(5,1/12)`, a `q=211/41472`. W aktualnym bonusie Scatter jest oceniany na planszy przed rozwinięciem Wild. Nie ma ponownych uruchomień bonusu podczas FS.

Aktualny osiągalny maksymalny wynik całej rundy wynosi 3037,3×, więc limit 5000× obecnie nie obcina wypłat. Wyniki EV wyżej są wobec tego dokładne w obecnym modelu.

## Cel 96% przy zachowaniu gry podstawowej

Docelowy udział bonusu wynosi `0,96−B=0,21547001682395128`, czyli 21,547001682395128% RTP. To nie jest dokładnie 22,5%, bo obecna gra podstawowa daje 74,453%, a wstępna alokacja projektu zakładała około 73,5%.

Potrzebna średnia wypłata bonusu po uruchomieniu to:

`(0,96−B)/q = 42,35058074750194×`.

Przy zachowaniu liczby FS potrzebna średnia wypłata jednego FS to:

`(0,96−B)/N = 5,234898967617403×`.

To około `3,538870767249611` razy obecne EV bonusu. Jest to kierunek ekonomii bonusu, a nie gotowy do wdrożenia mnożnik. Gdyby bezpośrednio przemnożyć wszystkie wypłaty bonusu, przed limitem maksymalna runda wyniosłaby około 10628,02× i limit 5000× mógłby się uruchomić. Wtedy:

`RTP(m) = B + m·RTP_bonus − E[(Y_base + m·Z_bonus − 5000)_+]`.

Parametr należy znaleźć ponownie z pełnego rozkładu i ostatecznych zasad zaokrągleń.

Dla samego prawdopodobieństwa rozwinięcia `p`:

`F(p)=B+p(E−L)` oraz `RTP(p)=B+N·F(p)`.

Przy `p=1` RTP wynosi tylko 89,61413837739872%. Do osiągnięcia 96% samym tym parametrem potrzeba byłoby `p=1,527904088814564`, czyli 152,79%; to niemożliwe prawdopodobieństwo.

Istnieje czysto algebraiczna możliwość `p=1` i mnożnika całego bonusu `1,4211993027843646`, która dawałaby 96% bez działania limitu (maksymalna runda około 4296,60×). To przykład matematycznej wykonalności, nie rekomendacja: rozwinięcie na każdym FS zmienia charakter HUSSAR CHARGE, a taka zmiana nadal wymaga oceny rozkładu, hit rate i wariancji.

Pomnożenie całej regularnej tabeli wypłat przez `1,1934421201873637` również dałoby dokładnie 96% przed zaokrągleniami i bez działania limitu. Jednak RTP gry podstawowej wzrosłoby do 88,73834539184073%, bonus dawałby zaledwie 7,261654608159265%, a częstość dodatnich trafień zostałaby taka sama. Ta droga nie realizuje obecnej intencji projektu.

## Hit rate i wariancja

`Pr(wygrana) = Pr(∪_l {linia l płaci} ∪ {Scatter płaci})`, nie suma częstości linii. Przy obecnych dodatnich wypłatach za każdy poprawny prefiks długości trzy zdarzenie trafienia linii zależy od pierwszych trzech bębnów. Zmiana odcinków linii na bębnach 4–5 nie zmienia samego zdarzenia trafienia, lecz zmienia wysokości i korelacje wypłat.

`Var(Σ_l X_l)=Σ_l Var(X_l)+2Σ_(i<j) Cov(X_i,X_j)`.

Z tego powodu kształty i współdzielenie początków linii mogą zmienić hit rate i wariancję bez zmiany nieobciętego RTP. Zwiększenie liczby linii przy obecnych wypłatach w mnożnikach całkowitej stawki podnosi RTP. Nowe linie nie są darmową zmianą graficzną. Tradycyjny zapis wypłat w mnożnikach stawki na linię wymaga przeliczenia tabeli i sposobu dzielenia całkowitej stawki.

Dla pełnej rundy bez limitu, z wypłatą gry podstawowej Y, liczbą FS K i niezależnymi wypłatami FS o średniej μ oraz wariancji σ²:

`E[T]=E[Y]+E[K]μ`,

`Var(T)=Var(Y)+E[K]σ²+Var(K)μ²+2μ·Cov(Y,K)`.

Ta kowariancja jest istotna, ponieważ liczba FS pochodzi z planszy podstawowej, która także wypłaca linie i Scatter. Nie należy zakładać niezależności wypłaty podstawowej i uruchomienia bonusu.

Po wybraniu nowej geometrii i matematyki należy obliczyć pełny rozkład wypłat, hit rate, częstość wypłat większych od stawki, momenty i osiągalny maksymalny wynik. Symulacja służy do niezależnej kontroli modelu; sama nie zastępuje dokładnego EV i obcięcia limitu.
