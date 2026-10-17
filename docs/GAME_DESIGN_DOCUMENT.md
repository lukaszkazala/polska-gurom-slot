# POLSKA GUROM — Game Design Document

**PROTOTYPE / NOT MATH-FROZEN** — 17.10.2026. Nowa rekonstrukcja; wszystkie wartości liczbowe konfiguracji są prototypowe.

## Status założeń

| Kategoria | Zakres |
|---|---|
| Zatwierdzone reguły | 5 bębnów × 3 rzędy, 20 stałych aktywnych linii, LTR od bębna 1, minimum 3 symbole, kombinacje 3/4/5, 10 stabilnych ID, B=TOTAL BET, 8/10/12 FS za 3/4/5 SC, cap pełnej rundy 5000× |
| Cele projektowe | RTP około96%, wczesny zakres95,5–96,5%, base73,5pp + bonus22,5pp, hit base25–30%, bonus1/150–250, zmienność medium-high |
| Parametry rekonstrukcji | Historyczne liczności36, paytable, Scatter1/5/20×, Charge25%, równe wagi bębnów2/3/4; nowe pełne paski pogrupowane i nowe konkretne linie |
| Historycznie raportowane | RTP80,5417%, base74,4530%, bonus6,0887%, hit49,6463%, maxobserwowane130×; średnie częściowo sprawdzone analitycznie pod jawnymi założeniami, rozkład historyczny nieodtwarzalny |
| Decyzje robocze | Najlepsza z regularnych interpretacji Wildów; wspólne paski base/FS; Scatter z naturalnej planszy także w FS; brak retriggerów; wszystkie FS rozgrywane po cap |
| Nierozstrzygnięte | Oryginalne paski/linie/evaluator, finalne grafiki L/P, kryterium liczbowe medium-high, docelowe parametry i zgodność SDK/RGS |

## Reguły

Każdy bęben niezależnie wybiera jeden równomierny stop na cyklicznym pasku. Plansza zawiera trzy kolejne pozycje z zawijaniem; pola nie są losowane niezależnie. Wszystkie20 linii jest aktywnych. Każda płaci jedną największą poprawną interpretację zaczynającą się na bębnie1. Wszystkie wypłaty są brutto. Brak Ways, kaskad, bonus buy, jackpotu, gamble i progresji.

WILD zastępuje osiem symboli regularnych, nigdy SCATTER. Nie ma własnej tabeli; pięć Wildów może zapłacić jako P4. SCATTER oceniany jest na całej naturalnej planszy, niezależnie od linii. Konstrukcja pasków gwarantuje najwyżej jeden SC na bęben i pięć na planszę. Za3/4/5 SC płatny spin przyznaje8/10/12 FS oraz wypłatę Scatter. W FS Scattery wypłacają, lecz nie przyznają spinów.

## POLSKA GUROM BONUS / HUSSAR CHARGE

Każdy FS losuje nową naturalną planszę z tych samych pasków. Zachowuje się jej Scattery, następnie losuje Charge z prawdopodobieństwem1/4. Przy Charge jeden z bębnów2,3,4 wybiera się z wagami1:1:1 i zamienia wszystkie jego trzy pola na Wild. Linie liczone są na rozszerzonej planszy, Scatter payout na naturalnej. Rozszerzenie trwa jeden spin i nigdy nie jest sticky. W kolejnym FS wszystko losuje się od nowa. Nie ma mnożników ani retriggerów.

## Rozliczenie i prezentacja

Runda zawiera płatny spin oraz wszystkie wynikające FS. Cap5000× dotyczy sumy. Wszystkie FS rozgrywa się mimo wcześniejszego osiągnięcia cap; późniejsze surowe wygrane mogą mieć zerową przyznaną część. Trace zapisuje obie kwoty. Frontend powinien odtwarzać trace, bez własnego losowania i przeliczania reguł. Ta faza nie implementuje frontendu ani płatności.

Osiem symboli regularnych to L1–L4 i P1–P4; P4 jest najwyżej płatnym Husarzem. Historyczne P1=Pierogi,P2=Bocian,P3=Szabla znajdują się wyłącznie w mapie prezentacyjnej. Maluch, zamek, skrzydła i domek to nieprzypisane kandydatury grafik. Zmiana grafiki nie zmienia konfiguracji matematycznej.
