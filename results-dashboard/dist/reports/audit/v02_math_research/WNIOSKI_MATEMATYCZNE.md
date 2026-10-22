# Kalibracja matematyczna v0.2

Ostateczny wariant to 20 stałych linii `nine_prefixes_with_v_twenty`, standardowe bębny 5×3, zmiana tylko `L1[3]` z 0,20× na 0,16× w bazowej tabeli oraz mnożnik **4× wypłat liniowych w darmowych obrotach**. Scatter nie podlega mnożnikowi. Rozwinięcie jednego Wild na bębnie 2, 3 lub 4 występuje z prawdopodobieństwem **216905037 / 1000000000** na darmowy obrót; trzy bębny wybierane są jednakowo. Pozostałe zasady: 8/10/12 FS za 3/4/5 Scatter, bez ponownych aktywacji, limit 5000× całej płatnej rundy z bonusem.

## Wynik

| Wielkość | Wartość |
|---|---:|
| RTP bazowe | 73,5257863834% |
| Wkład darmowych obrotów do RTP | 22,4742135992% |
| RTP łączne przed limitem | 95,9999999827% |
| Odchylenie od 96% | −0,0000000173 punktu procentowego |
| Częstość dodatniej wypłaty w płatnej rundzie | 29,7086953208% |
| Częstość wypłaty większej od całej stawki | 17,8895236109% |
| Częstość dodatniej wypłaty mniejszej od stawki | 11,6422179567% |
| Częstość wypłaty równej stawce | 0,1769537533% |
| Bonus | raz na 196,549763 rundy |
| Średni bonus po aktywacji | 44,1730135728× stawki |
| Mediana bonusu | 31,20× stawki |
| Odchylenie standardowe całej płatnej rundy | 5,1380297628× stawki |
| Odchylenie standardowe aktywowanego bonusu | 45,6547114712× stawki |

Płatna runda w tym raporcie obejmuje obrót bazowy oraz wszystkie przyznane mu darmowe obroty. Dodatnia wypłata nie musi oznaczać zysku względem całej stawki.

## Skąd wynika prawdopodobieństwo rozwinięcia

Niech `L` oznacza średnią sumę wypłat linii w zwykłym oknie, `E` średnią sumę po rozwinięciu jednego spośród trzech bębnów, a `S` średnią wypłatę Scatter. Dokładne wartości z ułamków wymiernych:

- `L = 110231291 / 151165440 = 0,7292096063756371`;
- `E = 15341713 / 4199040 = 3,6536239235634813`;
- `S = 1505 / 248832 = 0,006048257458847736`;
- średnia liczba FS na płatną rundę `N = 569 / 13824`;
- prawdopodobieństwo aktywacji `Q = 211 / 41472`.

Średni FS ma wypłatę `mu = 4 * ((1 − p) * L + p * E) + S`. Całkowite RTP przed limitem wynosi `L + S + N * mu`. Rozwiązanie dla dokładnych 96% to `p = 2182394757701 / 10061521780520`. Wybrany mianownik miliard daje różnicę RTP znacznie mniejszą od wymaganej dokładności, a wszystkie wypłaty nadal mieszczą się w całkowitych jednostkach 0,01× stawki.

## Współzależność linii i zmienność

Histogramy wejściowe z `audit/v02_distribution/joint_counts.npz` uwzględniają wszystkie `36^5 = 60 466 176` zestawów zatrzymań bębnów. Wspólne pola i wspólne początki linii pozostają skorelowane. Linie nie są traktowane jako niezależne zdarzenia.

Dla `X` będącego wypłatą bazową, `N` liczbą przyznanych FS oraz niezależnych wypłat FS `Z`, całkowita wypłata przed limitem ma drugi moment:

`E[Y²] = E[X²] + 2 * E[Z] * E[XN] + E[N] * E[Z²] + E[N(N−1)] * E[Z]²`.

Obliczenia momentów i składnika `E[XN]` korzystają z arytmetyki wymiernej. Wariancja rundy wynosi `26,3993498429`, a SD `5,1380297628×`. Nie ma jednej powszechnie obowiązującej granicy liczbowej dla określenia „średnio-wysoka zmienność”; należy prezentować tę etykietę wraz z SD i rozkładem wypłat. Ta kalibracja ma wyraźnie większą zmienność całej rundy niż sama gra podstawowa (SD 2,3101×), z dłuższym prawym ogonem pochodzącym z bonusu.

Rozkład bonusu daje medianę 31,20×, 90. percentyl 95,60× i 99. percentyl 230,40×. Około 2,5944% aktywowanych bonusów ma zerową wypłatę. Kwantyle obliczono konwolucją FFT; całkowita ujemna masa wynikająca z błędu numerycznego była mniejsza niż `4e−14` dla rundy i `7e−15` dla bonusu. Do ultrarzadkich zdarzeń limitu nie używano FFT.

## Limit 5000×

Największy FS po mnożniku to 714×. Największa runda bez limitu może osiągnąć `50,22 + 12 * 714 = 8618,22×`, więc ograniczenie 5000× jest rzeczywiście osiągalne i należy je stosować do całej rundy. Limit pojedynczego FS nie jest aktywny przy tej tabeli.

Mimo osiągalności limitu jego wpływ na RTP jest pomijalny. Dla dowolnego `t > 0` zachodzi

`(Y − C)+ <= exp(t * (Y − C)) / (e * t)`.

Mnożąc dokładne skończone funkcje tworzące momenty dla wypłaty bazowej i FS oraz zachowując związek liczby Scatter z liczbą FS, otrzymano dla `t ≈ 0,02404265` numerycznie obliczoną granicę Chernoffa utraty RTP mniejszą niż `1,92e−46` w jednostkach stawki. Prawdopodobieństwo wejścia w limit jest ograniczone przez `1,26e−47`. Konserwatywne zaokrąglenie obu oszacowań do `1e−40` nadal potwierdza RTP 96% z ogromnym zapasem względem dokładności `1e−7`.

To dowód kontroli wpływu limitu, a nie twierdzenie, że limit nie może wystąpić. Nie należy reklamować 5000× jako typowej lub praktycznie częstej nagrody.

## Pliki odtwarzające wynik

- `line_expectations.py`: niezależne dokładne wartości oczekiwane jednej linii i kalibracja `p`;
- `analyze_distribution.py`: momenty, częstość zysku, granica wpływu limitu i rozkład rund/bonusów;
- `line_expectations.json` oraz `distribution_analysis.json`: wyniki liczbowe;
- wejściowe histogramy i ich pełna enumeracja pozostają w `audit/v02_distribution/`.
