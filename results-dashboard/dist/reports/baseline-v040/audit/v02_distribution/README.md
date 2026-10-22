# Dokładne rozkłady matematyczne v0.2

`exact_distribution.py` odczytuje referencyjne bębny v0.1, przyjmuje nowe 20 linii z wariantu `nine_prefixes_with_v_twenty` oraz zmienia wyłącznie wypłatę `L1 × 3` na `0.16` stawki. Oryginał nie jest modyfikowany.

`joint_counts.npz` zawiera całkowitoliczbowe histogramy:

- `base`: wszystkie `36^5 = 60 466 176` plansze gry podstawowej.
- `forced_1`, `forced_2`, `forced_3`: rozkład po rozwinięciu Wild odpowiednio na drugim, trzecim i czwartym bębnie. Numeracja od zera.
- `fs_mixture_25pct`: suma `9*base + forced_1 + forced_2 + forced_3`, mianownik `12*36^5`.

Każdy histogram ma osie `[suma wypłat linii w jednostkach 0.01 stawki, liczba Scatterów na oryginalnej planszy]`. `base` i każdy `forced_*` mają mianownik `36^5`. Scatter pozostaje oceniany na oryginalnej planszy. Zastąpiony Wildem bęben można usunąć z enumeracji: 33 jego pozycje nie zawierają Scattera, a 3 zawierają jednego. Te wagi zachowują dokładny rozkład łączny.

**Mnożnik darmowych obrotów ×4 nie jest zastosowany w zapisanych histogramach.** Przy budowie finalnego rozkładu FS należy użyć `payout_units = 4*line_units + [0,0,0,100,500,2000][scatter_count]`. Mnożnik nie obejmuje Scatterów. Finalna szansa rozwinięcia ustalana jest osobno przez kalibrację.

`summary.json` zawiera dokładne średnie jako ułamki, momenty, wariancję, częstość wypłat dodatnich, większych od stawki i równych stawce oraz maksima warunkowe według Scatterów. Wiersz `fs_mixture_25pct` jest diagnostyką przed mnożnikiem, a nie finalnym RTP projektu.

Kontrole: referencyjna ocena 1000 deterministycznie wybranych sekwencji symboli; pełne zachowanie masy prawdopodobieństwa; niezależnie znana średnia gry podstawowej i częstość dodatnich wypłat; dokładna zgodność histogramu Scatterów ze współczynnikami dwumianowymi `C(5,k)*3^k*33^(5-k)`.

`maximum_witness.py` wyznacza rzeczywiście osiągalne plansze maksymalnych wypłat przy rozwinięciu Wild. Służą do deterministycznych testów mnożnika i limitu rundy.
