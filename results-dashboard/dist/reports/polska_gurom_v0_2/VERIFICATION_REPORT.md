# Raport ponownej weryfikacji v0.2

18 października 2026 r. Poprawiona wersja jest działającym, lokalnym prototypem matematycznym. Obliczenia, testy i dokumentację sprawdzono ponownie po wdrożeniu parametrów. Oryginał v0.1 i referencyjne pliki projektu pozostały bez zmian.

## Wynik końcowy

| Parametr | v0.1 | v0.2 | Założenie |
|---|---:|---:|---:|
| RTP nominalne, po limicie | 80,5417% | **96,0000%** | około 96% |
| RTP gry podstawowej | 74,4530% | **73,5258%** | około 73,5% |
| Wkład bonusu do RTP | 6,0887% | **22,4742%** | około 22,5% |
| Rundy z dodatnią wypłatą | 49,6221% | **29,7087%** | 25–30% |
| Bonus | 1/196,55 | **1/196,55** | 1/150–1/250 |
| Średnia wypłata uruchomionego bonusu | 11,9673× | **44,1730×** | bonus o istotnym udziale |
| Limit całej rundy | 5000× | **5000×** | 5000× |

Dokładne RTP przed ograniczeniem: `501530650123874911981 / 522427760640000000000 = 0,9599999998267222`. Nominalne 96,00% jest wartością zaokrągloną, a nie obietnicą wyniku pojedynczej sesji. Strata wartości oczekiwanej na skutek limitu jest mniejsza niż `5,21·10^-46` stawki, więc nie zmienia prezentowanego RTP.

## Zmiana parametrów

Wybrano 20 stałych ścieżek z dziewięcioma wspólnymi początkami, wszystkimi trzema poziomymi i obiema liniami V. Nie dodano linii i nie zmieniono zwykłych wygranych w system „gdziekolwiek”. Zmieniono tylko wypłatę L1 za trzy symbole z 0,20× na 0,16×. Bębny, pozostała podstawowa tabela, nagrody Scatter oraz 8/10/12 FS pozostały takie same.

W bonusie wypłaty liniowe otrzymują mnożnik 4, Scattery pozostają bez mnożnika. Szansa rozwinięcia pojedynczego bębna 2/3/4 wynosi 21,6905037% na FS i jest losowana całkowitoliczbowo. Nie ma retriggerów. Wszystkie kwoty silnika są całkowitymi setnymi całkowitej stawki; wynik zawiera historię plansz, zdarzenia płatnych linii i rzeczywiste kredyty po ograniczeniu.

## Kontrola niezależna od silnika

- Ponownie enumerowano **60 466 176** rzeczywistych zatrzymań bębnów oraz trzy stany pojedynczego rozwinięcia Wild. Nowe histogramy są identyczne z pierwszą niezależną enumeracją.
- Dla **100 000** możliwych sekwencji typów symboli porównano niezależny, zamrożony oracle, produkcyjny scorer i tablicę używaną do enumeracji. Brak różnic.
- Dodatkowo porównano **1000 naturalnych plansz podstawowych i 3000 rozwiniętych plansz FS** z niezależnym evaluatorem. Kwoty, Scattery i sumy zdarzeń linii są zgodne.
- Momenty pierwszego i drugiego rzędu obliczono na ułamkach wymiernych, zachowując korelacje linii i zależność wypłaty podstawowej od liczby przyznanych FS.
- Kontrola zgodności konfiguracji odrzuca stare histogramy i nieobsługiwane założenia, np. włączenie retriggerów bez zmiany modelu.

Fingerprint konfiguracji matematycznej:

```text
d79c6643b616c077afe91803cb0b96a65a7a7ef004b4d51416dad18570958148
```

Szczegóły: `verification/distribution_summary.json`, `verification/math_validation.json` i `verification/consistency_checks.json`.

## Testy i rzeczywisty limit

**20/20 testów zakończyło się powodzeniem.** Obejmują ocenę wszystkich linii, zakotwiczenie od lewej, przerwanie ciągu, najlepszą interpretację Wild, jednostki całkowitej stawki, kolejność Scatter/ekspansja, niezmienność wejściowej planszy, próg losowania całkowitego, historię 8/10/12 FS bez retriggerów, rozliczenie limitu i dokładne wartości matematyczne.

Osiągalny układ pięciu Scatterów wypłaca w podstawie 50,22× i przyznaje 12 FS. Osiągalny układ FS z rozwinięciem trzeciego bębna wypłaca 714×. Test 12 takich FS daje:

```text
surowa wypłata: 50,22 + 12*714 = 8618,22×
zaksięgowana wypłata: 5000,00×
redukcja: 3618,22×
kredyty FS: 6*714,00 + 665,78 + 5*0,00
podstawa + kredyty FS: dokładnie 5000,00×
```

Jest to test logicznego działania sufitu na realnych oknach bębnów, nie twierdzenie o częstym osiąganiu limitu. Wpływ bardzo rzadkich zdarzeń na RTP ograniczono osobno funkcjami tworzącymi momenty, z użyciem 60-cyfrowej arytmetyki Decimal i zaokrągleń na zewnątrz.

## Symulacje kontrolne

Parametry wyznaczono matematycznie przed symulacjami; nie zmieniano ich w odpowiedzi na zaobserwowane wyniki.

| Metoda | Rundy | Seed | RTP próby | 95% przedział RTP | Dodatnia wypłata |
|---|---:|---:|---:|---:|---:|
| Rzeczywisty `game.play_round` | 100 000 | 20261018 | 99,5183% | 95,9934–103,0431% | 29,9140% |
| Rzeczywisty `game.play_round` | **1 000 000** | 20261019 | **96,9815%** | **95,9573–98,0057%** | **29,7001%** |
| Niezależny model histogramów | **10 000 000** | 20261018 | **95,9756%** | **95,6585–96,2926%** | **29,7079%** |

Przedziały RTP korzystają z empirycznego odchylenia i przybliżenia normalnego; są diagnostyką Monte Carlo, nie zamiennikiem dokładnego modelu. Symulacja histogramów próbkuje pełne rozkłady całkowitoliczbowo, niezależnie od implementacji gry. Nie jest przedstawiana jako 10 mln wykonań silnika. Obie metody dają wyniki zgodne z teoretycznym 96% w podanych przedziałach; w żadnej próbie nie zaobserwowano sufitu, co nie zastępuje opisanego testu i granicy matematycznej.

## Charakter wypłat

Wypłata większa od stawki występuje w 17,8895% rund, częściowy zwrot w 11,6422%, a zwrot dokładnie stawki w 0,1770%. Prawdopodobieństwo zerowej wypłaty to około 70,2913%.

SD całej rundy wynosi około **5,1380×**, a aktywowanego bonusu **45,6547×**. Mediana bonusu wynosi 31,20×, 90. percentyl 95,60×, 99. percentyl 230,40×; około 2,5944% aktywowanych bonusów nie wypłaca nic. Kwantyle wyznaczono numerycznie przez FFT i oznaczono jako przybliżone. Sufit 5000× nie jest często występującą nagrodą tej kalibracji.

„Średnio wysoka zmienność” pozostaje etykietą projektową wspartą powyższym rozkładem. Nie ma tu arbitralnej deklaracji uniwersalnego progu branżowego. Dalsze zmiany zmienności powinny wynikać z oceny tego rozkładu i wymagać nowej walidacji.

## Granice tej wersji

Zadanie zmiany matematyki i lokalnego silnika zostało wykonane. Integracja aktualnego Stake Engine SDK, produkcyjnego generatora, rzeczywistych nominałów i walut oraz frontendu jest odrębnym etapem. Musi zachować tę samą matematykę albo uruchomić ponowną kalibrację i walidację. Sam frontend ma jedynie przedstawiać autorytatywną historię i zaksięgowane kwoty.
