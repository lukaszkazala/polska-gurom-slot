# Decyzja projektowa: przebudowa rozkładu wysokich wygranych

Data: 22.10.2026. Punkt odniesienia: matematyka `0.5.0-any-start`.

## Rozstrzygnięcie

**Wybrany kierunek: przebudować rozkład wysokich wygranych.** Dodać zróżnicowane wyniki pośrednie między 500× a 5000× oraz umożliwić osiągnięcie limitu także w darmowych obrotach. Zachować możliwość maksimum w bazie. To zmiana projektu matematyki; dotychczasowe obliczenia wypłat nie zostały zakwestionowane.

Status: decyzja kierunkowa zapisana; przebudowa banku i wdrożenie pozostają do wykonania. Bieżąca gra nadal korzysta z dotychczasowego rozkładu.

## Uzasadnienie oparte na aktualnym banku

Ponowne obliczenie z końcowych wag potwierdziło dokładne RTP 96%, maksimum 5000× i jego łączną częstość 1:8 000 000. Oba lokalne warianty interfejsu mają identyczną tabelę wag.

| Ustalenie | Wartość |
|---|---:|
| Pełne rundy z dodatnią wagą | 100 049 |
| Rundy wypłacające co najmniej 500× | 25 rekordów, 19 różnych kwot |
| Najwyższa wypłata rundy zawierającej bonus | 528,8× |
| Rekordy maksimum w bazie / w bonusie | 4 / 0 |
| Największa przerwa między możliwymi wypłatami | 3010,9×–4027,4×, czyli 1016,5× |
| Wkład wypłat ≥500× do RTP | 2,44355542032 p.p. |
| Wkład samego maksimum do RTP | 0,0625 p.p. |

Pozostałe duże puste przedziały to 528,8×–990,9×, 995,3×–1986,9×, 2018,4×–2968,3× i 4029,6×–5000×. Granice przedziałów są osiągalne; brak dotyczy ich wnętrza.

Przyczynę widać w kompilatorze: dobiera po cztery rzadkie rundy blisko sześciu punktów docelowych. Zmiana samych wag obecnych rekordów nie stworzy brakujących kwot ani maksimum w bonusie. Potrzebne są dodatkowe legalne przebiegi gry i ponowny dobór wag.

Ocena projektowa: bonus z mnożnikiem linii 4× i ekspansją Wildów powinien mieć dostęp do najwyższych nagród. Obecny bank ogranicza tę rolę bonusu. Przebudowa poprawi różnorodność możliwych rezultatów; sama w sobie nie gwarantuje częstszych wysokich wygranych ani lepszych wyników krótkich sesji.

## Granice przebudowy

- Zachować dokładne RTP 24/25, limit całej rundy 5000× i łączną szansę maksimum 1:8 000 000, sumowaną po bazie i bonusie. Dodanie maksimum bonusowego musi przesunąć część istniejącej masy maksimum, a nie ją podwoić.
- Zachować koszt rundy 1×, krok wypłaty 0,1×, zasady linii i kaskad oraz przydziały 8/10/12 darmowych obrotów.
- Zachować masy wejścia do bonusów: 8 FS — 4 679 041 094, 10 FS — 286 875 670, 12 FS — 4 018 776 biletów przy łącznej masie 10¹². Nowe wysokie bonusy mają otrzymać część istniejącej masy odpowiedniego wariantu.
- Zacząć od przebudowy banku i wag. Zmianę bębnów, tabeli wypłat lub mechaniki traktować jako rozszerzenie zakresu dopiero wtedy, gdy obecne reguły uniemożliwią osiągnięcie celów.
- Rozpocząć strojenie od obecnego budżetu RTP dla wypłat ≥500×. Każde przesunięcie zwrotu ze zwykłych wypłat do tego zakresu wykazać jawnie w porównaniu wariantów.

## Warunki odbioru nowej matematyki

1. W zakresie od 500× do 5000× odstęp między kolejnymi osiągalnymi kwotami o dodatniej wadze ma wynosić najwyżej 250×; uwzględnić także brzegi zakresu. To przyjęty cel projektu, a nie wymóg platformy. Nie trzeba generować każdej kwoty co 0,1×.
2. Dla pasm wysokich wypłat przed doborem wag określić docelową częstość i wkład w RTP. Same śladowe wagi dodane wyłącznie dla wypełnienia luk nie wystarczą do odbioru.
3. Maksimum ma mieć dodatnią wagę w bazie i podczas darmowych obrotów. Pokrycie sprawdzić osobno dla 8/10/12 FS; co najmniej jeden wariant bonusu musi zawierać rzeczywiste osiągnięcie limitu w trakcie FS. Dokładny podział masy maksimum między bazę i warianty bonusu należy ustalić podczas strojenia, przy stałej sumie 125 000 biletów.
4. Każda nowa runda ma wynikać z legalnych plansz i przejść, a jej wypłata z obowiązujących zasad. Zweryfikować pełne zdarzenia, częściową wypłatę przy limicie oraz zakończenie niewykonanych FS po osiągnięciu capu.
5. Przeliczyć pełny bank: RTP, częstości, wkłady bazy i bonusu, wariancję, hit rate, częstość zysku, koncentrację wysokich wypłat i największe luki. Przedstawić porównanie z punktem odniesienia oraz przeprowadzić regresje selektora, rozliczeń i prezentacji maksimum.

Wypełnienie warunków odbioru wymaga nowego eksportu i jego weryfikacji. Ten dokument rozstrzyga kierunek projektu i nie stanowi potwierdzenia wykonania przebudowy.

## Dowody

- [Ponowne obliczenie z aktualnych wag](EVIDENCE.json) — także sumy kontrolne plików źródłowych.
- [Pełny wcześniejszy audyt matematyki](../../audit/full_review_2026_10_20/math/RAPORT_MATEMATYKA_PL.md).
- [Kompilator aktualnego banku](../../test-interface-any-start/build_math.py).

Materiały w `sources/` oraz pliki gry nie zostały zmienione.
