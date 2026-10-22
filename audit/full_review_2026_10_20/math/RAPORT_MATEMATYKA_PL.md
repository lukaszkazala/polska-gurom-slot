# Audyt matematyki POLSKA GUROM v0.5.0-any-start

Audyt wykonano 20.10.2026; przegląd dowodów i zgodności skrótów bieżących plików ukończono 21.10.2026. **Nie wykryto błędu rachunkowego wypłat, kaskad ani rozliczania limitu w żadnej ze 100 049 opublikowanych rund. Dokładne RTP finalnych wag wynosi 96%.** Są natomiast istotne ograniczenia rozkładu i luka w opisaniu remisów. Wynik dotyczy lokalnego banku; nie potwierdza integracji RGS ani zatwierdzenia platformy.

## Co rzeczywiście sprawdzono

- Wszystkie **100 000 możliwych ciągów pięciu symboli**: 0 rozbieżności, w tym 50 ciągów z jednakowo płatnymi różnymi przedziałami.
- Wszystkie **100 049 pełnych rekordów**, 212 009 ocen planszy, 367 959 wypłat linii, 107 598 przejść kaskad, 4362 darmowe obroty i 1103 ekspansje: wypłaty z plansz, właściwe pola usuwane tylko raz, grawitacja, uzupełnienia bez Scattera, Scatter przed ekspansją, mnożnik ×4 wyłącznie linii, brak retriggerów oraz limit całej rundy. Żaden opublikowany wynik nie kończy się awaryjnym limitem kaskad.
- Zgodność CSV, skompresowanych książek i odtworzenia z aktualnego silnika; unikalność wszystkich sekwencji; dodatnie całkowite wagi, kompletne ID i skróty plików.
- **200 098 testów granic selektora**: pierwszy i ostatni los każdego przedziału wag trafia do właściwej rundy.

Niezależny kalkulator enumeruje sześć możliwych przedziałów długości 3–5 i sprawdza zbiór symboli po wyłączeniu Wildów. Nie wywołuje produkcyjnej funkcji naliczania wypłat. Tabela wypłat i linie są osobno zapisanym kontraktem, porównanym z konfiguracją. Przy rosnących wypłatach dłuższy pasujący przedział pokonuje swoje krótsze fragmenty. Sprawdzenie osiągalności początkowych okien korzysta z skonfigurowanych taśm; nie dowodzi równomiernego losowania taśm w finalnym modelu — rozkładem końcowym są wagi książek.

Dowody: [pełny wynik audytu](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/math/independent_full_bank_results.json), [niezależny kalkulator](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/math/independent_full_bank.py:66), [ponowna kontrola dowodów i skrótów](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/math/evidence_review.json).

## Parametry finalnych wag

| Miara | Wynik |
|---|---:|
| RTP | **24/25 = 96%** |
| RTP bazy / bonusu | 45,60774144% / 50,39225856% |
| RTP linii bazy / Scattera bazy | 44,98836194% / 0,61937950% |
| RTP linii bonusu / Scattera bonusu | 50,37346326% / 0,01879530% |
| Brak wypłaty | 84,37730808% |
| Dowolna dodatnia wypłata | 15,62269192% |
| Częściowy zwrot: 0 < wypłata < stawka | 5,20297326% |
| Zwrot równy stawce | 0,61331858% |
| Wypłata większa od stawki | **9,80640007%** |
| Bonus dowolnego rodzaju | 0,496993554%, około 1:201,21 |
| Maksimum 5000× | dokładnie **1:8 000 000** |
| Wariancja / odchylenie standardowe wypłaty | 99,023619919066 / 9,95106124587× stawka |
| Różne kwoty wypłaty | 818, łącznie z zerem |
| Największa szansa pojedynczej książki | 0,0022017407% |

100 049 książek ma dodatnie wagi; 61 726 ma dodatnią wypłatę. Udział takich książek, 61,70%, nie jest hit rate: po uwzględnieniu wag dodatnia wypłata występuje w 15,62% rund.

| Bonus | Liczba książek | Częstość na płatną rundę | Średnia wypłata samego bonusu | Najwyższa cała runda z tym bonusem |
|---|---:|---:|---:|---:|
| 8 FS | 473 | 0,4679041094%, 1:213,72 | 100,2863× | 528,8× |
| 10 FS | 29 | 0,028687567%, 1:3485,83 | 119,0897× | 237× |
| 12 FS | 24 | 0,0004018776%, 1:248831,98 | 128,1833× | 328,9× |

Każdy deklarowany bonus jest osiągalny. Średnia wypłata samego bonusu, warunkowo po jego uruchomieniu, wynosi 101,3942×. Ekspansja następuje w **25,4511% wykonanych darmowych obrotów**. Wśród ekspansji bębny 2/3/4 mają odpowiednio 32,5964% / 31,9140% / 35,4896%. Wariant 12 FS ma ekspansję w 22,9167% obrotów. To parametry finalnego banku; 25% i równomierny wybór bębna w konfiguracji opisują generator kandydatów. Przedstawienie ich jako dokładnych częstości finalnej gry byłoby błędem opisu.

## Co jest problemem, a co decyzją modelu

**Luka specyfikacji: remisy wpływają na dalszą kaskadę.** Silnik wybiera najbardziej lewy początek przy równej kwocie. Przykład `L1 L1 WILD WILD P2`: cztery L1 na bębnach 1–4 i trzy P2 na 3–5 płacą po 0,6×, lecz wybierany jest pierwszy przedział. Usuwane pola są różne, więc reguła wpływa także na następną planszę. Kod jest deterministyczny i zgodny z własnym komentarzem; zasada powinna zostać jawnie dopisana do reguł gry. [Implementacja rozstrzygnięcia](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface-any-start/engine/polska_gurom/game.py:181).

**Ograniczenie banku: bardzo duże przerwy między możliwymi wypłatami.** Nie ma żadnej wypłaty wewnątrz przedziałów 528,8–990,9×, 995,3–1986,9×, 2018,4–2968,3×, 3010,9–4027,4× i 4029,6–5000×. Wynika to z dobrania zaledwie czterech rzadkich wyników w każdej grupie przez kompilator. To nie jest błąd sumowania; jest to ubogi rozkład wysokich wygranych, wymagający świadomej decyzji projektu. Nie należy zaliczać punktu „brak nieuzasadnionych luk” bez takiego uzasadnienia. [Dobór grup](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface-any-start/build_math.py:93), [pełny rozkład](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/math/payout_distribution.csv).

**Ograniczenie pokrycia: maksimum jest osiągalne wyłącznie w bazie.** Wszystkie cztery książki 5000× mają ID 100020–100023 i nie zawierają bonusu. Żadna opublikowana runda z bonusem nie przekracza 528,8×. Limit podczas bonusu jest poprawnie obsługiwany w testach wymuszonych, lecz ma zerowe prawdopodobieństwo w banku. Nie można dostarczyć rzeczywistego ID replay „cap w bonusie”. Nie narusza to samej deklaracji globalnego limitu 5000×; naruszałoby obietnicę, że taki wynik można trafić w bonusie.

**Koncentracja jest mierzalna, ale nie dowodzi błędu.** Wyniki co najmniej 100× występują w 0,219563% rund i odpowiadają za 37,0812% całego RTP. 100 książek o największym wkładzie odpowiada za 20,7411% RTP. Samo maksimum daje 0,0625 punktu procentowego RTP, czyli 0,0651% całego zwrotu. Zmienność wynika głównie z bonusów i rzadszych większych wypłat, nie tylko z maksimum.

## Symulacje i przykłady

100 000 rund uruchomionych przez faktyczny selektor dało RTP 92,9898%; milion losów z finalnych wag dał 95,74338%. Oba wyniki są zgodne ze zmiennością tego modelu. Przy dokładnej wariancji błąd standardowy RTP wynosi odpowiednio 3,1468 i 0,9951 punktu procentowego. Przedziały normalne są przybliżeniem dla rozkładu z rzadkimi wysokimi wygranymi; nie zastępują dokładnego wyliczenia z wag. Brak maksimum w milionie rund ma prawdopodobieństwo **88,2497%**, więc nie świadczy o jego niedostępności. Dowód dostępności stanowią książki i dodatnie wagi.

[Symulacja faktycznego selektora 100 tys. rund](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/release/weighted_simulation_100k.json). Milion losowań i szczegóły niepewności są w pełnym wyniku oraz dodatkowej kontroli dowodów.

Gotowe są [10 przykładów do inspekcji](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/math/DZIESIEC_PRZYKLADOW.md), obejmujące środkowy/prawy początek, bonusy 8/10/12 i maksimum, oraz [testy wymuszonych granic i dodatkowych 10 tys. rund](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/full_review_2026_10_20/math/forced_and_sample_cascade_checks.json). W tej drugiej próbie RTP 220,539% dotyczy **generatora kandydatów przed ważeniem** i nie jest RTP gry. Przykłady są automatycznie wyeksportowane i sprawdzone; nie są deklaracją testów manualnych ani testów ACP.
