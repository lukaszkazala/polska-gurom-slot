# Komunikaty limitu 5000× — 22.10.2026

Zaktualizowano aktywną wersję `test-interface-any-start` oraz trzy paczki: tester lokalny, RGS_TEST i RGS_FRONTEND.

## Zachowanie

- Komunikat podaje faktycznie przyznaną wypłatę rundy w jej walucie. Korzysta z kwoty wyniku, także podczas replay z historyczną stawką.
- Osiągnięcie dokładnie 5000× bez redukcji uruchamia ten sam komunikat limitu.
- Zakończenie bonusu wyjaśnia osiągnięcie limitu całej rundy. Przy niewykorzystanych obrotach podaje ich liczbę i informuje, że nie zostaną rozegrane.
- Licznik zachowuje oryginalnie przyznaną liczbę obrotów: np. 2/8 zamiast 2/2. Limit w bazie może pokazać 0/8; limit na ostatnim obrocie pokazuje 8/8 bez informacji o niewykorzystanych obrotach.
- Wejście do bonusu i wznowienie pokazują pierwotny przydział. Tryb błyskawiczny i pomijanie ekranów zachowują trwałe wyjaśnienie końcowe.
- Szczegóły ograniczonej wygranej odróżniają kwotę linii przed limitem od wypłaty przyznanej dla całego etapu. Nie przypisują arbitralnie redukcji poszczególnym liniom. Kliknięcie linii nie usuwa trwałej notatki o limicie.
- Zmiany obejmują PL, EN i DE oraz zasady gry. Matematyka i kontrakt rozliczeń pozostają w wersji 0.5.0-any-start.

## Weryfikacja

**275/275 sprawdzeń logiki zaliczonych**, w tym 47 nowych przypadków limitu, 28 wcześniejszych napraw interfejsu, 60 RGS, 33 odzyskiwania RGS, 34 replay, 53 walut, 13 AUTO i 7 prezentacji pełnego bonusu 12 FS.

Nowe testy używają rzeczywistego wyniku maksimum z banku oraz syntetycznych przypadków granicznych wygenerowanych przez bieżący silnik. Bonus przerwany limitem jest przypadkiem syntetycznym; test nie twierdzi, że występuje w opublikowanym banku. Test wznowienia po pierwszym FS potwierdza licznik 1/8 → 2/8, jeden zakład, jedno obciążenie i jedno rozliczenie.

Wszystkie trzy archiwa są poprawne i zawierają aktualny komplet plików interfejsu. Szczegóły, wyniki testów i skróty paczek: `delivery_verification.json` oraz pliki wynikowe obok raportu. Powtarzalna kontrola paczek: `python audit/cap_messages_2026_10_22/verify_delivery.py` z katalogu projektu.

Testy korzystają z minimalnego DOM i wirtualnego czasu. Próba kontroli wizualnej w przeglądarce aplikacji nie doszła do skutku: połączenie z lokalnym serwerem zakończyło się `ERR_CONNECTION_TIMED_OUT`. Nie wykonano odbioru wizualnego ani testu na rzeczywistym środowisku platformy.
