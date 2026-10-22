"""Verify the delivered source/ZIP and summarize the nine repaired findings."""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import csv
import hashlib
import json
import re
import zipfile

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
APP=ROOT/'test-interface-any-start'
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def link(label,path):return f'[{label}]({path.as_posix()})'
before=read('before_manifest.json')
after={p.relative_to(APP).as_posix():sha(p) for p in APP.rglob('*')
       if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.zip')}
math_unchanged={name:after.get(name)==digest for name,digest in before.items() if name.startswith(('engine/','stake_math/'))}
total=weighted=0
with (APP/'stake_math/lookUpTable_base_0.csv').open() as f:
    for row in csv.reader(f):
        _,weight,payout=map(int,row);total+=weight;weighted+=weight*payout
rtp=Fraction(weighted,100*total)
archive=APP/'POLSKA_GUROM_TESTER.zip'
with zipfile.ZipFile(archive) as z:
    zip_matches=z.testzip() is None and all(z.read(name)==(APP/name).read_bytes() for name in z.namelist())
    start_ux='START_UX.cmd' in z.namelist()
    file_count=len(z.namelist())
regression=read('regression_summary.json')
bank=read('frontend_bank_validation.json')
layout=read('browser_layout_results.json')
portable=read('portable/portable_check.json')
python_count=0
for suite in ('test_server','test_cascades','test_network_faults','test_atomicity','test_bonus12_api'):
    log=(OUT/(suite+'.log')).read_text(encoding='utf-8')
    match=re.search(r'Ran (\d+) tests? in ',log)
    assert match,(suite,'no unittest completion evidence')
    python_count+=int(match[1])
js_count=sum(len(read(name)['checks']) for name in ('autoplay_logic_results.json','network_logic_results.json',
    'frontend_12fs_results.json','any_start_frontend.json','audit_fixes_frontend.json'))
assert regression['passed'] and len(regression['suites'])==10 and bank['passed'] and layout['passed']
assert all(math_unchanged.values()) and rtp==Fraction(24,25) and zip_matches and start_ux
assert portable['success'] and portable['zip_sha256']==sha(archive)
assert python_count+js_count==134
verification={
    'completed_date':'2026-10-21','math_version':'0.5.0-any-start','fixed_findings':[f'B{i:02}' for i in range(1,10)],
    'python_tests':python_count,'javascript_tests':js_count,'regression_total':python_count+js_count,
    'frontend_bank_validated':bank['books_checked'],'responsive_viewports_passed':len(layout['checks']),
    'portable_checks_passed':len(portable['checks']),'math_files_unchanged':math_unchanged,'rtp_exact':str(rtp),
    'zip_matches_sources':zip_matches,'zip_has_START_UX':start_ux,'zip_file_count':file_count,
    'zip_sha256':sha(archive),'changed_files':[name for name,digest in before.items() if after.get(name)!=digest],
    'added_files':[name for name in after if name not in before],
    'production_integration_completed':False,
}
(OUT/'after_manifest.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
(OUT/'release_verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')

old=ROOT/'audit/full_review_2026_10_20'
rows=json.loads((old/'CHECKLISTA_81.json').read_text(encoding='utf-8'))
updates={
 'G03':('TAK','B07 naprawione: aktywne zasady PL/EN/DE opisują lewy początek przy remisie; algorytm i wagi niezmienione.'),
 'G06':('TAK','B07 naprawione: wykluczenie Scattera, brak własnej tabeli Wilda i wypłaty samych Wildów są jawne.'),
 'G16':('TAK','B08 naprawione: jeden aktywny README v0.5, poprawne 100049 rund i kompilator aktualnego wariantu.'),
 'SE10':('TAK','Zakres lokalny: tabela, RTP i limit obecne; uzupełniono brakujące zasady Wildów i remisów. Nie jest to akceptacja platformy.'),
 'SE11':('TAK','B02 naprawione: wynik rundy jest historyczny, bieżący portfel pobierany osobno; sumy wygranych zachowane.'),
 'QA17':('NIEZWERYFIKOWANE','B03 lokalnie naprawione i sprawdzone: stawka oraz postęp FS zachowane; produkcyjne recovery RGS nadal niedostępne.'),
 'QA20':('TAK','Zakres lokalny: regresje współbieżności/idempotencji oraz nowe awarie zapisu i odzyskiwanie w dwóch kartach przechodzą.'),
 'QA21':('TAK','B05 naprawione: walidacja całych przejść i sum; odrzucenie uszkodzonej odpowiedzi zachowuje request ID. Awaria odczytu portfela również go zachowuje.'),
 'SE14':('NIEZWERYFIKOWANE','B04 naprawione, pięć viewportów bez uciętych kart i pozaekranowych kontrolek. Fizyczny dotyk i rzeczywisty popout platformy pozostają do sprawdzenia.'),
}
for row in rows:
    if row['id'] in updates:row['status'],row['evidence_or_reason']=updates[row['id']]
(OUT/'CHECKLISTA_PO_NAPRAWACH.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
checklist=['# Checklista po naprawach — 21.10.2026','','Dotyczy lokalnego demo 0.5.0-any-start. Tylko punkty objęte nowymi dowodami zmieniono względem audytu wejściowego. Pozostałe oceny zachowują pierwotny zakres i ograniczenia.','','| Punkt | Status | Uzasadnienie |','|---|---|---|']
checklist.extend(f"| {row['id']} | {row['status']} | {row['evidence_or_reason']} |" for row in rows)
(OUT/'CHECKLISTA_PO_NAPRAWACH_PL.md').write_text('\n'.join(checklist)+'\n',encoding='utf-8')

fixed=[
 ('B01','Rozliczenie jest zatwierdzane po przygotowaniu pełnej odpowiedzi. Błąd serializacji lub częściowy błąd wpisu do pamięci cofa całą operację. Awaria wysyłania po zatwierdzeniu zachowuje wynik do ponowienia.','test_atomicity.log'),
 ('B02','Bieżący portfel pochodzi z lekkiego /api/wallet. Nie jest zastępowany historycznym saldem zapisanym w wyniku. Awaria jego odczytu zachowuje pierwotny identyfikator płatnej rundy.','audit_fixes_frontend.json'),
 ('B03','Stawka i identyfikator są zachowane do końca prezentacji. Zapisywany jest ukończony obrót bazowy i liczba w pełni pokazanych FS. Po odświeżeniu test z 12 FS wznawia od piątego po pokazaniu czterech; AUTO pozostaje zatrzymane.','audit_fixes_frontend.json'),
 ('B04','Panel ma jedną kolumnę i trzy wiersze; wielkość liczb mieści się również dla angielskiego 5,000×. Pomiary pięciu viewportów nie wykazały ucięcia kart ani wyjścia głównych przycisków poza ekran.','browser_layout_results.json'),
 ('B05','Walidacja sprawdza zakresy i unikalność usunięć, ruchy i grawitację, plansze, linie, mnożniki i sumy wraz z limitem. Uszkodzone odpowiedzi są odrzucane przed skasowaniem oczekującego ID. Wszystkie prawdziwe rekordy banku przechodzą nowy walidator.','frontend_bank_validation.json'),
 ('B06','Ładowanie ilustracji ma limit 15 sekund. Błąd lub zawieszenie przełącza na symbole zastępcze i pozostawia możliwość gry. Odświeżenie pozwala ponowić pobieranie.','audit_fixes_frontend.json'),
 ('B07','Zasady PL/EN/DE wyjaśniają zastępowanie wyłącznie zwykłych symboli, brak zastępowania Scattera, wypłaty samych Wildów jako P4 oraz wybór lewego początku przy remisie i wpływ na usuwane pola.','audit_fixes_frontend.json'),
 ('B08','README przepisano dla aktualnego wariantu: 100049 rund, właściwy kompilator, zgodne zasady, stawki i opis odzyskiwania. Dodano wymóg restartu starego serwera po aktualizacji.','after_manifest.json'),
 ('B09','Pakowanie dołącza START_UX.cmd i START.cmd. Finalny ZIP ma 30 plików, zgadza się bajtowo z aktualnymi źródłami i przechodzi 27 kontroli samodzielnego uruchomienia.','portable/portable_check.json'),
]
doc=['# Naprawy po audycie POLSKA GUROM','','**Data: 21.10.2026. Naprawiono dziewięć wskazanych usterek B01–B09 w lokalnym wariancie test-interface-any-start.** Matematyka pozostaje 0.5.0-any-start. Kopia stanu sprzed zmian znajduje się w before_fixes.zip. Oryginalny raport audytu zachowano jako zapis stanu przed naprawami.','',
     '## Wyniki weryfikacji','','| Kontrola | Wynik |','|---|---:|',
     f'| Testy Python | {python_count}/{python_count} |',f'| Testy JavaScript | {js_count}/{js_count} |',
     '| Łączna regresja i nowe testy | **134/134** |','| Wszystkie rundy przez nowy walidator UI | **100 049/100 049** |',
     '| Widoki 320×568, 390×700, 600×400, 802×829, 1280×720 | **5/5** |','| Testy przenośnego ZIP | **27/27** |',
     '| Zgodność ZIP ze źródłami | **TAK** |','| Zmiany w silniku, banku i wagach | **BRAK — skróty identyczne** |','| Dokładne RTP | **24/25 = 96%** |','',
     'Testy JS korzystają z rzeczywistych rund i konfiguracji wyeksportowanych z bieżącego silnika; wcześniejsze uproszczone dane zastąpiono poprawnymi pełnymi sekwencjami. Kontrole renderowania wykonano osobno w rzeczywistej przeglądarce. Próby awarii oczekują teraz braku dodatkowego obciążenia; nie zaliczają reprodukcji starego błędu jako poprawności.','',
     '## Naprawione problemy','']
for key,description,proof in fixed:
    doc.extend([f'### {key} — naprawione','',description,'',link('Dowód',OUT/proof),''])
doc+=['## Paczka i uruchomienie','',link('Poprawiony ZIP demo',archive),'',
      'Wypakuj cały ZIP. Zakończ poprzedni proces serwera przez Ctrl+C, a następnie uruchom START_UX.cmd (port 8772) lub START.cmd (port 8765). Działająca wcześniej instancja Pythona nie wczytuje automatycznie zmienionego serwera. Podgląd z testów działa lokalnie na porcie 8798.','',
      f'ZIP SHA256: `{sha(archive)}`. Liczba plików: {file_count}.','',
      link('Manifest po zmianach',OUT/'after_manifest.json')+' · '+link('Weryfikacja wydania',OUT/'release_verification.json')+' · '+link('Checklista po naprawach',OUT/'CHECKLISTA_PO_NAPRAWACH_PL.md'),'',
      '## Zakres, który pozostaje do osobnej realizacji','',
      'Zmiany nie dodają produkcyjnego RGS, replay platformy, walut/social ani statusów ACP. Nie zmieniają też rozkładu wysokich wygranych: istniejące przerwy w wypłatach i maksimum osiągalne tylko w bazie pozostają cechami dotychczasowej matematyki. To odrębne elementy projektu i integracji; nie są przedstawiane jako naprawione lub zatwierdzone. Fizyczne urządzenia i rzeczywisty popout platformy wymagają końcowego odbioru.','',
      '## Poprawiony panel przy 802 px','',f"![Czytelny panel bonusu]({(OUT/'panel_fixed_pl.png').as_posix()})",'']
(OUT/'RAPORT_NAPRAW_PL.md').write_text('\n'.join(doc)+'\n',encoding='utf-8')
verification['checklist_statuses']=dict(Counter(row['status'] for row in rows))
(OUT/'FINAL_STATUS.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
print(json.dumps({key:verification[key] for key in ('fixed_findings','regression_total','frontend_bank_validated','portable_checks_passed','zip_sha256','rtp_exact')},indent=2))
