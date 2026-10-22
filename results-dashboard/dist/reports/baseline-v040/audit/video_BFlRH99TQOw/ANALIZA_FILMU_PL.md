# Drugi film: rachunek kombinacji i RTP

Materiał: [The Rules and Maths Behind Slot Machines — Casino Maths](https://www.youtube.com/watch?v=BFlRH99TQOw), opublikowany 15 marca 2017 r., około 3 min 16 s. Analiza: 18 października 2026 r.

**Wniosek dla projektu:** materiał przydaje się do nauki liczenia kombinacji i wartości oczekiwanej. Rachunki pokazane na ekranie są spójne. Wniosek o poprawie opłacalności przez obniżenie ceny gry wymaga jednak niezmienionych kwot nagród. Przy proporcjonalnym skalowaniu stawki i wypłat RTP pozostaje takie samo. Film nie uzasadnia zmiany zweryfikowanej matematyki POLSKA GUROM.

## Co sprawdziłem

Przeczytałem pełne angielskie napisy automatyczne, 71 segmentów obejmujących cały materiał. Dodatkowo obejrzałem kluczowe kadry: tabelę wypłat około 0:19, częstotliwości symboli około 0:39, tabelę kombinacji i zwrotów około 1:37 oraz końcowe ułamki około 2:07. Nie deklaruję odsłuchania całej ścieżki dźwiękowej.

W obrazie potwierdziłem **1073**, **13,41%** i **94,45%**. Odczyty „173” i „94.4” w automatycznych napisach nie są dowodem błędu autora. Obliczenia sprawdziłem też niezależnie; skrypt i wyniki są w tym folderze.

## Przebieg argumentacji autora

| Fragment | Temat |
|---|---|
| [0:00–0:36](https://www.youtube.com/watch?v=BFlRH99TQOw&t=0s) | Przykład trzech bębnów, tabela nagród, podwójne symbole i skalowanie wypłat liczbą kredytów. |
| [0:37–1:28](https://www.youtube.com/watch?v=BFlRH99TQOw&t=37s) | Liczebności symboli, mnożenie możliwości i sumowanie wypłat. |
| [1:29–2:11](https://www.youtube.com/watch?v=BFlRH99TQOw&t=89s) | Sumy 1073 i 7556, mianownik 8000 oraz dwa różne wskaźniki. |
| [2:12–2:25](https://www.youtube.com/watch?v=BFlRH99TQOw&t=132s) | Rozważanie niższej ceny pojedynczej gry. |
| [2:26–2:58](https://www.youtube.com/watch?v=BFlRH99TQOw&t=146s) | Pięć bębnów, dodatkowe linie i długookresowa średnia wypłat. |
| [2:59–koniec](https://www.youtube.com/watch?v=BFlRH99TQOw&t=179s) | Uogólnienie dotyczące atrakcyjnych wizualnie automatów i preferencji rozrywkowych. |

## Odtworzenie rachunku z ekranu

Przy **20 równoprawdopodobnych pozycjach na każdym z trzech niezależnych bębnów** liczba kombinacji zatrzymań to `20³ = 8000`. Iloczyn liczebności odpowiednich symboli daje liczbę kombinacji dla wskazanego wzorca.

| Wzorzec | Liczba kombinacji | Wypłata za 1 kredyt | Iloczyn |
|---|---:|---:|---:|
| 7–7–7 | 1 | 200 | 200 |
| BAR–BAR–BAR | 6 | 100 | 600 |
| Melon–melon–melon | 8 | 100 | 800 |
| Melon–melon–BAR | 4 | 100 | 400 |
| Dzwon–dzwon–dzwon | 40 | 18 | 720 |
| Dzwon–dzwon–BAR | 5 | 18 | 90 |
| Śliwka–śliwka–śliwka | 63 | 14 | 882 |
| Śliwka–śliwka–BAR | 21 | 14 | 294 |
| Pomarańcza–pomarańcza–pomarańcza | 100 | 10 | 1000 |
| Pomarańcza–pomarańcza–BAR | 25 | 10 | 250 |
| Wiśnia–wiśnia–dowolny | 240 | 5 | 1200 |
| Wiśnia–bez wiśni na drugim bębnie–dowolny | 560 | 2 | 1120 |
| **Suma** | **1073** | | **7556** |

Każdy iloczyn i obie sumy są poprawne. Wynik dzielenia:

- `1073/8000 = 13,4125%`;
- `7556/8000 = 0,9445 = 94,45%`;
- przy takim rzeczywistym zwrocie i koszcie 1 kredytu średni wynik netto gracza to `−0,0555` kredytu, czyli przewaga matematyczna kasyna wynosi 5,55%.

**7556 oznacza sumę wypłat w hipotetycznym przejściu przez wszystkie kombinacje**, a nie wypłatę pojedynczej gry. Pierwszy ułamek ma opisywać częstość trafienia; drugi opisuje średnią zwracaną część stawki. To różne wielkości.

### Dlaczego 21/24/23 symbole nie oznaczają 21/24/23 pozycji

Sumy etykiet w tabeli częstotliwości rzeczywiście wynoszą 21, 24 i 23. Autor dopuszcza jednak dwa symbole na jednej pozycji. Wtedy suma etykiet może przekraczać liczbę pozycji, a mianownik nadal może wynosić `20³`. Zastąpienie go automatycznie iloczynem `21×24×23` byłoby błędem.

Jest tu ograniczenie niezależnej weryfikacji: tabela liczebności nie określa, które symbole występują wspólnie na podwójnych pozycjach. Dlatego potwierdziłem **sumę 1073 trafień w wierszach**, lecz bez pełnego przypisania symboli do pozycji i reguły rozliczania nie certyfikuję, że są to 1073 różne wygrywające zatrzymania.

Jeśli wzorce się nakładają, częstość dodatniej wypłaty wymaga policzenia ich sumy zbiorów. Dla RTP sposób postępowania zależy od zasad: gdy wszystkie trafione wzorce płacą łącznie, wartości oczekiwane można sumować mimo nakładania. Gdy płaci wyłącznie najlepsza interpretacja, trzeba uwzględnić pierwszeństwo nagród. To warunek poprawnego modelu, a nie dowiedziony błąd tego filmu.

### Dwa wiersze z wiśniami są już rozdzielone

`2×6×20 = 240` oznacza wiśnie na pierwszych dwóch bębnach. `2×(20−6)×20 = 560` wyklucza wiśnię na drugim. Razem dają `800 = 2×20×20` kombinacji z wiśnią na pierwszym bębnie. Użycie 800 w drugim wierszu i dodanie jeszcze 240 naliczyłoby część wyników podwójnie.

## Najważniejsza korekta: niższa stawka a opłacalność

Około 2:12 autor rozważa obniżenie kosztu gry z 1 funta do około 94 pensów. Trzeba rozróżnić dwa przypadki. Poniższy rachunek przyjmuje jego zagregowaną średnią wypłatę 0,9445 przy pierwotnej cenie 1.

| Zmiana | Średnia wypłata | Koszt gry | Średni wynik netto | RTP |
|---|---:|---:|---:|---:|
| Punkt wyjścia | 0,9445 | 1 | −0,0555 | 94,45% |
| Niższa cena, nagrody w tej samej kwocie | 0,9445 | 0,94 | +0,0045 | około 100,4787% |
| Niższa stawka i proporcjonalnie niższe nagrody | 0,88783 | 0,94 | −0,05217 | 94,45% |

Drugi wiersz wymaga zachowania bezwzględnych kwot nagród. W zwykłym modelu proporcjonalnym `wypłata = mnożnik × stawka` obniżenie stawki zmniejsza kwoty, ale nie zmienia RTP. Sam film na początku wskazuje liniowe skalowanie wypłat liczbą kredytów; nie można więc bez dodatkowego założenia potraktować obniżenia zwykłej stawki jako uzyskania przewagi.

## Pozostałe doprecyzowania

**Pięć bębnów:** `20⁵ = 3 200 000` jest poprawne przy podanych założeniach. Sama większa liczba kombinacji nie wyznacza RTP ani częstości trafień. Dodatkowe linie są wyborem projektowym; pięć bębnów nie wymaga matematycznie „kompensacji” przez ukośne wygrane.

**Dłuższa gra:** dla niezależnych rund o stałym skończonym rozkładzie średnia empiryczna zbiega do wartości oczekiwanej. Nie robi tego jednostajnie ani obowiązkowo po ustalonej liczbie obrotów. Przy RTP 94,45% oczekiwana skumulowana strata po N rundach po jednym kredycie wynosi `0,0555×N`. Zbieżność średniej nie obiecuje odzyskania strat. [Gambling Commission — objaśnienie RTP](https://www.gamblingcommission.gov.uk/public-and-players/guide/return-to-player-how-much-gaming-machines-payout) również rozróżnia średnią długookresową i wynik sesji. Opisuje przy tym osobno automaty losowe i kompensowane; wniosku o stałych szansach naszego prototypu nie rozszerzam na wszystkie rodzaje urządzeń.

**Wygląd i tempo:** twierdzenie z końca filmu, że efektowne maszyny zwykle mają niższe RTP, nie jest uzasadnione przedstawionym rachunkiem ani danymi. Dla ustalonej stawki, RTP i liczby płatnych rund na godzinę oczekiwana strata na godzinę wynosi `stawka × (1−RTP) × liczba rund`. Czas animacji wpływa na tempo, a nie samą definicję RTP. Ocena atrakcyjności wizualnej nie zastępuje odczytu zasad i parametrów.

## Zastosowanie do POLSKA GUROM v0.2

Sprawdziłem zgodność bieżącego odcisku konfiguracji z dotychczasowym niezależnym raportem rozkładu oraz zgodność pierwszych momentów aktualnego `theory.py`. Matematyka pozostaje taka jak w poprzedniej analizie:

| Parametr | Obecny projekt |
|---|---:|
| Kombinacje zatrzymań w podstawie | `36⁵ = 60 466 176` |
| RTP przed limitem | 95,9999999827% |
| Rundy z dodatnią wypłatą | 29,7086953208% |
| Rundy z wypłatą ponad stawkę | 17,8895236109% |
| Bonus | średnio raz na 196,55 rundy |

Ta analiza sprawdza zgodność z istniejącą walidacją; nie wykonuje ponownie pełnej enumeracji. Dokumentacja jest już zgodna z v0.2.

Najbardziej użyteczne zasady projektowe z tego materiału:

1. **Liczyć częstość wypłaty po rozliczeniu całej planszy.** Nie sumować częstości trafień poszczególnych linii jako prawdopodobieństwa wygranej rundy; linie współdzielą pola.
2. **Zachować regułę najlepszej interpretacji Wild raz na linię.** Oddzielne linie mogą płacić razem. To rozstrzyga analogiczną niejednoznaczność do wieloznacznych symboli w filmie.
3. **Zachować jednostkę całej stawki.** Mnożników wypłat nie dzielić ponownie przez 20. Przy proporcjonalnej zmianie stawki rozkład mnożników i RTP powinien pozostać taki sam; dodatkowe zaokrąglenia walutowe wymagają sprawdzenia.
4. **Utrzymać oddzielne metryki:** RTP, dodatnia wypłata i zysk ponad stawkę. W naszym projekcie część dodatnich wypłat nadal jest stratą netto.
5. **Oddzielić prezentację od ustalania wyniku.** Animacje powinny przedstawiać wynik silnika oraz rzeczywiście zaksięgowane kwoty, w tym działanie limitu rundy.

Pierwszy film dawał szerszy opis RNG, bonusów i zmienności. Drugi dodaje krótki przykład rachunku kombinatorycznego oraz pokazuje, dlaczego trzeba pilnować mianownika, rozłączności zdarzeń i jednostek wypłaty. Oba materiały są edukacyjnym kontekstem; obecne parametry projektu wynikają z konfiguracji i zweryfikowanego rozkładu.

## Pliki pomocnicze

- `video_metadata.json`: tytuł, autor, opis, czas i rodzaj napisów.
- `transcript.json`: pełne napisy automatyczne do lokalnego sprawdzenia.
- `verify_analysis.py`: odtworzenie rachunków z obejrzanych tabel i kontrola bieżącej konfiguracji.
- `analysis_checks.json`: wyniki, zakres certyfikacji oraz odciski użytych plików projektu.

Odtworzenie obliczeń z głównego katalogu projektu: `python audit/video_BFlRH99TQOw/verify_analysis.py`.

W ramach tej analizy utworzono wyłącznie nowe materiały w `audit/video_BFlRH99TQOw/`. Kod gry, wcześniejszy raport i pliki `sources/` pozostały bez zmian.
