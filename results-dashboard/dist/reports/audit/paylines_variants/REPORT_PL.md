# Warianty 20 stałych linii: audyt badawczy

Analiza dotyczy kodu `D:\Kazaluka_slots\polska_gurom_phase2_v0.1`, bez jego modyfikacji. Wyniki powstały przez dokładne zliczenie 36³ = 46 656 kombinacji stopów pierwszych trzech bębnów, z analitycznym doliczeniem scatterów na pozostałych dwóch bębnach. To nie jest estymacja z symulacji.

## Wynik

**Tak: sam inny dobór 20 stałych linii może obniżyć częstość spinów z dodatnią wypłatą z 49,62% do 29,71%, przy zachowaniu oczekiwanej wypłaty przed limitem całej rundy.** Nie trzeba w tym celu zmieniać bębnów ani tabeli wypłat. Jest to kandydat do dalszego badania, a nie gotowa, zatwierdzona matematyka gry.

| Zestaw | Linie | Różne początki na bębnach 1–3 | HF linii | HF łącznie ze scatter | Średnia liczba wygrywających linii w spinie z wygraną liniową |
|---|---:|---:|---:|---:|---:|
| 3 poziome | 3 | 3 | 12,1271% | 12,5546% | 1,1161 |
| Obecny zestaw | 20 | 20 | 49,4170% | 49,6221% | 1,8260 |
| Badawczy: 10 początków | 20 | 10 | 30,8363% | 31,1304% | 2,9263 |
| Badawczy: 9 łagodnych początków | 20 | 9 | 28,6051% | 28,9185% | 3,1545 |
| Badawczy: 9 początków z obiema liniami V | 20 | 9 | 29,3939% | **29,7087%** | 3,0699 |

HF oznacza P(wypłata > 0), a nie P(wypłata > stawka). Przykładowo wypłata 0,20× stawki też jest trafieniem. Nie policzono tu częstości wygranych netto.

## Dlaczego działa

W aktualnej grze linia płaci od trzech pasujących symboli z lewej strony, z zastępowaniem WILD. Dlatego samo istnienie wygranej na danej linii zależy wyłącznie od jej pierwszych trzech wierszy. Bębny 4 i 5 rozstrzygają wysokość wypłaty za 3, 4 albo 5 symboli, ale nie to, czy linia w ogóle płaci.

Obecne 20 linii ma 20 różnych początków. Zwiększa to liczbę różnych układów, które mogą dać choć jedną wypłatę. Gdy kilka odrębnych linii ma wspólny początek, wygrywają one równocześnie. Trafienia grupują się w mniejszej liczbie spinów. Linie muszą być z góry zdefiniowane i odrębne; każda płaci osobno zgodnie z regułami.

Dla jednej linii prawdopodobieństwo wygranej wynosi:

`q = [Σ_s (n_s + 2)^3 − 7·2^3] / 36^3 = 2105 / 46656 = 4,51174554%`.

Suma jest po ośmiu zwykłych symbolach o licznościach 7, 5, 5, 4, 4, 3, 3, 2. Odejmowanie usuwa siedmiokrotne nadmiarowe zliczenie trzech WILD. Dla dowolnych 20 linii oczekiwana liczba wygrywających linii wynosi zatem `20q = 0,9023491`. Zmienia się ich współwystępowanie.

Każdy stop jest losowany równomiernie i niezależnie na każdym bębnie. Dla konkretnego bębna wybór wiersza 0, 1 lub 2 tylko cyklicznie przesuwa indeks stopu. Rozkład pojedynczego symbolu na linii pozostaje taki sam. Każda linia ma więc ten sam rozkład wypłaty, a liniowość wartości oczekiwanej daje:

`E[suma wypłat linii] = N · E[wypłata jednej linii]`.

Zależność między liniami nie zmienia tej sumy EV, lecz zmienia rozkład łącznej wypłaty i jej wariancję. Analogiczna niezmienność EV działa w obecnym bonusie z rozszerzeniem całego bębna do WILD, ponieważ rozszerzenie również nie zależy od wiersza linii.

## EV i limit

Dla każdego badanego zestawu 20 linii, przy obecnych bębnach i tabeli:

- EV wypłat liniowych w bazie: **0,7384817257× stawki**.
- EV całej bazy ze scatter: **0,7445299832× stawki**.
- EV rundy z bonusem, przed zastosowaniem limitu rundy: **0,8054166419× stawki**, czyli RTP **80,54166419%**.

Samą zmianą przebiegu 20 linii nie naprawi się więc zbyt niskiego RTP prototypu. To niezależna decyzja dotycząca tabeli, wag i bonusu.

Zestaw 3 poziomych przy niezmienionej tabeli ma tylko 0,1168205163× EV bazy, dlatego nie jest porównaniem przy zachowanym RTP. Każda wartość tabeli w projekcie jest mnożnikiem całej stawki, nie stawki podzielonej przez liczbę linii.

Średnia dodatnia wypłata bazy rośnie z **1,5004×** dla obecnych 20 linii do **2,5061×** dla wariantu V. Jest to iloraz `EV bazy / HF`, a nie dowód określonej wariancji lub częstości wygranych netto.

Limit 5000× nie wpływa na pojedynczy spin bazy: nawet proste zawyżone ograniczenie wynosi 20·50 + 20 = 1020×. Limit skumulowanej rundy z darmowymi spinami może wpływać na RTP i jego wpływ może zależeć od zestawu linii. Zachowania EV całej rundy **po** limicie nie wolno zakładać bez ponownego badania.

## Zestaw badawczy 20 linii z V i HF 29,7087%

Wiersze: 0 = góra, 1 = środek, 2 = dół. Zapis od bębna 1 do 5.

```
 1: 1 1 1 1 1
 2: 1 1 1 0 0
 3: 1 1 1 2 2
 4: 0 0 0 0 0
 5: 2 2 2 2 2
 6: 0 0 0 1 1
 7: 2 2 2 1 1
 8: 0 1 1 1 0
 9: 2 1 1 1 2
10: 0 1 1 2 2
11: 2 1 1 0 0
12: 1 1 0 0 1
13: 1 1 2 2 1
14: 1 1 0 1 2
15: 1 1 2 1 0
16: 0 0 0 1 2
17: 0 1 2 1 0
18: 2 1 0 1 2
19: 0 1 2 2 1
20: 2 1 0 0 1
```

Wszystkie linie są odrębne. Zestaw zawiera trzy poziome i obie ikoniczne linie V. Żaden segment nie skacze bezpośrednio z góry na dół. Każda linia ma najwyżej jedną zmianę kierunku po pominięciu odcinków poziomych. Współrzędna pozioma zawsze rośnie, więc rysowana ścieżka nie cofa się do poprzedniego bębna.

Zestaw ma dziewięć wspólnych początków: `000`, `012`, `011`, `110`, `111`, `112`, `211`, `210`, `222`. Początki `000` i `111` mają po trzy kontynuacje, pozostałe po dwie. Jest 19 linii symetrycznych w odbiciu góra/dół plus jedna dodatkowa rampa `00012`. Pełna symetria góra/dół, środkowa pozioma i dokładnie 20 odrębnych linii są jednocześnie niemożliwe: jedyną linią stałą w takim odbiciu jest `11111`, a pozostałe występują parami, więc liczba byłaby nieparzysta.

## Co pozostało do sprawdzenia przed wdrożeniem

Ponownie policzyć lub wiarygodnie oszacować wariancję całej rundy, rozkład i percentyle wypłat, częstość wygranych netto, osiągalne maksimum i wpływ limitu 5000×. Zweryfikować wypłaty i współwystępowanie linii po expanding WILD, rozkład sumy darmowych spinów oraz rozliczanie limitu. Ocenić czy wspólne początki czytelnie pokazują kilka odrębnych wygranych na ekranie. Sam wynik HF i niezmienione EV przed limitem nie wystarczają do zatwierdzenia takiego zestawu.

Reprodukcja: `compare_variants.py`. Wszystkie surowe wyniki i oba zestawy 9 prefiksów: `comparison_results.json`.
