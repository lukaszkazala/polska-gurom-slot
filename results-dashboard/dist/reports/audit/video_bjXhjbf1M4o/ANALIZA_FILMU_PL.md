# Analiza filmu i zastosowanie do POLSKA GUROM

Data weryfikacji: 18 października 2026 r.

**Wniosek:** film dobrze wyjaśnia losowanie wyników i różnicę między RTP a zmiennością. Jako materiał dla naszego projektu wymaga jednak doprecyzowania twierdzeń o bonusach, jackpotach, zbieżności RTP i gwarantowaniu zysku. Aktualny model projektu realizuje większość omawianych podstaw. Końcowy odczyt kodu i dokumentacji v0.2 potwierdza zgodność głównych parametrów; dalsza praca dotyczy przede wszystkim integracji i prawidłowej prezentacji wyników.

## Zakres i wiarygodność analizy

Źródło: [Gamble Smart — How Slot Machines ACTUALLY Work](https://www.youtube.com/watch?v=bjXhjbf1M4o).

Przeczytałem pełne angielskie napisy automatyczne: 663 segmenty, ostatni kończy się w 24:00,44. Odczytałem opis i rozdziały filmu. Odtwarzacz zgłaszał błąd, dlatego nie deklaruję odsłuchania wypowiedzi ani obejrzenia każdego kadru. Napisy mogą przekręcać nazwy i liczby. Liczby z przykładu Double Diamond sprawdziłem w artykule źródłowym i przeliczyłem niezależnie.

Odnośnik `gsgs.live/par` z opisu prowadzi do pliku o nazwie `20091117_harrigan_dixon.pdf`. Sprawdziłem artykuł **Kevin A. Harrigan i Mike Dixon, „PAR Sheets, probabilities, and slot machine play: Implications for problem and non-problem gambling”**, DOI 10.4309/jgi.2009.23.5, w [kopii wydawcy](https://cdspress.ca/wp-content/uploads/2022/08/Kevin-A.-Harrigan-Mike-Dixon-.pdf). Obejrzałem strony PDF 23–25 z tabelami 1–6, w tym tabelą mapowania bębna i tabelą prawdopodobieństw.

Zewnętrznych streszczeń automatycznych nie używam jako dowodu treści filmu. Rozdziały poniżej streszczają wypowiedzi; dalsze obliczenia i zalecenia są moją analizą projektu.

## Mapa treści filmu

| Czas | Główna myśl autora |
|---|---|
| [0:00](https://www.youtube.com/watch?v=bjXhjbf1M4o&t=0s) | Wprowadzenie; doświadczenie technika i zakres materiału. |
| [2:00](https://www.youtube.com/watch?v=bjXhjbf1M4o&t=120s) | RNG ma uniemożliwiać przewidywanie kolejnych wyników; karta gracza nie „ustawia” losowania. |
| [3:14–6:03](https://www.youtube.com/watch?v=bjXhjbf1M4o&t=194s) | Liczby są mapowane na pozycje bębna; symbole i nagrody mają różne prawdopodobieństwa. |
| [6:03](https://www.youtube.com/watch?v=bjXhjbf1M4o&t=363s) | Przykład rozkładu wypłat Double Diamond. |
| [7:22](https://www.youtube.com/watch?v=bjXhjbf1M4o&t=442s) | Gra nie musi korygować wyników po wcześniejszych wygranych lub stratach. |
| [9:23](https://www.youtube.com/watch?v=bjXhjbf1M4o&t=563s) | Bonusy z wybieraniem mogą prezentować nagrodę wylosowaną wcześniej z ważonej puli. |
| [11:38](https://www.youtube.com/watch?v=bjXhjbf1M4o&t=698s) | Darmowe obroty korzystają z losowań; ich zasady i bębny mogą różnić się od podstawy. |
| [12:52](https://www.youtube.com/watch?v=bjXhjbf1M4o&t=772s) | Rozróżnienie zwykłych progresywnych jackpotów i „must hit by”. |
| [15:09](https://www.youtube.com/watch?v=bjXhjbf1M4o&t=909s) | Zachowany postęp gry może wpływać na wartość kolejnej próby. |
| [16:49–22:38](https://www.youtube.com/watch?v=bjXhjbf1M4o&t=1009s) | Zmienność opisuje rozłożenie wypłat; autor dodaje porady dotyczące wyboru gier. |
| [22:40–24:01](https://www.youtube.com/watch?v=bjXhjbf1M4o&t=1360s) | Zakończenie i zachęta do przeczytania dokumentacji. |

## Co trzeba doprecyzować przed zastosowaniem do projektu

### 1. Losowość nie oznacza jednakowych szans nagród

Równomiernie wybierany indeks może wskazywać tabelę, w której mała nagroda występuje wielokrotnie, a największa tylko raz. To daje nierówne szanse nagród przy poprawnym losowaniu indeksu. Trzeba osobno określić generator, mapowanie i tabelę wypłat. Sam wygląd bębnów lub koła nie wystarcza do ustalenia prawdopodobieństw.

W naszym modelu zatrzymania wybierane są równomiernie z 36 pozycji każdego bębna. L1 występuje 7 razy, P4 dwa razy. Ich prawdopodobieństwa na jednym wskazanym polu wynoszą odpowiednio 7/36 i 2/36. Trzy pola jednego bębna pochodzą z sąsiednich pozycji paska: nie są trzema niezależnymi losowaniami symboli. Ten związek trzeba zachować w prezentacji i obliczeniach.

### 2. RTP jest wartością oczekiwaną, bez terminu obowiązkowego „wyrównania”

Nie istnieje liczba obrotów, po której losowa gra ma obowiązek wypłacić dokładnie swoje RTP. Przy założeniach naszego modelu średnia empiryczna zbiega do wartości oczekiwanej, ale konkretna skończona próba nadal ma odchylenia. Nie wolno wymuszać wyrównania przez zmianę szans po wynikach gracza.

W projekcie jest `36^5 = 60 466 176` równoprawdopodobnych kombinacji zatrzymań w podstawie. Po 10 mln niezależnych obrotów prawdopodobieństwo zobaczenia jednej konkretnej kombinacji wynosi zaledwie około **15,243%**. Tej liczby nie należy mylić z prawdopodobieństwem konkretnej kwoty wypłaty, którą może dawać wiele kombinacji. Pokazuje ona, dlaczego nie można utożsamiać dużej symulacji z obejrzeniem wszystkich możliwych wyników.

Jako zewnętrzny punkt odniesienia [UK Gambling Commission, RTS 7A–7B](https://www.gamblingcommission.gov.uk/manual/remote-gambling-and-software-technical-standards/rts-7-generation-of-random-outcomes) wymaga losowości, zgodnego mapowania i zakazuje kompensacyjnego zmieniania szans. Ten standard dotyczy wskazanego w nim rynku i zakresu; nie stanowi certyfikacji naszego prototypu.

### 3. Wcześniejsze obliczenie wyniku i jego losowość to różne kwestie

Projekt może obliczyć kompletną rundę na serwerze, a następnie wyświetlić kolejne obroty. Sam ten moment obliczenia nie przesądza o zgodności rozkładu ani o wpływie gracza na wynik. Trzeba zbadać algorytm generowania i zasady produktu.

Obecne `play_round()` generuje wynik podstawy oraz wszystkie przyznane darmowe obroty podczas jednego wywołania. Każdy FS dostaje nowe losowanie okna i zdarzenia rozwinięcia. To nie jest mechanizm dobierania końcowej sumy na podstawie wcześniejszych strat gracza.

Przy przyszłym bonusie z wybieraniem trzeba jednoznacznie ustalić, czy kliknięcie zmienia nagrodę, czy odsłania wcześniej wylosowaną wartość. Pokazanie niewybranych pól po zakończeniu samo w sobie nie jest dowodem sposobu losowania. Potrzebne są reguły i dokumentacja implementacji. RTS 7C osobno opisuje zachowanie ustalonego układu ukrytych nagród.

### 4. Progresywny jackpot wymaga konkretnej specyfikacji

Stała szansa trafienia przy rosnącej nagrodzie jest możliwym modelem. Nie wolno jednak wywnioskować z samej nazwy „progressive”, że szansa jest jednakowa dla każdej stawki, nominału i stanu gry. Podobnie opis ukrytego progu „must hit by” nie wyznacza automatycznie jego rozkładu, sposobu naliczania ani resetowania.

W obecnym projekcie nie ma progresywnego jackpota. **5000× jest limitem wypłaty rundy**, a nie narastającą pulą ani obietnicą trafienia przed określonym obrotem. Dodanie progresji byłoby rozszerzeniem matematyki i stanu gry, z osobnym wkładem do RTP.

### 5. Dodatnia wartość oczekiwana nie gwarantuje zysku

W rachunku prawdopodobieństwa `EV > 0` oznacza dodatnią średnią wyniku przy wskazanym modelu, a nie dodatni wynik każdej sesji. To rozróżnienie jest istotne przy wypowiedzi około 15:31–15:35. Przewaga związana ze stanem wymaga obliczenia kosztu dojścia do nagrody oraz wszystkich możliwych wyników.

Prototyp nie przechowuje postępu pomiędzy osobnymi płatnymi rundami. Brak bonusu przez długi czas nie zwiększa w nim szansy na bonus w następnej rundzie. Przy obecnej częstości aktywacji prawdopodobieństwo **braku bonusu przez 200 rund wynosi około 36,054%**. Średnia „raz na 196,55 rund” nie jest harmonogramem.

### 6. Niska zmienność nie zapewnia „zbudowania budżetu”

Zmniejszenie wariancji nie zmienia ujemnej wartości oczekiwanej gracza przy RTP poniżej 100%. Nie można zakładać, że gra o niskiej zmienności podwoi kapitał przed przejściem do innej gry. Porady z końca filmu nie stanowią podstawy matematyki produktu.

Poniższe dwa modele dydaktyczne mają tę samą średnią, ale bardzo różne rozkłady. Pozostałe wyniki płacą zero; wypłaty odnoszą się do całej stawki.

| Model dydaktyczny | Szansa dodatniej wypłaty | Wypłata przy trafieniu | RTP | Odchylenie standardowe |
|---|---:|---:|---:|---:|
| A | 50% | 1,92× | 96% | 0,96× |
| B | 1% | 96× | 96% | 9,5519× |

Etykieta zmienności powinna wynikać z rozkładu, nie z liczby animacji, mnożników lub atrakcyjności ekranu.

### 7. Przykład Double Diamond: poprawne liczby

Dla wariantu **Double Diamond Deluxe** w przywołanym artykule tabela 2 podaje 373 248 kombinacji i 8 wyników największej nagrody. Zatem:

`72^3 = 373 248`

`P = 8 / 373 248 = 1 / 46 656 ≈ 0,002143347%`

Tabela 1 również podaje 46 656 prób na jackpot w średniej. Przybliżenie „około 42 tys.” z późniejszej części napisów nie jest poprawną wartością dla tej tabeli. Niejednoznacznego odczytu mianownika w napisach około 6:58 nie traktuję jako dowodu pomyłki autora w dźwięku lub grafice.

Z tej samej tabeli wynika około **85,7146% zerowych wypłat** i **5,0797% wyników z pojedynczą wiśnią**. Są to częstości zdarzeń, a nie procent przejmowanego obrotu. Liczb tych nie przenosimy do naszej gry ani innych wersji Double Diamond. [Artykuł i tabele źródłowe](https://cdspress.ca/wp-content/uploads/2022/08/Kevin-A.-Harrigan-Mike-Dixon-.pdf).

## Co wynika z aktualnego projektu

Ponownie uruchomiłem niezależny weryfikator projektu na histogramach wszystkich kombinacji zatrzymań. Weryfikator sprawdza zgodność histogramów z odciskiem konfiguracji. Wyniki pierwszych momentów porównałem z aktualnym `theory.py`; są zgodne. **Aktualny `theory.py` uwzględnia mnożnik 4× w FS.** Podczas analizy dokumentacja została zaktualizowana; sprawdziłem ponownie README, GDD, PAR sheet i specyfikację matematyczną. Ich końcowa wersja v0.2 podaje aktualne parametry.

| Wielkość | Zweryfikowana wartość | Znaczenie |
|---|---:|---|
| RTP rundy przed limitem | 95,9999999827% | Podstawa i cały przyznany bonus na jedną płatną stawkę. |
| RTP podstawy | 73,5257863834% | Wypłaty obrotu bazowego, bez wartości kolejnych FS. |
| Wkład bonusu do RTP | 22,4742135992% | Średnia po wszystkich płatnych rundach, również bez aktywacji. |
| Dodatnia wypłata | 29,7086953208% | Runda oddaje jakąkolwiek kwotę. |
| Wypłata ponad stawkę | 17,8895236109% | Runda kończy się dodatnim wynikiem netto. |
| Wypłata poniżej stawki, ale ponad zero | 11,6422179567% | Częściowy zwrot nadal oznaczający stratę netto. |
| Wypłata równa stawce | 0,1769537533% | Wynik netto zero. |
| Szansa bonusu na rundę | 0,5087770062% | Średnio raz na 196,549763 rundy. |
| Średnia wypłata samego bonusu po aktywacji | 44,1730135728× | Bez wypłaty obrotu bazowego, który go uruchomił. |
| Mediana bonusu po aktywacji | około 31,20× | Kwantyl wyznaczony numerycznie. |
| Zerowa wypłata samego bonusu | około 2,5944% aktywacji | Nie oznacza zerowej wypłaty całej rundy; aktywacja daje też Scatter w podstawie. |
| Odchylenie standardowe rundy przed limitem | 5,1380297628× | Ilościowa miara zmienności. |
| Rozwinięcie bębna w FS | 21,6905037% | Jedna próba na każdy FS; równy wybór bębna 2, 3 lub 4. |

RTP po limicie jest minimalnie mniejsze niż powyższe RTP przed limitem. Weryfikator ogranicza utratę średniej wypłaty do mniej niż `5,207e-46` jednostki stawki, więc nie zmienia to podanych cyfr. To oszacowanie graniczne, nie obliczona dokładnie częstość trafienia limitu. Kwantyli z FFT nie używam do szacowania tak rzadkich zdarzeń.

Około **39,19% rund z dodatnią wypłatą** to częściowy zwrot poniżej stawki. Dla prezentacji produktu trzeba rozróżnić „wypłacono” i „zysk netto”. Nazwanie każdej dodatniej kwoty zarobkiem byłoby błędem.

### Zasady, które trzeba zachować

- Plansza 5×3, 20 stałych linii. Wypłaty w konfiguracji są mnożnikami **całej stawki**; nie należy ponownie dzielić ich przez 20.
- 3/4/5 Scatter przyznaje 8/10/12 FS; brak ponownych aktywacji w bonusie.
- W FS wypłaty liniowe mają mnożnik 4×. Scatter nie jest mnożony.
- Scatter jest oceniany na pierwotnym oknie, przed zamianą bębna na Wild.
- Rozwinięcie zastępuje cały jeden wybrany bęben dla oceny linii. Wynik przechowuje pierwotną i zmienioną planszę.
- Limit 5000× dotyczy sumy całej płatnej rundy z bonusem. Maksymalna suma przed limitem może wynosić 8618,22×, więc ograniczenie ma rzeczywistą funkcję.
- Linie współdzielą pola, zatem ich trafienia są zależne. Sumowanie wartości oczekiwanych jest poprawne, lecz obliczanie częstości i wariancji tak, jakby linie były niezależne, byłoby błędne.
- Paski są rotacjami tej samej sekwencji. Przy równomiernych niezależnych zatrzymaniach sama rotacja nie zmienia rozkładu okien danego bębna.

## Konkretne zalecenia dla projektu

1. **Utrzymywać zgodność dokumentacji z wersją matematyki.** Końcowy odczyt README, GDD, PAR sheet i specyfikacji potwierdza już wersję v0.2, RTP około 96%, mnożnik 4× i szansę rozwinięcia 21,6905037%. Wcześniej odczytana treść była starsza, lecz ta rozbieżność nie pozostaje aktualnym ustaleniem raportu. Przy następnych zmianach dokumenty powinny nadal wskazywać wersję, parametry i znaczenie metryk.
2. **Zachować obliczanie wyniku niezależnie od animacji.** Interfejs ma wyświetlać otrzymane plansze, trafione linie, Scatter, mnożnik i zaksięgowane wypłaty. Tempo animacji i przyciski prezentacji nie powinny uruchamiać ponownego losowania ustalonego wyniku.
3. **Oddzielić generator symulacyjny od rozwiązania produkcyjnego.** Obecny `random.Random` nadaje się do powtarzalnych badań. [Dokumentacja Pythona](https://docs.python.org/3/library/random.html) opisuje go jako deterministyczny i nieodpowiedni do zastosowań kryptograficznych. Wybór i walidację generatora oraz sposobu dostarczania wyników trzeba dopasować do docelowej platformy. Samo szybkie wywoływanie RNG w pętli nie jest dowodem bezpieczeństwa.
4. **Opisywać zmienność liczbami.** W materiałach roboczych podawać SD rundy, częstość wypłaty i zysku, częstość oraz rozkład bonusu. Użycie etykiety „średnio-wysoka” wymaga przyjętej skali porównawczej.
5. **Po zmianie ekonomii ponownie wyznaczać rozkład.** Zmiana linii, wypłat, pasków, mnożnika lub szansy rozwinięcia może zmienić kilka metryk naraz. Zachowywać zgodność konfiguracji, histogramu, raportu i wersji produktu.
6. **Projektować dodatkowy bonus lub progresję jako osobną zmianę.** Film nie jest powodem do automatycznego dodania jackpotów, postępu pomiędzy rundami czy pozornych wyborów. Każda taka mechanika wymaga własnych reguł, rozkładu i wpływu na RTP.

Analiza nie zmienia kodu gry ani istniejących dokumentów i nie dotyka `sources/`. Film wykorzystuję jako materiał edukacyjny; parametry projektu wynikają z jego konfiguracji i weryfikacji matematycznej.

## Dowody i odtwarzanie wyników

W tym samym folderze:

- `project_math_rechecked.json`: świeży wynik istniejącego weryfikatora projektu, zapisany osobno od wcześniejszych raportów.
- `analysis_checks.json`: porównanie pierwszych momentów, obliczenia przykładów oraz odciski źródeł.
- `verify_analysis.py`: odtwarzalne obliczenia użyte w tym raporcie.
- `transcript_en.json`: pobrane napisy automatyczne do lokalnej weryfikacji.
- `reference_harrigan_dixon.pdf`: kopia artykułu źródłowego; pliki `reference_page-23.png`–`reference_page-25.png` to odczytane tabele.

Odtworzenie z głównego folderu projektu, przy dostępnych zależnościach:

```powershell
python polska_gurom_v0_2/tools/verify_math.py --output audit/video_bjXhjbf1M4o/project_math_rechecked.json
python audit/video_bjXhjbf1M4o/verify_analysis.py
```

Identyfikator sprawdzonej konfiguracji matematycznej: `d79c6643b616c077afe91803cb0b96a65a7a7ef004b4d51416dad18570958148`. Ocena dokumentów odnosi się do plików o odciskach zapisanych w `analysis_checks.json`; późniejsze zmiany należy sprawdzić ponownie.
