# Sprawdzenie dashboardu po naprawie 12 darmowych obrotów

Kontrola automatyczna: 20.10.2026. Wersja matematyki: **0.4.1-weighted-12fs**.

Dashboard obejmuje 166 plików źródłowych, 24 serie symulacji i 11 etapów historii. Wszystkie 139 wcześniejszych dowodów zachowano osobno, zgodnie z oryginalnymi sumami kontrolnymi. Dawne trzy serie ważone 10/50/100 mln są archiwalne; widok domyślny pokazuje nowe trzy serie wersji 0.4.1. Oddzielnie pozostają 160 mln pełnych rund niezmienionego generatora kandydatów.

Aktualna suma regresji wynosi **135/135** w dziewięciu zestawach: 107 ponownie wykonanych wcześniejszych przypadków i 28 nowych kontroli bonusu 12FS. SDK oraz niezależny audyt całego banku nie są drugi raz wliczane do tej liczby.

Bonus 12FS ma 24 legalne pełne wyniki i dodatnią masę 4 018 776 / 10¹². Otwarty błąd pokrycia został usunięty; dokładny RTP pozostaje 96%. W nowych losowaniach 10/50/100 mln odnotowano odpowiednio 53, 230 i 374 trafienia wariantu 12FS.

Skrypt `check_dashboard.py` wykonuje 19 kontroli struktury i spójności: liczby wyników, rozdzielenie modeli, sumy testów, pokrycie 12FS, unikalność identyfikatorów, zgodność osadzonych danych, odnośniki historii oraz identyczność kopii z bieżącymi lub zachowanymi oryginałami. Wynik znajduje się w `results_v041.json`. Dawny `results.json` pozostaje bez zmian.

Osobna kontrola samodzielnego HTML sprawdza osadzone dane i każdy surowy plik po bezstratnym rozpakowaniu gzip. Plik HTML ma około 8 MB, zawiera komplet źródeł i działa bez instalacji. ZIP obejmuje wyłącznie aktywne 166 pozycji rejestru, potrzebne zasoby strony, pojedynczy HTML, instrukcję i bieżące raporty QA. Sprawdzane są integralność ZIP, skład oraz wszystkie bajty każdego pliku.

Ta kontrola nie wykonuje testów przeglądarkowych i nie przypisuje dawnych sprawdzeń wizualnych nowej wersji. Nie uruchamia również nowych symulacji gry. Lokalne zaliczenie testów nie stanowi zatwierdzenia Stake ani potwierdzenia integracji z rzeczywistym portfelem.
