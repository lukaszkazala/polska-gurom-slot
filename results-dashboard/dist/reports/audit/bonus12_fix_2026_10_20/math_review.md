# Niezależny przegląd poprawki 12 darmowych obrotów

Stan analizy: 20 października 2026. Przegląd kodu kompilatora i silnika; nie jest certyfikacją platformy.

## Przyczyna

Konfiguracja `FREE_SPINS = {3: 8, 4: 10, 5: 12}` i evaluator działają prawidłowo. Kompilator 0.4.0 zbierał pierwsze 100 000 unikalnych naturalnych pełnych rund, a potem dodawał tylko rzadkie wygrane z uzupełnianiem Wildami. Nie sprawdzał, czy każdy zadeklarowany typ bonusu ma choć jeden wynik z dodatnią wagą. W próbce zabrakło rundy z pięcioma Scatterami, więc końcowy selektor nie mógł jej wylosować.

Na każdym pasku jest jeden Scatter na 36 stopów. Okno ma trzy pozycje, czyli prawdopodobieństwo Scattera na bębnie to 3/36 = 1/12. Przy niezależnych stopach dokładne naturalne prawdopodobieństwo pięciu Scatterów wynosi (1/12)^5 = 1/248 832. Daje to tylko 0,4018776 oczekiwanego trafienia w 100 tys. losowań i około 66,91% szansy braku trafienia. To wyjaśnia lukę skończonego zbioru; częstotliwości generatora i końcowego eksportu należy nadal rozróżniać.

## Ocena proponowanej poprawki

Akceptuję dodanie 24 rzeczywistych, odtwarzalnych pełnych rund 12FS, w tym naturalnego świadka `seed=650496`, oraz legalnych sekwencji stopów z `wild_refill_limit=0`. Niezależnie odtworzony świadek ma 5 Scatterów, przyznaje i wykonuje 12 obrotów, a jego wypłata wynosi 5040 jednostek (50,4× stawki). Wypłat nie należy modyfikować po obliczeniu.

Przy sumie wag 10^12 proponowana łączna masa 12FS wynosi `round(10^12 / 248832) = 4 018 776`, co daje prawdopodobieństwo 0,0004018776%, średnio raz na 248 831,98 płatnej rundy. Zaokrąglenie odbiega od dokładnego naturalnego prawdopodobieństwa o mniej niż pół biletu na 10^12.

Zachowanie dotychczasowej całkowitej masy bonusów `4 969 935 540` jest spójne z zakresem poprawki. Pozostałą masę można rozdzielić na 8/10FS w proporcji istniejących 473:29 wyników. Przy dzieleniu całkowitoliczbowym masa 8FS wynosi `4 679 041 094`, a 10FS `286 875 670` (różnica jednego biletu zależnie od jawnej reguły zaokrąglenia jest dopuszczalna). Suma trzech mas musi być dokładna. Nie jest to pełna rekalibracja proporcji 3/4 Scatterów do naturalnego generatora.

Bonusowe masy i dotychczasowe rzadkie grupy należy zarezerwować przed kalibracją zwykłych niebonusowych wygranych. Korekta przez prawdziwe wyniki 0,2× i 0,3× może wtedy zachować dokładny RTP 24/25, a końcowe wyniki zerowe domykają sumę wag. Wspólna waga wszystkich dodatnich wyników, stosowana wcześniej, nie zachowa jednocześnie wszystkich tych ograniczeń.

## Warunki wymagane przed zatwierdzeniem

- Każdy typ z `FREE_SPINS` ma co najmniej jeden prawidłowy pełny wynik i ściśle dodatnią całkowitą masę.
- Każdy nowy wynik ma dokładnie pięć Scatterów na pierwotnej planszy, przyznaje 12FS i ma 12 wykonanych obrotów, chyba że poprawnie zakończyła go maksymalna wygrana.
- Każdy stop leży na rzeczywistym pasku; w planszy nie podstawia się ręcznie symboli. Uzupełnienia, kaskady i mnożniki przechodzą niezależnego ewaluatora.
- Każdy wynik odtwarza się identycznie z zapisanej specyfikacji; zdarzenia są unikalne; wypłata eksportu równa się wypłacie ewaluatora.
- Wszystkie wagi są dodatnimi liczbami całkowitymi; suma wag wynosi 10^12; suma `waga × wypłata_w_jednostkach` wynosi dokładnie 96 × 10^12.
- Łączna masa bonusów pozostaje 4 969 935 540, a masa 12FS 4 018 776. Niezerowy wynik w banku nie wystarcza, jeśli jego końcowa waga wyniosłaby zero.
- Limit wypłaty pozostaje 5000×; masa wszystkich wyników dokładnie 5000× pozostaje 125 000, czyli prawdopodobieństwo 1/8 000 000.
- Selektor poprawnie wybiera nowe wyniki na obu brzegach ich przedziału biletów. API i interfejs muszą przekazywać oraz wykonać 12FS bez pobrania dodatkowej płatnej stawki.
- Suma płatnych rund w symulacjach jest dokładnie zadeklarowaną liczbą, niezależnie od liczby obrotów wewnątrz bonusów.
- Nowy eksport ma nową wersję matematyki, aktualne skróty plików i odrębne wyniki badań. Stare symulacje 0.4.0 nie stanowią walidacji 0.4.1.

## Ograniczenia i dalsza kontrola

24 warianty pokrywają funkcję oraz tworzą skończoną warunkową próbkę. Nie dowodzą odtworzenia całego naturalnego rozkładu wypłat przy 5 Scatterach. Warto rozłożyć początkowe pozycje Scatterów między trzy dostępne wiersze na każdym bębnie i użyć odrębnych ziaren kontynuacji. Końcowy bank nadal jest modelem ważonym, a częstotliwość 12FS została jawnie dobrana na podstawie pasków.

Przy podanej masie w niezależnych próbach 10 mln / 50 mln / 100 mln oczekiwane liczby 12FS to około 40,19 / 200,94 / 401,88. Wyników nie należy wymuszać; raport powinien pokazać rzeczywiste trafienia oraz przedziały niepewności. Istniejące naturalne raporty 10/50/100 mln nie zawierają jawnych liczników 5 Scatterów, więc nie należy przypisywać im tego pomiaru.

Po przebudowie potrzebna jest pełna kontrola mechaniki wszystkich nowych wyników, walidacja całego eksportu i publicznego SDK, test granic selektora oraz test przejścia 12FS przez API i frontend. Kontrole archiwalne należy zachować jako archiwalne.
