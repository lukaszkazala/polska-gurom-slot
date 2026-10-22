# Częstość bonusów — aktualny model POLSKA GUROM

Analiza 19.10.2026, model v0.4.0-weighted. Sprawdzono wszystkie 100 024 pełne rundy i ich końcowe wagi, a następnie przyporządkowano zapisane wyniki wcześniejszych symulacji do typów bonusu.

Bonus uruchamia się z dokładnym prawdopodobieństwem **0.496993554%** na płatną rundę: średnio **raz na 201.21 płatnych rund**.

To częstość wynikająca z końcowego rozkładu gry. Parametry naturalnego generatora kandydatów nie określają bezpośrednio szans po nadaniu wag.

## Poszczególne bonusy

| Początkowe Scattery | Darmowe obroty | Szansa na płatną rundę | Średnio raz na | Udział w bonusach |
|---:|---:|---:|---:|---:|
| 3 | 8 | 0.468282771% | 213.55 | 94.22% |
| 4 | 10 | 0.028710783% | 3483.01 | 5.78% |
| 5 | 12 | 0.000000000% | Nie występuje | 0.00% |

**Wykryta luka:** w konfiguracji są 12 darmowych obrotów za 5 Scatterów, ale w aktualnym skończonym zestawie wyników nie ma żadnej takiej rundy. Ten bonus ma obecnie szansę 0%. Wcześniejsza odpowiedź potwierdzająca dostępność całego zakresu 8/10/12 opierała się na regule konfiguracji; końcowy eksport nie pokrywa jej w całości.
Wśród wyników są 473 różne rundy bonusowe z 8 obrotami i 29 z 10 obrotami. Nie ma wyniku z 12 obrotami. To błąd pokrycia zadeklarowanych możliwości gry, a nie kwestia braku szczęścia podczas krótkiego testu. Walidator formatu i porównanie wypłat nie sprawdzają, czy każdy zadeklarowany typ bonusu ma dodatnią wagę. Potrzebna jest osobna kontrola tego pokrycia.

## Jak często bonus pojawi się w serii

| Płatne rundy | Szansa na co najmniej jeden bonus | Szansa na brak bonusu |
|---:|---:|---:|
| 25 | 11.71% | 88.29% |
| 50 | 22.05% | 77.95% |
| 100 | 39.24% | 60.76% |
| 200 | 63.08% | 36.92% |
| 500 | 91.72% | 8.28% |
| 1000 | 99.31% | 0.69% |

Przy 100 płatnych obrotach brak bonusu ma prawdopodobieństwo około 60,76%. Średnio raz na 201 rund nie oznacza gwarancji trafienia w takim odstępie. Każde kolejne płatne losowanie ma tę samą szansę; poprzednie porażki jej nie podnoszą.
Mediana czasu do bonusu to 140 płatnych rund. Dla szansy co najmniej 90% potrzeba 463 rund; dla 95% — 602; dla 99% — 925. Są to własności rozkładu geometrycznego, bez gwarancji wyniku konkretnej sesji.
Jedna płatna runda obejmuje wszystkie jej kaskady i ewentualne darmowe obroty. Bonus nie uruchamia kolejnych darmowych obrotów. Stawka, szybkość animacji i AUTO nie zmieniają wag.

## Porównanie z wykonanymi wcześniej symulacjami

Poniższe wartości odczytano z pełnych histogramów zapisanych symulacji. Nie wykonywano ponownie 160 mln losowań na potrzeby tej analizy.

| Płatne rundy | Liczba bonusów | Częstość zmierzona | Średni odstęp w próbce |
|---:|---:|---:|---:|
| 10 000 000 | 49 775 | 0.497750% | 200.90 |
| 50 000 000 | 247 509 | 0.495018% | 202.01 |
| 100 000 000 | 495 905 | 0.495905% | 201.65 |

Częstości z prób są przybliżeniami. Dokładne prawdopodobieństwo wynika z wag: suma wag rund bonusowych 4 969 935 540 / suma wszystkich wag 1 000 000 000 000. W próbce 50 mln odchylenie liczby bonusów od oczekiwania wynosi −1,99 odchylenia standardowego, nieznacznie poza normalnym pasmem 95%; w próbce 100 mln wynosi −1,55. Nie dobierano nowych seedów ani nie zmieniano modelu na podstawie tych wyników.

## Wnioski

- Ogólna częstość bonusu to około 1:201,21.
- Około 94,22% trafionych bonusów przyznaje 8 darmowych obrotów, a 5,78% przyznaje 10.
- Bonus 12 obrotów wymaga poprawienia pokrycia eksportu oraz ponownego wyliczenia wag i kontroli RTP.
- Ta analiza nie zmieniła reguł, wag ani bieżącej gry. Dokładne RTP obecnego rozkładu pozostaje 96%, mimo wykrytej luki w pokryciu zasad bonusu.

[Dokładne liczby i źródła histogramów](<C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/bonus_frequency_2026_10_19/results.json>)
