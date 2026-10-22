from pathlib import Path

root = Path(__file__).resolve().parent / 'dist'
p = root / 'index.html'
s = p.read_text(encoding='utf-8')
changes = {
    'content="#101722"': 'content="#f5f7fb"',
    'LABORATORIUM WYNIKÓW': 'WYNIKI GRY',
    'PRZESTRZEŃ ANALIZ': 'POLSKA GUROM',
    'Jeden widok.<br>Wszystkie dowody.': 'Wszystkie wyniki<br>w jednym miejscu.',
    '<span>Laboratorium</span>': '<span>Dashboard</span>',
    'POLSKA GUROM / CENTRUMUM ANALIZ': 'POLSKA GUROM',
    'POLSKA GUROM / CENTRUM ANALIZ': 'POLSKA GUROM',
    'Pełny obraz wyników.': 'Wyniki gry',
    'Matematyka, testy i zachowanie gry — zebrane w jednym miejscu.': 'RTP, bonusy i testy. Zobacz najważniejsze liczby lub przejdź do szczegółów.',
    'Wyniki dużych prób.': 'Symulacje',
    'Testy, które mają znaczenie.': 'Testy i awarie',
    'Jak rozwijała się gra.': 'Historia projektu',
    'Wszystkie raporty pod ręką.': 'Raporty źródłowe',
    'Poprawny format i zaliczone testy nie zastępują pełnego pokrycia zasad gry ani approval Stake.': 'Testy wykonano lokalnie. Zatwierdzenie przez Stake nie było wykonywane.',
    '<i>LAB</i>': '<i>WYNIKI</i>',
}
for before, after in changes.items():
    s = s.replace(before, after)
old = '<button class="button subtle export-data" aria-label="Pobierz dane JSON"><svg><use href="#i-download"/></svg><span>Pobierz dane</span></button>'
new = '<a class="button subtle" data-download-html href="dashboard.html" download="POLSKA_GUROM_DASHBOARD.html" aria-label="Pobierz cały dashboard HTML"><svg><use href="#i-download"/></svg><span>Pobierz HTML</span></a>'
s = s.replace(old, new)
p.write_text(s, encoding='utf-8')
p = root / 'app.js'
s = p.read_text(encoding='utf-8').replace('KONTROLE BIEŻĄCEJ WERSJI', 'TESTY REGRESJI')
s = s.replace('calibration: "Strojenie", historical:', 'calibration: "Strojenie", diagnostic: "Kontrola pomocnicza", historical:')
s = s.replace('href="${safeHref(report.href)}" download aria-label=', 'href="${safeHref(report.href)}" download="${esc(report.path.split("/").at(-1))}" aria-label=')
p.write_text(s, encoding='utf-8')
