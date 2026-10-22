# Naprawa bonusu 12 darmowych obrotów

Data: 20 października 2026. Wersja matematyki: `0.4.1-weighted-12fs`.

## Przyczyna

Reguła 5 Scatterów → 12 darmowych obrotów była poprawnie zapisana w silniku. Interfejs odtwarzał wszystkie obroty otrzymane w wyniku. Błąd występował podczas budowy skończonego zestawu wyników używanego do losowania: 100 000 naturalnych rund oraz 24 rzadkie wyniki nie zawierały żadnej rundy z pięcioma Scatterami. Kompilator nie sprawdzał pokrycia wszystkich zadeklarowanych wariantów bonusu. W efekcie 12 FS miało prawdopodobieństwo zero w używanym eksporcie.

Na istniejących paskach bębnów pięć Scatterów występuje naturalnie z prawdopodobieństwem `(3/36)^5 = 1/248832`. Próbka 100 000 rund ma około 66,9% szans pominięcia takiego zdarzenia. Samo zwiększenie przypadkowej próbki nie zabezpiecza przed powtórzeniem błędu.

## Zmiana

- `test-interface/build_math.py` uzupełnia zestaw o 24 pełne, różne wyniki 12 FS odtworzone z naturalnych ziaren generatora. Lista ziaren i wyników jest w `bonus12_witnesses.json`.
- Kompilator wymaga pokrycia 8, 10 i 12 FS przed nadaniem wag oraz dodatniej masy każdego wariantu po kalibracji. Instaluje sprawdzony eksport z manifestem na końcu.
- `test-interface/engine/polska_gurom/selection.py` przy wczytywaniu sprawdza kompletność wariantów, ich dodatnie wagi, rzeczywistą liczbę Scatterów i przyznanych obrotów oraz odtwarza wszystkie wyniki bonusowe. Brakujące, wyzerowane lub fałszywie opisane pokrycie jest odrzucane.
- Zachowano dokładne RTP 96%, łączną częstość bonusów oraz prawdopodobieństwo maksymalnej wygranej 5000× równe 1:8 000 000. Pozostałe wagi przeliczono w arytmetyce całkowitoliczbowej.

Nowy zestaw zawiera 100 048 unikalnych wyników. Wariant 12 FS ma 24 wyniki o łącznej wadze 4 018 776 na 1 000 000 000 000, czyli **0,0004018776%**, około **1:248 832 płatnych rund**. To średnia długookresowa, a nie gwarancja trafienia po określonej liczbie obrotów.

## Sprawdzenie

| Nowe rzeczywiste losowania z końcowych wag | Trafienia 12 FS | Zaobserwowane RTP |
|---|---:|---:|
| 10 000 000 | 53 | 96,171822% |
| 50 000 000 | 230 | 96,1249922% |
| 100 000 000 | 374 | 96,0104817% |
| Łącznie 160 000 000 | **657** | — |

Każda seria ma niezależne ziarno. Raport i histogramy pochodzą z rzeczywiście wykonanych losowań, nie z przemnożenia małej próbki. Wszystkie trzy RTP mieszczą się w 95% paśmie odniesienia dla wariancji tego rozkładu.

- **135/135 bieżących testów regresji**: 107 dotychczasowych sprawdzonych ponownie i 28 dodatkowych dotyczących pokrycia, API oraz interfejsu 12 FS. Obejmują też autospin, przerwane połączenia, powtórzenia żądań i przenośną paczkę gry.
- Niezależne odtworzenie i kontrola mechaniki **100 048/100 048 wyników**, w tym wszystkich **526 wyników bonusowych**.
- Walidacja formatu i matematyki przez lokalnie uruchomiony, przypięty publiczny SDK: PASS. To lokalna kontrola; nie oznacza zatwierdzenia ani wdrożenia gry przez Stake.
- W prawdziwej przeglądarce pełny animowany wynik 5 Scatterów przyznał i rozegrał **12/12 FS**. Potem autoplay ukończył **100/100 płatnych rund**, każdą z pełnym bonusem 12 FS, poprawnie rozliczając saldo. W tym wydzielonym teście kontrolowany los wybierał istniejący wynik 100024 z dodatnią wagą; nie służy on do pomiaru częstości. Szczegóły: `browser_results.json`.

SHA-256 końcowej tabeli wag: `c0d3d55fcac1c152ac8e8fe07ea08b4c2c9c9e6a3b29861dd9dddae79c67c51d`.

## Pliki do użycia

Poprawiona gra: `test-interface/POLSKA_GUROM_v0_4_1_12FS_FIX.zip`. Rozpakuj całą paczkę i uruchom `START.cmd`; zamknij wcześniej uruchomiony stary serwer gry. Nowe pliki matematyki są dołączone do paczki.

Dashboard pokazuje wyniki nowej wersji i zachowuje poprzednie wyniki jako historię. Wcześniejszych raportów nie przerabiano na wyniki nowej matematyki. Samodzielna wersja HTML: `audit/dashboard_delivery/POLSKA_GUROM_DASHBOARD.html`.
