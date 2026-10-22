# Ponowne sprawdzenie wyników, dashboardu i paczki gry

Sprawdzono bieżącą matematykę `0.4.1-weighted-12fs`. Nie zmieniano silnika, wag, eksportu, dashboardu ani materiałów historycznych. Nowe skrypty i dowody zapisano wyłącznie w tym katalogu.

## Wynik kontroli deterministycznej: 100/100 zgodności

Ponownie odczytano wszystkie **100 048 pełnych wyników** i wszystkie **300 144 rekordy** trzech histogramów. Pierwsza droga liczenia korzystała z liczb całkowitych o dowolnej długości i dokładnych ułamków. Druga używała osobnych tabel SQLite, łączenia rekordów po identyfikatorze oraz sum całkowitoliczbowych. Obie drogi dały identyczne sumy losowań, wypłat, kwadratów wypłat i liczby bonusów 8/10/12 FS.

Dokładna suma wag wynosi **1 000 000 000 000**, suma ważonych wypłat **96 000 000 000 000 jednostek**, a RTP **24/25 = 96%**. Dokładna wariancja wynosi **2435830022639691/50000000000000**. Maksimum 5000× ma łączną szansę **1:8 000 000**.

| Rodzaj bonusu | Pełne wyniki | Łączna waga | Prawdopodobieństwo |
|---|---:|---:|---:|
| 8 FS | 473 | 4 679 041 094 | 0,4679041094% |
| 10 FS | 29 | 286 875 670 | 0,0286875670% |
| 12 FS | 24 | 4 018 776 | 0,0004018776% |

Łączna szansa bonusu to **0,496993554%**. Liczby i nagrody przypisano na podstawie rzeczywistych treści rozpakowanych wyników, a nie wyłącznie deklaracji w manifeście.

| Losowania | Suma wypłat w jednostkach | RTP próbki | 8 FS | 10 FS | 12 FS |
|---:|---:|---:|---:|---:|---:|
| 10 000 000 | 961 718 220 | 96,171822% | 46 769 | 2 789 | 53 |
| 50 000 000 | 4 806 249 610 | 96,1249922% | 234 023 | 14 395 | 230 |
| 100 000 000 | 9 601 048 170 | 96,0104817% | 467 294 | 29 172 | 374 |

Zgodne są także wszystkie koszyki wysokości wypłat, liczby wygranych maksymalnych, wariancje empiryczne, błędy standardowe, wartości z, normalne przedziały RTP 95% i 99%, przedziały Cloppera–Pearsona i dwumianowe przedziały liczby maksymalnych wygranych.

## Dodatkowy pełny replay oryginalnego losowania

Odtworzono wszystkie **160 mln oryginalnych biletów** na tych samych trzech seedach PCG64. Użyto innej długości partii oraz innego algorytmu przypisywania biletu do wyniku: histogramu o dokładnych całkowitych granicach CDF, zamiast pierwotnego `searchsorted` i `bincount`.

**Wszystkie 100 048 liczników w każdej z trzech serii były identyczne z oryginalnymi CSV.** Zgadzały się również skróty początkowego i końcowego stanu RNG. Są to ponownie przeliczone te same eksperymenty, a nie dodatkowe niezależne 160 mln losowań.

## Uczciwa interpretacja fluktuacji

Wszystkie trzy wyniki RTP mieszczą się w zapisanych przedziałach 95%. Nie oznacza to, że każda osobna częstość bonusu mieści się w swoim przedziale 95%:

- W 50 mln losowań 12 FS wystąpiło **230** razy, przy średniej **200,9388**. Centralny przedział dwumianowy 95% wynosi **174–229**. Wynik jest o jedno trafienie powyżej granicy; dokładne dwustronne p wynosi około **0,04423**.
- W 100 mln losowań 10 FS wystąpiło **29 172** razy, przy średniej **28 687,567**. Przedział 95% wynosi **28 356–29 020**, a dokładne dwustronne p około **0,004303**.
- Łączna liczba 10 FS, **46 356** w 160 mln, również przekracza swój indywidualny przedział 95% (**45 481–46 320**; p około **0,03347**).
- Łączna liczba 12 FS, **657**, mieści się w przedziale **594–693** przy średniej **643,00416**.

Dwumianowy przedział 95% dopuszcza wyniki poza nim; sprawdzanie wielu kategorii i serii zwiększa szansę zauważenia przynajmniej jednego takiego przypadku. Globalne porównanie czterech kategorii (brak bonusu/8/10/12) daje p około **0,01222** dla 100 mln i **0,15421** dla łącznych 160 mln. Nie skorygowano tych p o wielokrotne porównania i nie przedstawia się ich jako zatwierdzenia ani dowodu błędu RNG. Pełny replay potwierdza, że odchylenia rzeczywiście powstały w zapisanym losowaniu; nie są pomyłką w raporcie. **Nie zmieniano wag w odpowiedzi na te próbki.**

## Dashboard, historia i dostawa

- Aktualne liczby w JSON, osadzonych danych strony i samodzielnym HTML są identyczne z ponownym obliczeniem.
- Wszystkie **166 raportów** zgadza się bajt po bajcie między plikami, rejestrem skrótów i skompresowanym pakietem w HTML. Wszystkie **139 raportów historycznych** zachowuje oryginalne skróty i wyraźny prefiks archiwum.
- Aktualny licznik **135 kontroli** wynika z dziewięciu bieżących serii: 17 + 30 + 13 + 27 + 10 + 10 + 11 + 10 + 7. Testy historyczne nie są do niego doliczone. Dodatkowy audyt pełnych wyników i lokalny SDK nie podbijają tego licznika.
- Osiem raportów serii zawiera poszczególne wyniki kontroli. Raport 11 testów pokrycia przechowuje wynik całej serii; niezależne sprawdzenie składni źródła potwierdza dokładnie 11 metod testowych. Ten audyt uzgadnia istniejące dowody, nie twierdzi, że uruchomił ponownie wszystkie testy funkcjonalne.
- **19/19 plików ZIP gry** jest identycznych z bieżącym kodem, interfejsem i eksportem. Skrót ZIP to `d27d3f7f35b216f8991729a1366a178d7d8cb741e6fd6321b0d1632133d1882b`.
- Samodzielny HTML dostarczony w katalogu wydania jest identyczny ze sprawdzonym HTML w `dist`.

## Granice wniosku

To sprawdzenie potwierdza zgodność danych i paczek lokalnych. Zgodność z najnowszą dokumentacją, rzeczywista integracja Stake RGS i zatwierdzenie platformy wymagają osobnego zakresu w głównym audycie.

Testy połączenia wykorzystują localhost i wirtualny portfel. Ich raport jawnie opisuje utratę pamięci/portfela/historii przy restarcie oraz przechowywanie pełnych odpowiedzi tylko dla ostatnich 100 wyników. Odrzucenie ponownego obciążenia nie stanowi trwałego finansowego rozliczenia.

Dowody maszynowe: `simulation_dashboard_recheck.json`, `original_rng_replay.json`, `bonus_sampling_addendum.json`.
