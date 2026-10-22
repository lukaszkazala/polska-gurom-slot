# Sprawdzenie dashboardu POLSKA GUROM

Kontrola: 20.10.2026. Wynik kontroli struktury i danych: **17/17 PASS**. Osobny przegląd kompletności danych: **16/16 PASS**.

Dashboard obejmuje 139 niezmienionych plików źródłowych, 21 serii symulacji, 17 zestawów kontroli i 10 etapów historii. Wszystkie 125 pozycji inwentarza źródeł i 36 odsyłaczy historycznych mają kopie w bibliotece.

Wartości 160 mln końcowych losowań i 160 mln osobnych rund generatora są rozdzielone. Suma 107 bieżących kontroli regresji obejmuje dokładnie sześć zestawów, bez doliczania starszych testów i dodatkowych audytów.

W przeglądarce sprawdzono nawigację po sześciu widokach, zmianę modelu i serii wykresu RTP, szczegóły symulacji, filtry serii, kalkulator bonusu, wyszukiwanie testów, szczegóły awarii HTTP 408, archiwum, kategorie i wyszukiwanie raportów, podgląd Markdown, JSON i zdjęć oraz zamykanie szczegółów. Układy 1440 i 390 px nie powodują poziomego przepełnienia strony. Tabele na telefonie przewijają się we własnym obszarze. Konsola przeglądarki nie zgłosiła błędów.

Uzupełniono brakujący raport weryfikacji v0.2, poprawiono kategorie starych i kalibracyjnych wyników, dodano filtr archiwum oraz podsumowanie parametrów matematyki. Usunięto błąd ponownego otwierania okna raportu przy zamykaniu. Zasoby mają wersjonowane adresy, aby przeglądarka wczytała aktualne dane.

Nie wykonywano ponownie dużych symulacji na potrzeby dashboardu. Panel przedstawia zapisane wyniki i dowody. Brak wariantu 12 darmowych obrotów pozostaje jawnym błędem pokrycia zasad aktualnej gry. Poprawność dashboardu nie oznacza naprawienia tej kwestii ani zatwierdzenia przez Stake.

Wyniki maszynowe: `results.json` i `../dashboard_data_review.json`. Dowody wyglądu: `desktop.png`, `mobile.png`.
