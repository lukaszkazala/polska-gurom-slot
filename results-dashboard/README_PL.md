# POLSKA GUROM — dashboard wyników

Dashboard prezentuje zapisane wyniki badań i testów. Nie wykonuje nowych losowań i nie zmienia matematyki gry.

- 24 serie symulacji, w tym nowe 10, 50 i 100 mln końcowych losowań wersji 0.4.1 oraz osobne pełne symulacje generatora i archiwum 0.4.0.
- 135 unikalnych bieżących testów regresji, dodatkowe audyty i wcześniejsze kontrole.
- Dokładne RTP, częstość bonusów, maksymalna wygrana i parametry rozkładu.
- Historia 11 etapów oraz 166 niezmienionych plików źródłowych, w tym wszystkie 139 wcześniejszych dowodów.

Wersja internetowa jest prywatna. Możesz też pobrać pojedynczy plik `POLSKA_GUROM_DASHBOARD.html` i otworzyć go dwukrotnym kliknięciem, bez instalacji. Ma około 8 MB i zawiera wszystkie dane, wykresy oraz 166 plików źródłowych. Raporty są bezstratnie spakowane wewnątrz HTML; przeglądarka sama je rozpakowuje. Podgląd i pobieranie raportów działają bez internetu w aktualnej przeglądarce Chrome lub Edge. W paczce ZIP ten sam kompletny panel nazywa się `dashboard.html`. Folder `reports/` zawiera również osobne kopie źródeł.

Dane aktualnej matematyki `0.4.1-weighted-12fs` i ponownie wykonanych testów pochodzą z 20.10.2026. Starsze dane zachowano w archiwum wraz z ich wersjami. Wyniki generatora kandydatów opisują ten sam niezmieniony generator, a nie końcowy ważony rozkład gry.

Bonus 12 darmowych obrotów za 5 Scatterów jest naprawiony i sprawdzony: 24 legalne pełne rundy mają dodatnią łączną masę 4 018 776 / 10¹², średnio raz na około 248 832 płatne rundy. Zachowano dokładny RTP 96%, całkowitą częstość bonusów i maksymalną wygraną 5000× z częstością 1/8 mln. Zaliczone kontrole lokalne nie stanowią zatwierdzenia Stake ani potwierdzenia integracji z rzeczywistym portfelem.

Odświeżanie danych projektu: `python results-dashboard/build_data_v041.py`, a następnie `python results-dashboard/build_standalone.py`. Weryfikacja: `python audit/dashboard_qa/check_dashboard.py` i `python audit/dashboard_qa/check_standalone.py`. Paczka ZIP: `python audit/dashboard_qa/package_dashboard.py`. Kontrola struktury zapisuje nowy raport `audit/dashboard_qa/results_v041.json`, pozostawiając dawne `results.json` bez zmian. Skrypty dashboardu nie uruchamiają symulacji gry. Pliki w `sources/` pozostają materiałami tylko do odczytu.
