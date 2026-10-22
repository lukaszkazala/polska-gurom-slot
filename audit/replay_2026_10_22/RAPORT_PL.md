# Replay — 22.10.2026

Dodano replay w aktywnej wersji `test-interface-any-start`.

- Przycisk pod bębnami odtwarza wybraną zapisaną rundę. Starsze rundy: Ustawienia → Historia rund → dane wybranej rundy → Odtwórz rundę.
- Odtwarzane są oryginalne plansze, kaskady, rozszerzenia WILD, wykonane darmowe obroty i wypłaty po ograniczeniu do 5000×. Replay zaczyna prezentację od początku.
- Replay nie tworzy zakładu, nie zapisuje checkpointów `/bet/event`, nie wywołuje zakończenia rundy i nie zmienia salda, statystyk, kolejności historii ani zapisanej stawki.
- Podczas replay blokowane są nowe zakłady i AUTO. Replay nie startuje podczas nierozliczonej rundy, aktywnego AUTO ani odczytu portfela.
- Historia zakończonych rund RGS jest zachowana w tej samej karcie przez sessionStorage, do 100 wyników, jeśli pamięć przeglądarki jest dostępna. Zapis nie zawiera tokenu uruchomienia. Pełna zapisana runda może być odtwarzana bez sieci.
- Publiczny link `replay=true` pobiera zapis przez GET `/bet/replay/{game}/{version}/{mode}/{event}` bez sesji portfela. Przycisk Odtwórz rundę rozpoczyna animację, a Odtwórz ponownie uruchamia ją ponownie. Widoczne są oryginalna stawka, koszt i wynik. Błędny zapis blokuje odtwarzanie bez przejścia do nowej gry.

## Weryfikacja

- `qa/test_replay.cjs`: 34/34. Lokalne i RGS rundy przegrane, zwykłe wygrane, bonusy 8 i 12 obrotów, limit 5000×, wielokrotne odtwarzanie, offline, odzysk historii po odświeżeniu, niezmienność portfela i pamięci oraz błędne dane.
- `qa/test_rgs.cjs`: 60/60.
- `qa/test_rgs_recovery.cjs`: 33/33.
- Dodatkowo wykonano regresję AUTO: wszystkie 13 scenariuszy przeszły.
- Rzeczywista przeglądarka: replay bonusu zakończył 12/12 obrotów, pokazał 24 kaskady, końcowe 79,95 USD i przycisk Odtwórz ponownie. Zrzut: `replay-bonus12.jpg`.
- Odczyt symulatora po uruchomieniu replay: 0 zakładów, 0 rozliczeń, saldo 100 000 000 mikrojednostek. Wykonano jedynie publiczny GET replay. Dowód: `browser_wallet_check.json`.
- Trzy paczki ZIP przebudowano, sprawdzono ich integralność oraz zgodność plików z aktualnym kodem. Manifest: `packages.json`.

Nie zmieniano silnika ani banku matematyki. Starszy wariant `test-interface` i referencje `sources/` pozostają poza tą zmianą.

Sprawdzenie wykonano lokalnie i z lokalnym symulatorem. Prawdziwy endpoint replay Stake oraz odbiór platformy wymagają dostępu do jej środowiska. Implementacja wspiera bieżący format jednego zdarzenia `roundResult` i tryb `base` z kosztem ×1.

Kontrakt: [oficjalne wymagania replay Stake Engine](https://stake-engine.com/docs/approval-guidelines/game-replay-requirements), odczyt 22.10.2026.
