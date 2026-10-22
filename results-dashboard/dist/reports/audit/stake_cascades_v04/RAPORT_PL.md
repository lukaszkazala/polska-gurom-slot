# POLSKA GUROM v0.4 — matematyka i testy

19 października 2026. Wynik kontroli lokalnych: **PASS**.

Gra losowa ma dokładne **96% RTP** z wag pełnych rund. Limit całej rundy wynosi **5000×**; jego częstość wynosi **1:8 000 000**. Kaskady uruchamiają się automatycznie.

## Model końcowy

- Jeden tryb `base`  koszt 1× stawki; 100 024 różnych pełnych rund  wszystkie z dodatnimi wagami.
- Jedna runda zawiera płatny obrót, wszystkie kaskady i cały bonus. Rozliczenie następuje raz.
- Suma wag: 1 000 000 000 000. Suma waga × wypłata: 96 000 000 000 000 jednostek (skala 100).
- RTP = 96 000 000 000 000 / (100 × 1 000 000 000 000) = 24/25 = **96%**, bez zaokrąglania wyniku.
- Wypłaty liniowe są w kroku 0,1×. Nie stosuje się osobnego zaokrąglenia tylko na potrzeby eksportu.
- Dowolna dodatnia wypłata: **29.448973%** rund; wypłata wyższa od stawki: **16.888488%**.
- Bonus: **0.496994%** rund. Odchylenie standardowe wypłaty rundy: **6.978496×**.
- 550 różnych wartości wypłaty. Największa szansa pojedynczego book: 0.001004%.
- 100 000 wyników pochodzi z generatora kandydatów. 24 dodatkowe wyniki zapewniają osiągalne duże wygrane, w tym cztery różne wyniki 5000×. Każdy powstał przez rzeczywiste ocenianie linii i uzupełnienia dopuszczone przez paski symboli; żadna wypłata nie została dopisana ręcznie.
- Wagi są stałe i niezależne od gracza, salda, stawki, historii oraz ustawień animacji. Lokalna gra używa tej samej tabeli wag co eksport RGS.

## Testy 10, 50 i 100 mln — końcowy rozkład RGS

Każda płatna runda to jeden faktyczny losowy całkowity bilet i wyszukanie wyniku w końcowej tabeli wag. Nie zastąpiono losowań wzorem ani rozkładem wielomianowym. To test wyboru gotowych pełnych rund; mechanika i wszystkie zapisane zdarzenia są sprawdzone osobno poniżej.

| Rundy | Seed | Zmierzony RTP | 95% przedział normalny | Trafienia 5000× |
|---:|---:|---:|---:|---:|
| 10 000 000 | 2026101901 | 95.7149450% | 95.28242–96.14747% | 0 |
| 50 000 000 | 2026101902 | 95.9247888% | 95.73136–96.11822% | 4 |
| 100 000 000 | 2026101903 | 96.0205807% | 95.88380–96.15736% | 12 |

Łącznie **160 mln niezależnych losowań** w trzech seriach z różnymi seedami. Wszystkie trzy wyniki mieszczą się w normalnym paśmie 95% względem dokładnego RTP. Przedziały opisują błąd Monte Carlo, nie certyfikację. Zero trafień maksimum w serii 10 mln jest możliwe; oczekiwana liczba to 1,25. Nie dobierano ponownie seedów po obejrzeniu wyników.

## Niezależna kontrola mechaniki i wcześniejsze regresje

- **100024 / 100024** books: niezależne wyliczenie każdej wygranej liniowej, usunięć, ruchu w dół, uzupełnienia oraz rozliczenia limitu.
- Pełne zdarzenia każdego book zgadzają się z lokalnym odtworzeniem. Sprawdzono także wszystkie cztery wyniki maksimum, bonusy i rozwinięcia WILD.
- 10 testów mechaniki kaskad — PASS. 10 testów HTTP i salda — PASS (w tym ponowienia tej samej rundy, konflikty ID, równoczesne ponowienia i limit 5000×).
- 13 deterministycznych testów autospinu — PASS: 100 obrotów we wszystkich prędkościach, ukrycie przy 80/81, błąd i ponowienie 81. rundy, zatrzymanie, brak salda.
- Rzeczywista przeglądarka: **100/100** losowych płatnych rund z animacjami turbo, poprawne zakończenie, brak błędów konsoli; następnie przywrócono normalną animację.
- Paczka ZIP po wypakowaniu: **27 kontroli PASS**, w tym zgodność plików silnika, faktycznie uruchomiony serwer i kompletne rozliczenie serializowanych kaskad.
- Oryginalne 30 plików modelu v0.2 pozostało bez zmian (kontrola sum SHA-256).

## Dodatkowe pełne symulacje generatora kandydatów

Niezależna kompilowana implementacja generowała plansze, oceniała wszystkie linie i wykonywała opadanie oraz bonusy od początku. Jej przebieg porównano dokładnie z Pythonem dla 10 000 rund ze wspólnym strumieniem SplitMix64. Te serie badają generator kandydatów, **nie końcowy rozkład ważonych books**.

| Rundy | Seed | Zwrot generatora | Techniczny limit kaskad osiągnięty |
|---:|---:|---:|---:|
| 10 000 000 | 2026101911 | 96.3363530% | 0 |
| 50 000 000 | 2026101922 | 96.1687414% | 0 |
| 100 000 000 | 2026101933 | 96.1089010% | 0 |

## Stake SDK i zakres zgodności

Lokalnie wykonano niezmienione publiczne funkcje SDK: `verify_lookup_format`, `verify_books_and_payout_mults`, `compare_payout_values`, `get_lut_statistics`. Wszystkie zakończyły się poprawnie; brak ostrzeżeń walidatora. Dodatkowo sprawdzono dokładne liczby całkowite, zgodność ID z numerem linii, 100 024 różne sekwencje zdarzeń, dodatnie wagi, krok wypłat i granice uint64.
Użyto oficjalnego Math SDK z commita `a6dccd86de740cc5d318079483cb6204cc5c19bc`; pobrane źródła mają zapisane i sprawdzone sumy SHA-256.
**Nie wykonano zatwierdzenia przez platformę ani publikacji.** Integracja rzeczywistego portfela RGS, uwierzytelnienia, replay i końcowy proces approval pozostają osobnym etapem. Parametr 25% rozwinięcia dotyczy generatora; końcowe częstości wynikają z wag.

Źródła: [Math Requirements](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/math-requirements/%2Bpage.svx), [How RGS Works](https://github.com/engineio/docs/blob/main/src/routes/docs/architecture/how-rgs-works/%2Bpage.svx), [publiczny walidator SDK](https://github.com/engineio/math-sdk/blob/a6dccd86de740cc5d318079483cb6204cc5c19bc/utils/rgs_verification.py).

## Pliki i odtworzenie kontroli

- [Gra — kompletna paczka ZIP](<C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/POLSKA_GUROM_v0_4_RTP96.zip>)
- [Same trzy pliki publikacji matematyki Stake](<C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/POLSKA_GUROM_STAKE_MATH_v0_4.zip>)
- [Dokładne parametry matematyki](<C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/stake_math/mathematics.json>)
- [Surowe wyniki 10/50/100 mln, przedziały i histogramy](<C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/stake_cascades_v04/fast_sim/weighted_results/weighted_simulation_report.json>)
- [Raport publicznego SDK](<C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/stake_cascades_v04/official_validation/official_validation_report.json>)
- [Niezależny audyt wszystkich books](<C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/stake_cascades_v04/book_mechanics_report.json>)
- [Wyniki autospinu](<C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/qa/autoplay_logic_results.json>)
- [Kontrole paczki](<C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface/qa/portable_check.json>)
- [Zbiorczy raport JSON](<C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/stake_cascades_v04/final_results.json>)

Z katalogu projektu: `python audit/stake_cascades_v04/build_math.py`, potem `python audit/stake_cascades_v04/verify_book_mechanics.py`, `python audit/stake_cascades_v04/official_validation/run_official_validation.py` i `python audit/stake_cascades_v04/fast_sim/weighted_book_tests.py`. Skrypty wykorzystują zapisane seedy. Duże losowania wymagają NumPy/SciPy; kompresja i publiczny walidator wymagają zstandard. Uruchomienie samej gry korzysta ze standardowej biblioteki Pythona.
