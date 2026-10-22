# PAR sheet — POLSKA GUROM v0.2

Parametry skoordynowane z kodem i niezależną walidacją z 18 października 2026 r. Jednostka wypłat: mnożnik całkowitej stawki. „Runda” obejmuje płatny obrót i przyznany mu bonus.

| Parametr | Wartość |
|---|---:|
| Plansza | 5×3 |
| Stałe linie, zawsze aktywne | 20 |
| Długość każdego bębna | 36 |
| Nominalne RTP po limicie | 96,00% |
| Dokładne RTP przed limitem | 95,99999998267222% |
| RTP podstawowe | 73,52578638344849% |
| Udział bonusu | 22,474213599223736% |
| Górna granica utraty RTP przez limit | <5,21·10⁻⁴⁶ stawki/rundę |
| Dodatnia wypłata | 29,70869532083524% |
| Wypłata większa od stawki | 17,88952361085797% |
| Dodatnia wypłata mniejsza od stawki | 11,64221795669698% |
| Wypłata równa stawce | 0,1769537532802859% |
| Bonus | 0,5087770061728395%, raz na 196,549763 rundy |
| Średnia liczba FS na bonus | 8,0900473934 |
| Mnożnik linii w FS | 4 |
| Mnożnik Scatter w FS | 1 |
| Prawdopodobieństwo ekspansji na FS | 216905037/1000000000 = 21,6905037% |
| Dopuszczalne rozwijane bębny | 2, 3, 4; wybór równomierny |
| Średnia wypłata FS | 5,4601674657× |
| Średnia wypłata aktywowanego bonusu | 44,1730135728× |
| Mediana aktywowanego bonusu, numerycznie | 31,20× |
| 90. percentyl bonusu, numerycznie | 95,60× |
| 99. percentyl bonusu, numerycznie | 230,40× |
| Zerowa wypłata bonusu po aktywacji | 2,5944058650% |
| Wariancja pełnej rundy przed limitem | 26,3993498429 |
| SD pełnej rundy przed limitem | 5,1380297628× |
| SD aktywowanego bonusu przed limitem | 45,6547114712× |
| Maksymalny FS | 714× |
| Maksymalna osiągalna runda przed limitem | 8618,22× |
| Maksymalna wypłata po limicie | 5000× |

Tabela wypłat, wszystkie 20 linii, dokładne ułamki i pełne zasady są w [MATH_SPECIFICATION.md](MATH_SPECIFICATION.md). Bębny mają skład 7/5/5/4/4/3/3/2/2/1 odpowiednio L1/L2/L3/L4/P1/P2/P3/P4/Wild/Scatter. Jedyna zmiana bazowej tabeli względem v0.1 to L1 za trzy symbole: 0,20×→0,16×.

Kwantyle są opisową konwolucją FFT, a nie podstawą kontroli bardzo rzadkiego limitu. Użyto dla niego osobnej, zaokrąglanej na zewnątrz granicy Decimal/Chernoff. Wszystkie liczby odnoszą się do dołączonej konfiguracji. Wyniki symulacji i ich przedziały statystyczne są w [VERIFICATION_REPORT.md](../VERIFICATION_REPORT.md) i katalogu `verification/`.
