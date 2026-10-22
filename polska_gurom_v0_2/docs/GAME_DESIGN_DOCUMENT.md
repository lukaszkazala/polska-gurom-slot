# POLSKA GUROM — zasady v0.2

Wersja poprawionej matematyki z 18 października 2026 r. Cele: nominalne RTP 96%, alokacja około 73,5% gra podstawowa / 22,5% bonus, 25–30% rund z dodatnią wypłatą, bonus co 150–250 rund, projektowana średnio wysoka zmienność. Dane liczbowe znajdują się w PAR sheet i raporcie walidacji.

## Plansza i wygrane

- 5 bębnów, 3 rzędy, 20 zawsze aktywnych stałych linii.
- Linia wybiera po jednym polu z kolejnych bębnów. Może przechodzić między rzędami; wygrywają minimum 3 zgodne symbole kolejno od pierwszego bębna z lewej.
- Symbole zwykłe: L1–L4, P1 Pierogi, P2 Bocian, P3 Szabla, P4 Husarz. WILD zastępuje symbole zwykłe, nigdy SCATTER.
- Każda pełna linia jest inna. Linie mogą współdzielić początki i płatne pola; każda płaci oddzielnie. W ramach jednej linii płacona jest jedna, najlepsza interpretacja Wild. Same Wild są opłacane według najlepszej interpretacji zwykłego symbolu; nie ma osobnej nagrody Wild.
- To system stałych linii, nie 243 ways i nie zwykłe symbole płacące gdziekolwiek.
- Tabela jest wyrażona jako mnożnik całkowitej stawki za obrót, nie stawki na linię.

## Scattery i bonus HUSSAR CHARGE

- SCATTER płaci gdziekolwiek: 3 = 1×, 4 = 5×, 5 = 20× całkowitej stawki.
- W płatnym obrocie 3/4/5 Scatterów przyznaje 8/10/12 darmowych obrotów.
- Darmowe obroty używają tych samych bębnów i linii, ale wszystkie wypłaty liniowe są mnożone przez 4. Scatter nie otrzymuje mnożnika.
- Na każdy FS przypada szansa `216905037/1000000000` na rozwinięcie jednego całego bębna do Wild. Bęben jest wybierany równomiernie spośród 2, 3, 4. Nie wolno warunkować wyboru od wyniku planszy ani historii gracza.
- Scattery i ich wypłaty liczy się na oryginalnej planszy, przed rozwinięciem Wild. Dopiero linie ocenia się na planszy po rozwinięciu.
- Nie ma ponownych aktywacji ani dodatkowych FS w bonusie, jackpotów, zakładów gamble lub trwałego postępu.

## Limit i prezentacja

Łączna wypłata płatnego obrotu oraz przyznanych mu FS jest ograniczona do 5000× całkowitej stawki. Historia zachowuje wszystkie przyznane FS. Każdy ma osobno surowy wynik oraz rzeczywiście zaksięgowaną kwotę; po wykorzystaniu limitu dalsze kredyty wynoszą zero.

Frontend przedstawia wynik silnika, bez własnego losowania. Powinien pokazać wygrane ścieżki z identyfikatorem linii, kwotą oraz liczbą opłaconych symboli. Przy wypłacie za trzy symbole wyróżnia trzy płatne pola; dalsza część linii może być dyskretnym kontekstem. Dla Scatterów i rozwinięcia Wild należy zachować kolejność opisaną wyżej. Częściowy zwrot mniejszy od stawki należy odróżniać od zysku netto.

Przed integracją zależną od SDK należy zweryfikować aktualne Stake Engine SDK. Ta wersja nie zawiera frontendu ani funkcji gry na prawdziwe pieniądze.
