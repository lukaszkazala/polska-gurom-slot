# Zmiany matematyczne

**PROTOTYPE / NOT MATH-FROZEN**

## 17.10.2026 — 0.1.0-reconstruction

- Rozpoczęto z pustego katalogu, bez AGENTS.md i materiałów `sources/`. Nie było kodu ani oryginalnych pełnych pasków v0.1.
- Zachowano historyczne liczności, paytable, Scatter payout oraz25% Charge jako prototypowe parametry rekonstrukcji. Nie podjęto automatycznego tuningu.
- Jawnie wybrano nowe identyczne pogrupowane paski i20 konkretnych unikalnych linii. Nie twierdzimy, że odtwarzają historyczne hit frequency i wariancję.
- Rozdzielono grafikę od stabilnych10 ID i modelu matematycznego.
- Przyjęto roboczy evaluator sprawdzający wszystkie regularne interpretacje Wildów, w tym pięćWildów jakoP4. Rozdzielono tę regułę od tuningu parametrów i opisano różnicę SDK.
- Wprowadzono cykliczne okna, kontrolowaną arytmetykę całkowitą, FS bez retriggerów, nie-sticky Charge jednego z bębnów2/3/4 i Scattery z naturalnej planszy.
- Cap dotyczy pełnej rundy. Wszystkie przyznane FS rozgrywa się także po jego osiągnięciu. Rejestrowane są kwoty raw,paid,redukcja i osiągnięcie limitu.
- Przygotowano analitykę przed cap, deterministyczne testy, backend MC z kontrolą względem silnika skalarnego, dowód osiągalności/maksimum i raport wpływu cap.
- Zbadano aktualne oficjalne źródła Stake; nie uruchomiono SDK/RGS, optymalizacji wag ani publikacji. Stwierdzono rozbieżność kroku wypłat w walidatorze.

Kolejne strojenie wymaga odrębnego zlecenia; raport przedstawia wyłącznie propozycje. Math Freeze nie wykonano.
