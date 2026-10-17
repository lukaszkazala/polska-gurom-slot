# PAR sheet — rekonstrukcja

**PROTOTYPE / NOT MATH-FROZEN**. Parametry poniżej nie są finalnym tuningiem. Jednostka tabeli to×TOTAL BET na pojedynczą wygrywającą linię.

## Parametry i źródło

Pełne paski i20 linii: `configs/reconstruction_v0_1.json`. To jedyne źródło parametrów silnika. Kolejność wszystkich5 pasków jest identyczna: L1×7,L2×5,L3×5,L4×4,P1×4,P2×3,P3×3,P4×2,WILD×2,SCATTER×1; długość36. JSON przechowuje pełne listy, nie generator ani same liczności.

| Symbol | Liczność na każdym bębnie | P w ustalonym rzędzie | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|
| L1 |7|7/36|0,20|0,80|2,50|
| L2 |5|5/36|0,25|1,00|3,50|
| L3 |5|5/36|0,30|1,20|4,50|
| L4 |4|4/36|0,40|1,60|6,00|
| P1 |4|4/36|0,60|2,50|10,00|
| P2 |3|3/36|0,80|3,50|15,00|
| P3 |3|3/36|1,20|5,50|25,00|
| P4 |2|2/36|2,00|10,00|50,00|
| WILD |2|1/18|—|—|—|
| SCATTER |1|1/36|1,00|5,00|20,00|

Ostatni wiersz płaci za liczbęSC na całej planszy. Wild nie ma osobnej paytable. Naturalny Wild w ustalonym polu:1/18. LiczbaWildów w oknie bębna:0 z32/36,1 z2/36,2 z2/36. P(co najmniej1Wild w oknie)=1/9; oczekiwana liczbaWildów w3 polach=1/6. Wildy są sąsiadami na stopach33,34 (odstępy cykliczne1 i35), SC jest na35 (odstęp do następnego SC36). SC w oknie:0 z33/36,1 z3/36,≥2 niemożliwe. Nie ma różnic między bębnami ani osobnych pasków FS.

Charge1/4 na FS; warunkowy wybór bębnów2/3/4:1/3 każdy. FS awards3→8,4→10,5→12. Bez retriggerów. Cap5000× na całą rundę, wszystkie FS rozgrywane. Stan kolejnej płatnej rundy nie zależy od poprzedniej.

## Wartości teoretyczne — EXACT przed cap

| Wielkość | Dokładna wartość | Prezentacja |
|---|---:|---:|
| P(3SC)|1210/248832|0,4862719%|
| P(4SC)|55/248832|0,0221033%|
| P(5SC)|1/248832|0,0004019%|
| P(bonus)|211/41472|0,5087770%|
| Odstęp1/p|41472/211|196,549763 rundy|
| EFS na bonus|1707/211|8,090047|
| EFS na płatną rundę|569/13824|0,0411603|
| Base RTP|45018881/60466176|74,4529983%|
| E wypłatyFS|59630005/40310784|1,47925689×|
| Bonus RTP|33929472845/557256278016|6,08866588%|
| Total RTP|448823480141/557256278016|80,5416642%|
| Scatter EV na naturalny spin|1505/248832|0,0060482575×|

Dokładne ułamki mają pierwszeństwo nad zaokrąglonymi liczbami w tabeli. Szczegółowy JSON analityczny stanowi wynik uruchomienia, a nie ręcznie wpisany cel. Wartość warunkowa bonusu≈11,9672584×; do wkładu22,5pp potrzeba≈44,2236967× przy tej częstości. Hit frequency, wariancja, największa obserwacja i cap hits: MONTE CARLO w `reports/MATH_REPORT.md`, nie wynik z marginałów pojedynczej linii.

Dokładna średnia po cap: NOT CALCULATED; udowodnione wąskie ograniczenie i maksimum rundy opisuje raport oraz `reports/results/max_win_proof.json`. Maksymalna surowa wypłata12324× i przyznana5000× są osiągalne z dodatnim prawdopodobieństwem; największa obserwowana wypłata w próbce to inna metryka.
