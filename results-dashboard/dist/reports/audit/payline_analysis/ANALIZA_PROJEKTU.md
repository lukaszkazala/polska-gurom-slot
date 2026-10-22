# Ocena zygzakowatych linii w POLSKA GUROM v0.1

Analiza z 18 października 2026 r. na podstawie kodu i dokumentów prototypu w `D:/Kazaluka_slots/polska_gurom_phase2_v0.1`, dokładnych obliczeń oraz istniejącej symulacji miliona rund. Zdjęcie stanowi inspirację wizualną; nie pozwala ustalić matematyki sfotografowanego automatu. Oryginału projektu i plików referencyjnych nie zmieniono.

**Wniosek: zygzakowate linie mają sens i są zgodne z obecnym projektem.** Ich rysowanie będzie prezentacją istniejącego mechanizmu. Dobór linii może też pomóc osiągnąć założoną częstość trafień, ale osiągnięcie 96% RTP wymaga osobnego dostrojenia bonusu.

## Co już działa

Projekt ma planszę 5×3 i 20 unikalnych stałych linii: 3 poziome oraz 17 ze zmianą rzędu. Linia `(0,1,2,1,0)` oznacza góra → środek → dół → środek → góra. Co najmniej trzy zgodne symbole muszą wystąpić na kolejnych bębnach od pierwszego z lewej. Rząd może się zmieniać zgodnie z zapisaną ścieżką.

Każdą linię ocenia się raz, wypłacając najlepszą interpretację zwykłego symbolu z uwzględnieniem Wild. Różne linie mogą płacić jednocześnie i współdzielić pola. Scatter płaci według odrębnej reguły „gdziekolwiek”. Nie jest to system 243 ways ani dobieranie dowolnego szlaczka dopiero po wyniku.

Wypłaty w `config.py` są mnożnikami całkowitej stawki. Przy stawce 1 zł trzy Pierogi na jednej linii dają 0,60 zł. Dwie takie płatne linie dają razem 1,20 zł. Nie należy ponownie dzielić tych kwot przez 20. W konwencji ze stawką na linię trzeba byłoby odpowiednio przeliczyć tabelę.

## Obecny balans

| Parametr | Obecnie | Założenie projektu |
|---|---:|---:|
| Całkowite teoretyczne RTP | 80,5417% | około 96% |
| RTP gry podstawowej | 74,4530% | około 73,5% |
| Wkład bonusu do RTP | 6,0887% | około 22,5% |
| Runda z dodatnią wypłatą, dokładnie | 49,6221% | 25–30% |
| Częstość bonusu | 1 na 196,55 rundy | 1 na 150–250 |
| Średnia wypłata bonusu po uruchomieniu | 11,9673× stawki | do dostrojenia |

Wkład bonusu jest częścią całkowitego RTP, liczoną względem płatnych rund; nie oznacza zwrotu 6,09% stawki w pojedynczym darmowym obrocie. Symulacja miliona rund dała RTP 80,3087% i częstość dodatnich wypłat 49,6463%, zgodnie z dokładnymi obliczeniami w granicach wahań próby.

„Dodatnia wypłata” nie oznacza zysku. W istniejącej symulacji 29,0543% wszystkich rund kończyło się wypłatą większą od zera, lecz mniejszą od postawionej stawki. Należy oddzielnie mierzyć zwrot części stawki, zwrot całej stawki i wypłatę przewyższającą stawkę.

RTP opisuje średnią długoterminową, nie gwarantowany wynik sesji. Zob. [wyjaśnienie Gambling Commission](https://www.gamblingcommission.gov.uk/public-and-players/guide/return-to-player-how-much-gaming-machines-payout).

## Dlaczego kształt ma znaczenie

Każdy bęben losuje niezależnie jedną z 36 pozycji z równym prawdopodobieństwem. Przy cyklicznym bębnie przesunięcie wiersza nie zmienia marginalnej częstości symboli. Dlatego każda stała linia ma tę samą oczekiwaną wypłatę, niezależnie od kształtu.

Przy 20 liniach i tej samej tabeli średnia wypłata z linii jest sumą 20 identycznych wartości oczekiwanych. Nie trzeba i nie wolno zakładać, że zdarzenia wygranych na poszczególnych liniach są niezależne.

Kształty wpływają na to, **czy wygrane rozkładają się na wiele rund, czy występują razem w tych samych rundach**. Obecne 20 linii ma 20 różnych początków na pierwszych trzech bębnach. To daje wiele różnych możliwości niewielkiego trafienia.

Sprawdzono również badawczy zestaw 20 linii z dziewięcioma wspólnymi początkami, wszystkimi trzema liniami poziomymi i obiema liniami V. Linie przechodzą maksymalnie o jeden rząd pomiędzy sąsiednimi bębnami.

| Zestaw | Pełne linie | Różne początki długości 3 | Dokładna częstość dodatnich wypłat |
|---|---:|---:|---:|
| Obecny | 20 | 20 | 49,6221% |
| Badawczy, z obiema liniami V | 20 | 9 | 29,7087% |

Wariant osiąga cel częstości dodatnich wypłat bez zmiany liczby linii, składu bębnów i tabeli. Zachowuje ten sam oczekiwany zwrot **przed zastosowaniem limitu wypłaty**. Nie uznano go za gotowy do wdrożenia: trzeba jeszcze policzyć wariancję, rozkład kwot, częstość zysku netto, osiągalny maksimum oraz ewentualne obcięcie przez limit 5000×. Zmiana geometrii może zmienić ogon rozkładu i przez limit zmienić ostateczne RTP.

To dowód wykonalności kierunku, a nie stwierdzenie, że dziewięć początków zawsze daje 29,71%. Wynik zależy od konkretnych początków i kolejności symboli na bębnach.

## Właściwy model matematyczny

Wszystkie wypłaty poniżej wyrażono jako mnożniki całkowitej stawki.

1. Dla każdej linii należy wyznaczyć najlepszą dozwoloną wypłatę `g(s1,…,s5)`. Wild może tworzyć kilka możliwych interpretacji; płacona jest najlepsza, a nie ich suma.
2. Średnia wypłata jednej linii to `μ = Σ g(s1,…,s5) · Π p_j(sj)`. W tym projekcie wystarcza przeliczenie 10⁵ sekwencji typów symboli. Sama częstość symboli wystarcza do EV pojedynczej linii, ale nie do rozkładu wszystkich linii razem.
3. Średnia wypłata podstawowych linii wynosi `20·μ = 0,7384817257`. Po dodaniu Scatterów gra podstawowa daje `B = 0,7445299832`.
4. Jeden Scatter na bębnie długości 36 jest widoczny w trzech pozycjach zatrzymania. Prawdopodobieństwo Scattera na bębnie wynosi zatem `1/12`, a liczba widocznych Scatterów ma rozkład `Binomial(5,1/12)`. Bonus przy minimum trzech Scatterach występuje z prawdopodobieństwem `q = 211/41472 ≈ 0,00508777`.
5. Ponieważ bonus nie uruchamia kolejnych bonusów, a kolejne darmowe obroty mają identyczny rozkład, przed limitem `RTP = B + q · średnia liczba FS na bonus · średnia wypłata FS`.

Obecnie otrzymujemy:

`0,7445299832 + 0,0050877701 · 8,0900473934 · 1,4792568907 = 0,8054166419`.

W wersji uwzględniającej limit należy obliczać bezpośrednio `E[min(5000, Y + Σ F_i)]`, z uwzględnieniem również limitów pojedynczych spinów, jeśli mogą zadziałać. Obecny osiągalny maksymalny wynik 3037,3× jest niższy od limitu, więc obecny model nie wymaga poprawki za obcięcie. Po zmianach nie można tego zakładać.

Częstość trafień to prawdopodobieństwo sumy zdarzeń, nie suma prawdopodobieństw linii. Przy obecnych dodatnich wypłatach za minimum trzy symbole wystarczy dokładnie przeliczyć 36³ układów pierwszych trzech bębnów i dołączyć rozkład Scatterów na pozostałych dwóch. Cała przestrzeń podstawowych plansz ma 36⁵ = 60 466 176 równie prawdopodobnych wyników.

Zmienność wymaga kowariancji: `Var(Σ X_l) = Σ Var(X_l) + 2Σ Cov(X_i,X_j)`. Nie wolno traktować 15 widocznych pól jako niezależnych losowań: trzy pola kolumny pochodzą z jednego ciągłego okna bębna. Rozkład całych rund musi też uwzględniać zależność wypłaty podstawowej i liczby darmowych obrotów przez Scattery.

Pełne wzory, w tym wariancja rundy i obliczenia na ułamkach wymiernych, znajdują się w [notatce matematycznej](../paylines_agent_math/MATEMATYKA_LINII.md).

## Jak osiągnąć 96%

Przy zachowaniu obecnego RTP gry podstawowej i częstości bonusu potrzebny wkład bonusu wynosi **21,5470%**, a średnia wypłata uruchomionego bonusu **42,3506× stawki**. Przy obecnej liczbie darmowych obrotów oznacza to średnio **5,2349× na darmowy obrót**, zamiast 1,4793×.

Jest to około 3,54 razy obecna wartość bonusu. Nie stanowi gotowej rekomendacji mnożnika: prosty mnożnik może uruchomić limit 5000× i wymagać ponownego wyznaczenia parametru oraz jawnych zasad zaokrągleń.

Samo podniesienie częstości rozwinięcia Wild z 25% do 100% daje jedynie **89,6141% RTP**. Trzeba zatem zaprojektować ekonomię bonusu: rozważyć osobne bębny bonusowe, rozkład i nagrody HUSSAR CHARGE lub jawny mnożnik bonusowy. Wybór powinien wynikać z docelowego rozkładu wypłat i założonej średnio-wysokiej zmienności, a nie wyłącznie trafienia w jedną liczbę RTP.

Dodanie linii lub podniesienie całej tabeli mogłoby zwiększyć RTP, ale nie rozwiązuje jednocześnie celu częstości trafień i znaczenia bonusu. Dlatego rekomendowane są osobne etapy: dobór 20 ścieżek, walidacja rozkładu, następnie strojenie bonusu.

## Co jest potrzebne do czytelnej animacji

Repozytorium nie ma jeszcze frontendu. Silnik liczy sumy, lecz jego wynik nie przechowuje kompletnej historii plansz i wypłat każdej linii. Do rysowania ścieżek powinien przekazywać planszę przed i po rozwinięciu Wild, numer wygranej linii, symbol, liczbę opłaconych dopasowań, podświetlane komórki i kwotę. W bonusie potrzebna jest też historia kolejnych darmowych obrotów.

Najpierw warto pokazać sumę wypłat, potem kolejno wygrane ścieżki z kwotami. Przy trzech opłaconych symbolach należy wyróżnić właśnie trzy pola, nawet jeśli pomocniczo widać dalszy przebieg linii. Scattery i transformację Wild trzeba przedstawić zgodnie z kolejnością silnika: Scatter jest liczony na oryginalnej planszy, przed rozwinięciem Wild.

Opis linii i pokazywanie kolejnych wygranych są spójne z zasadami prezentacji gier liniowych opisanymi w [GLI-19 v3.0, punkt 4.4.3](https://gaminglabs.com/wp-content/uploads/2020/07/GLI-19-Interactive-Gaming-Systems-v3.0.pdf). To odniesienie projektowe, nie ocena zgodności prawnej ani certyfikat gry.

Przed integracją trzeba sprawdzić konkretne przypadki zygzaków 3/4/5 symboli, przerwanie ciągu, ciąg zaczynający się dopiero na drugim bębnie, przecinające się linie, wybór najlepszej interpretacji Wild oraz zgodność sumy animowanych kwot z wypłatą rundy. Walidacja końcowa powinna obejmować dokładne EV, ogon i limit oraz niezależną symulację z błędem statystycznym. Liczba symulowanych rund powinna wynikać z wariancji i częstości rzadkich zdarzeń.

## Pliki z wynikami

- `results.json`: bieżąca teoria, dokładna częstość wypłat, niezależna kontrola wariantu V i kontrola niezmienności plików oryginału.
- `../paylines_variants/comparison_results.json`: pełne zestawy badanych linii i dokładne częstości trafień.
- `../paylines_agent_math/tuning_results.json`: dokładne wyniki strojenia na ułamkach wymiernych.

**Rekomendacja:** zachować 20 zawsze aktywnych linii i animować ich rzeczywiste trafienia. Rozwinąć badawczy zestaw z powtarzającymi się początkami jako sposób dopasowania rytmu gry do celu 25–30%, a ekonomię bonusu dostroić osobno. Obecnej matematyki 80,54% nie traktować jako ukończonej wersji z deklarowanym RTP 96%.
