# Naprawy po audycie POLSKA GUROM

**Data: 21.10.2026. Naprawiono dziewięć wskazanych usterek B01–B09 w lokalnym wariancie test-interface-any-start.** Matematyka pozostaje 0.5.0-any-start. Kopia stanu sprzed zmian znajduje się w before_fixes.zip. Oryginalny raport audytu zachowano jako zapis stanu przed naprawami.

## Wyniki weryfikacji

| Kontrola | Wynik |
|---|---:|
| Testy Python | 53/53 |
| Testy JavaScript | 81/81 |
| Łączna regresja i nowe testy | **134/134** |
| Wszystkie rundy przez nowy walidator UI | **100 049/100 049** |
| Widoki 320×568, 390×700, 600×400, 802×829, 1280×720 | **5/5** |
| Testy przenośnego ZIP | **27/27** |
| Zgodność ZIP ze źródłami | **TAK** |
| Zmiany w silniku, banku i wagach | **BRAK — skróty identyczne** |
| Dokładne RTP | **24/25 = 96%** |

Testy JS korzystają z rzeczywistych rund i konfiguracji wyeksportowanych z bieżącego silnika; wcześniejsze uproszczone dane zastąpiono poprawnymi pełnymi sekwencjami. Kontrole renderowania wykonano osobno w rzeczywistej przeglądarce. Próby awarii oczekują teraz braku dodatkowego obciążenia; nie zaliczają reprodukcji starego błędu jako poprawności.

## Naprawione problemy

### B01 — naprawione

Rozliczenie jest zatwierdzane po przygotowaniu pełnej odpowiedzi. Błąd serializacji lub częściowy błąd wpisu do pamięci cofa całą operację. Awaria wysyłania po zatwierdzeniu zachowuje wynik do ponowienia.

[Dowód](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/fixes_2026_10_21/test_atomicity.log)

### B02 — naprawione

Bieżący portfel pochodzi z lekkiego /api/wallet. Nie jest zastępowany historycznym saldem zapisanym w wyniku. Awaria jego odczytu zachowuje pierwotny identyfikator płatnej rundy.

[Dowód](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/fixes_2026_10_21/audit_fixes_frontend.json)

### B03 — naprawione

Stawka i identyfikator są zachowane do końca prezentacji. Zapisywany jest ukończony obrót bazowy i liczba w pełni pokazanych FS. Po odświeżeniu test z 12 FS wznawia od piątego po pokazaniu czterech; AUTO pozostaje zatrzymane.

[Dowód](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/fixes_2026_10_21/audit_fixes_frontend.json)

### B04 — naprawione

Panel ma jedną kolumnę i trzy wiersze; wielkość liczb mieści się również dla angielskiego 5,000×. Pomiary pięciu viewportów nie wykazały ucięcia kart ani wyjścia głównych przycisków poza ekran.

[Dowód](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/fixes_2026_10_21/browser_layout_results.json)

### B05 — naprawione

Walidacja sprawdza zakresy i unikalność usunięć, ruchy i grawitację, plansze, linie, mnożniki i sumy wraz z limitem. Uszkodzone odpowiedzi są odrzucane przed skasowaniem oczekującego ID. Wszystkie prawdziwe rekordy banku przechodzą nowy walidator.

[Dowód](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/fixes_2026_10_21/frontend_bank_validation.json)

### B06 — naprawione

Ładowanie ilustracji ma limit 15 sekund. Błąd lub zawieszenie przełącza na symbole zastępcze i pozostawia możliwość gry. Odświeżenie pozwala ponowić pobieranie.

[Dowód](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/fixes_2026_10_21/audit_fixes_frontend.json)

### B07 — naprawione

Zasady PL/EN/DE wyjaśniają zastępowanie wyłącznie zwykłych symboli, brak zastępowania Scattera, wypłaty samych Wildów jako P4 oraz wybór lewego początku przy remisie i wpływ na usuwane pola.

[Dowód](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/fixes_2026_10_21/audit_fixes_frontend.json)

### B08 — naprawione

README przepisano dla aktualnego wariantu: 100049 rund, właściwy kompilator, zgodne zasady, stawki i opis odzyskiwania. Dodano wymóg restartu starego serwera po aktualizacji.

[Dowód](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/fixes_2026_10_21/after_manifest.json)

### B09 — naprawione

Pakowanie dołącza START_UX.cmd i START.cmd. Finalny ZIP ma 30 plików, zgadza się bajtowo z aktualnymi źródłami i przechodzi 27 kontroli samodzielnego uruchomienia.

[Dowód](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/fixes_2026_10_21/portable/portable_check.json)

## Paczka i uruchomienie

[Poprawiony ZIP demo](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/test-interface-any-start/POLSKA_GUROM_TESTER.zip)

Wypakuj cały ZIP. Zakończ poprzedni proces serwera przez Ctrl+C, a następnie uruchom START_UX.cmd (port 8772) lub START.cmd (port 8765). Działająca wcześniej instancja Pythona nie wczytuje automatycznie zmienionego serwera. Podgląd z testów działa lokalnie na porcie 8798.

ZIP SHA256: `ca96e5ed37580b995a2664bc363cc65323b4ac4b2e9f295261db213bebd9b4b9`. Liczba plików: 30.

[Manifest po zmianach](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/fixes_2026_10_21/after_manifest.json) · [Weryfikacja wydania](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/fixes_2026_10_21/release_verification.json) · [Checklista po naprawach](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/fixes_2026_10_21/CHECKLISTA_PO_NAPRAWACH_PL.md)

## Zakres, który pozostaje do osobnej realizacji

Zmiany nie dodają produkcyjnego RGS, replay platformy, walut/social ani statusów ACP. Nie zmieniają też rozkładu wysokich wygranych: istniejące przerwy w wypłatach i maksimum osiągalne tylko w bazie pozostają cechami dotychczasowej matematyki. To odrębne elementy projektu i integracji; nie są przedstawiane jako naprawione lub zatwierdzone. Fizyczne urządzenia i rzeczywisty popout platformy wymagają końcowego odbioru.

## Poprawiony panel przy 802 px

![Czytelny panel bonusu](C:/Users/Kazaluka/.codex/.chatgpt-projects/g-p-6ad10d7dc94881919023097cba0cf4b4/audit/fixes_2026_10_21/panel_fixed_pl.png)

