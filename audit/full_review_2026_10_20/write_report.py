"""Assemble verified audit evidence without changing the application."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
APP = ROOT / 'test-interface-any-start'

def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))

def link(label, path, line=None):
    target = (ROOT / path).as_posix()
    if line:
        target += ':' + str(line)
    return f'[{label}]({target})'

def evidence(label, path):
    return link(label, OUT.relative_to(ROOT) / path)

def readable(text):
    # Leave paths, links and code spans exact while improving prose spacing.
    chunks = re.split(r'(\[[^\]]*\]\([^\n)]*\)|`[^`]*`)', text)
    fixes = {'ponownie21':'ponownie 21','dla100049':'dla 100 049','kombinacji10':'kombinacji 10',
             'na5':'na 5','i5 prób':'i 5 prób','oraz10000':'oraz 10 000','oraz1000000':'oraz 1 000 000',
             'skali100':'skali 100','wynosi45':'wynosi 45','bonusu50':'bonusu 50','Scatterów0':'Scatterów 0',
             'i0,018':'i 0,018','daje96':'daje 96','to101':'to 101','zawiera61':'zawiera 61',
             'czyli61':'czyli 61','w15':'w 15','próbka100000':'próbka 100 000','zwrot223':'zwrot 223',
             'modelu96':'modelu 96','wag.25':'wag. 25','daje25':'daje 25','bębnów2':'bębnów 2',
             'udziały32':'udziały 32','Wyniki≥':'Wyniki ≥','w0,219':'w 0,219','dostarczają37':'dostarczają 37',
             'dostarczają58':'dostarczają 58','od96':'od 96','dostarcza0':'dostarcza 0','czyli0':'czyli 0',
             'dało92':'dało 92','dał95':'dał 95','około0':'około 0','około88':'około 88',
             'Maksimum5000':'Maksimum 5000','maksimum1':'maksimum 1','ponad2':'ponad 2',
             'przy802':'przy 802','również320':'również 320','dodatkowo320':'dodatkowo 320',
             'scenariusz0':'scenariusz 0','przy2PLN':'przy 2 PLN','bonusów8':'bonusów 8',
             'brakującego12':'brakującego 12','punktów81':'punktów 81','checklista81':'checklista 81',
             'Status81':'Status 81','weryfikacji81':'weryfikacji 81','dnia21':'dnia 21',
             '5FS':'5 FS','8FS':'8 FS','10FS':'10 FS','12FS':'12 FS',
             '600×400,802':'600×400, 802','3/4/5':'3 / 4 / 5','P1 oznacza ryzyko błędnego rozliczenia przy opisanej awarii;':'',
             'na przykład802':'na przykład 802','banku12':'banku 12','banku5000':'banku 5000',
             'tylko4':'tylko 4','maksimum4':'maksimum 4','ma24':'ma 24','z8':'z 8','z10':'z 10','z12':'z 12',
             'obroty20':'obroty 20','w0,5':'w 0,5'}
    for i in range(0, len(chunks), 2):
        part = chunks[i]
        for a,b in sorted(fixes.items(),key=lambda item:len(item[0]),reverse=True): part=part.replace(a,b)
        part=re.sub(r',(?=[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż])', ', ',part)
        part=re.sub(r'(?<=\D),(?=\d)', ', ',part)
        part=re.sub(r';(?=\S)', '; ',part)
        part=re.sub(r':(?=[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9])', ': ',part)
        part=re.sub(r'^(\d+)\.(?=\S)',r'\1. ',part,flags=re.M)
        part=part.replace('|47/47: HTTP10,kaskady10,bonus12API10,network17', '| 47/47: HTTP 10, kaskady 10, bonus 12 API 10, network 17')
        part=part.replace('53/53: AUTO13,network30,bonus12frontend7,any-start3','53/53: AUTO 13, network 30, bonus 12 frontend 7, any-start 3')
        chunks[i]=part
    return ''.join(chunks)

math = read('math/independent_full_bank_results.json')
metrics = math['metrics']
release = read('release/release_results.json')
official = read('release/official_validation_report.json')
simulation = read('release/weighted_simulation_100k.json')
browser = read('frontend/browser_checks_2026_10_21.json')

issues = [
 {'id':'B01','priority':'P2','kind':'odporność rozliczenia','title':'Wyjątek podczas serializacji może spowodować dwukrotne obciążenie tego samego żądania',
  'source':'server.py','line':342,'evidence':'server/extended_server_results.json',
  'reproduction':'W izolowanym teście asdict(result) zgłasza jednokrotnie MemoryError po zmianie salda. Pierwsza odpowiedź: HTTP 500; saldo 1 000 000 → 999 900 groszy, rounds=1, brak zapisanego wyniku. Ponowienie request_id=commit-gap obciąża kolejne 100 groszy: saldo 999 800, rounds=2.',
  'impact':'To błąd atomowości lokalnego serwera. Został dowiedziony przez wymuszenie awarii; nie zaobserwowano go podczas zwykłych rund z poprawnymi wynikami. Nie dotyczy dowiedzionego działania portfela RGS, którego tutaj nie ma.',
  'recommendation':'Przygotować pełny wynik i odpowiedź przed zmianą portfela, a zmianę salda, statystyk oraz wpis idempotencji zatwierdzać razem lub wycofywać razem.'},
 {'id':'B02','priority':'P2','kind':'stan interfejsu','title':'Retry starej rundy cofa wyświetlane saldo i statystyki po grze w drugiej karcie',
  'source':'web/app.js','line':419,'evidence':'frontend/extended_frontend_results.json',
  'reproduction':'Karta A traci odpowiedź po rozliczeniu. Karta B gra kolejną rundę w tej samej sesji. A ponawia odczyt poprzedniego ID. Serwer poprawnie zwraca ten sam wynik, ale również historyczny portfel. UI A pokazuje 999 800 groszy i 1 rundę, podczas gdy faktyczny portfel ma 999 300 groszy i 2 rundy.',
  'impact':'Brak podwójnej wypłaty w tym przypadku; gracz widzi nieaktualne saldo. Przy dalszej grze decyzja interfejsu o dostępnych środkach też może być oparta na starym stanie.',
  'recommendation':'Oddzielić niezmienny wynik rundy od aktualnego portfela. Po recovery odczytać bieżący stan sesji i stosować monotoniczną wersję portfela.'},
 {'id':'B03','priority':'P2','kind':'wznowienie','title':'Odświeżenie podczas animacji przywraca domyślną stawkę',
  'source':'web/app.js','line':378,'evidence':'frontend/extended_frontend_results.json',
  'reproduction':'Rozpocząć rundę za 100 PLN; po otrzymaniu odpowiedzi, gdy animacja nadal trwa, odświeżyć stronę. state.pending jest już skasowane. init ustawia currentBet na 10 000 groszy z historii, ale state.bet pozostaje 200 groszy. W przeglądarce potwierdzono analogicznie zmianę widocznej stawki 10 PLN → 2 PLN.',
  'impact':'Rozliczenie starej rundy pozostaje prawidłowe. Wskaźnik stawki nie odpowiada ostatnio rozegranej rundzie; przebieg animacji nie jest wznawiany od przerwanego miejsca.',
  'recommendation':'Zachowywać wybraną stawkę i etap prezentacji do zakończenia rundy; przy inicjalizacji uzgodnić state.bet, currentBet oraz wynik historyczny.'},
 {'id':'B04','priority':'P2','kind':'układ ekranu','title':'Karty bonusu są ucinane na pośrednich szerokościach',
  'source':'web/player-layout.css','line':18,'evidence':'frontend/browser_checks_2026_10_21.json',
  'reproduction':'Otworzyć grę przy viewport 802×829. .feature-rail ma 108 px, ale odziedziczone grid-template-columns tworzy trzy kolumny po 28 px. Każda karta ma clientWidth 24 px; zawartość wymaga 38/38/72 px. Widać ucięte FREE SPINS, HUSSAR CHARGE i 5,000×.',
  'impact':'Gracz nie może czytelnie odczytać opisu bonusu i maksimum. Przyczyną jest konflikt responsywnych reguł style.css:108–109 z player-layout.css; obecne testy Node nie uruchamiają tych stylów.',
  'recommendation':'Zresetować grid-template-columns na jedną kolumnę w pionowym rail albo zastosować wspólny breakpoint ukrywający/przenoszący cały panel.'},
 {'id':'B05','priority':'P2','kind':'walidacja odpowiedzi','title':'Nieprawidłowe współrzędne kaskady przechodzą walidację i przerywają animację',
  'source':'web/app.js','line':281,'evidence':'frontend/extended_frontend_results.json',
  'reproduction':'W odpowiedzi z prawdziwą rundą maksimum podmienić wyłącznie removed_positions pierwszego etapu na [[999,0]]. validateSpinResponse akceptuje tablicę, a tumbleTransition próbuje użyć nieistniejącego pola i zgłasza TypeError. pending jest już usunięte; rekord trafia do historii.',
  'impact':'To luka wykazana przez podmianę odpowiedzi testowej. Wszystkie niezmienione rekordy finalnego banku mają poprawne współrzędne, więc nie jest to dowód uszkodzenia obecnego eksportu.',
  'recommendation':'Przed zaakceptowaniem wyniku sprawdzać zakres i unikalność usunięć, strukturę/przesunięcia movements, zgodność plansz i sum etapów; odrzucić wadliwy wynik z zachowaniem możliwości recovery.'},
 {'id':'B06','priority':'P2','kind':'ładowanie zasobów','title':'Zawieszone pobieranie ilustracji nie ma limitu czasu aplikacji',
  'source':'web/app.js','line':575,'evidence':'frontend/extended_frontend_results.json',
  'reproduction':'W teście pozostawić Image bez onload i onerror, przy poprawnych odpowiedziach API. Promise.all ilustracji nie rozwiązuje się i nie ma aktywnego timera kończącego inicjalizację. Osobny limit 15 sekund w api() nie obejmuje obrazów.',
  'impact':'Fault injection potwierdza możliwość utknięcia przy ładowaniu. Przy prawidłowym pobieraniu lokalnych ilustracji ekrany załadowały się poprawnie; przeglądarka może niezależnie zakończyć rzeczywistą awarię własnym timeoutem.',
  'recommendation':'Dodać limit czasu obrazów oraz bezpieczne przejście do symboli zastępczych z możliwością ponowienia.'},
 {'id':'B07','priority':'P2','kind':'zasady gry','title':'Zasady nie określają remisów i interpretacji układu samych Wildów',
  'source':'web/app.js','line':49,'evidence':'math/independent_full_bank_results.json',
  'reproduction':'Dla L1 L1 WILD WILD P2 dwa układy płacą po 0,6×: L1 od bębna 1 (cztery symbole) i P2 od bębna 3 (trzy symbole). Silnik wybiera lewy początek. Z kolei pięć Wildów interpretuje jako P4 i płaci 40× na linię. Odczytane zasady mówią tylko o najwyższej wypłacie i zastępowaniu symboli.',
  'impact':'Nie znaleziono błędu algorytmu. Brakuje jawnego kontraktu dla gracza; rozstrzygnięcie remisu zmienia pola usuwane w następnej kaskadzie. Remisy odmiennych przedziałów występują w 50 z 100 000 możliwych ciągów.',
  'recommendation':'Dopisać wybór najbardziej lewego początku przy równych wypłatach, regułę samych Wildów oraz jawne wykluczenie zastępowania Scattera.'},
 {'id':'B08','priority':'P3','kind':'dokumentacja','title':'README wciąż zawiera nieaktualne instrukcje i liczby',
  'source':'README_PL.md','line':60,'evidence':'release/source_manifest.json',
  'reproduction':'Obok aktualnego nagłówka v0.5 pozostaje aktywne zdanie o dołączonym silniku v0.4.1, 100 048 rundach i polecenie przebudowy test-interface/build_math.py. Aktualna gra ma 100 049 rund i własny test-interface-any-start/build_math.py.',
  'impact':'Osoba odtwarzająca matematykę może uruchomić kompilator innej wersji. Część README oznaczono historycznie, ale późniejsze bieżące instrukcje nadal są sprzeczne.',
  'recommendation':'Przenieść opis v0.4 do wyraźnej historii; w części uruchomieniowej zostawić wyłącznie dane i polecenia v0.5.'},
 {'id':'B09','priority':'P3','kind':'paczka demo','title':'ZIP nie zawiera START_UX.cmd polecanego na początku instrukcji',
  'source':'package_demo.py','line':28,'evidence':'release/release_results.json',
  'reproduction':'Zbudować ZIP oficjalnym lokalnym package_demo.py i porównać spis. Archiwum ma 29 plików; zawiera START.cmd, lecz nie START_UX.cmd. README rozpoczyna instrukcję od uruchomienia START_UX.cmd.',
  'impact':'Polecona ścieżka startu z rozpakowanego ZIP nie istnieje. Alternatywny START.cmd jest obecny, a paczka przeszła 27 kontroli przenośnego uruchomienia.',
  'recommendation':'Dołączyć uruchamiacz UX do ZIP albo dostosować pierwszą instrukcję do faktycznie dostarczonego START.cmd.'},
]
(OUT/'BLEDY.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2),encoding='utf-8')

status = {}
def setrow(ids, value, note):
    for item in ids.split(): status[item]=(value,note)

setrow('G01 G02 G04 G05 G07 G08 G09 G10 G11 G13 G15','TAK','Kod, pełny bank i niezależny kalkulator; zakres lokalny v0.5.')
setrow('G03 G06','NIE','B07: algorytm poprawny, reguły remisów/samych Wildów niewyjaśnione graczowi.')
setrow('G12','NIEZWERYFIKOWANE','Cap rozlicza poprawnie; forced bonus-cap PASS, lecz bank nie ma bonus-cap i UI liczy wykonane FS, nie opisuje przerwanych przydzielonych FS.')
setrow('G14','TAK','Jeden tryb base, koszt 1; brak zakupu bonusu i Double Chance w aktualnym UI.')
setrow('G16','NIE','B08: README nadal miesza wersje i polecenia kompilatorów.')
setrow('SE01 SE02 SE03 SE04 SE05','TAK','Dokładne wagi i publiczny SDK PASS; jeden tryb base, koszt 1, eksport 100049 rekordów.')
setrow('W01','NIEZWERYFIKOWANE','Statystyki policzone, max 1:8 mln spełnia oba publiczne progi; jakość dziur i ogona pozostaje do oceny platformy.')
setrow('W02','TAK','100k pełnych ważonych rund, 1 mln losowań wag; trafienie dodatnie 1:6,40095.')
setrow('W03','TAK','Policzono dodatnie wagi, udział płatnych rekordów, dominację i przedziały; ujawniono znaczne dziury wysokich wypłat.')
setrow('QA01 QA02 QA03 QA04 QA05 QA06 QA07 QA08','TAK','Pełny bank, exact rational metrics, 8/10/12 FS z dodatnią wagą, granice selektora i analiza kodu selekcji.')
setrow('QA09','NIEZWERYFIKOWANE','Brak duplikatów/przesunięć; lokalny publiczny SDK akceptuje ID od zera. Aktualny prywatny uploader nie został sprawdzony.')
setrow('QA10','NIEZWERYFIKOWANE','Eksport scale100 i krok10 poprawne; produkcyjne kwoty portfela scale1000000 niewdrożone.')
setrow('QA11','NIEZWERYFIKOWANE','Publiczny SDK commit a6dccd86… PASS; brak uploadu i analizy ACP.')
setrow('QA12 QA13 QA14','TAK','Cały bank ma kompletne dane i poprawne przejścia, sumy i cap; wykonano exact replay selektora. B05 dotyczy odporności UI na podmienioną odpowiedź.')
setrow('QA15','NIEZWERYFIKOWANE','Źródła/bank i nowy audytowy ZIP zgodne, rebuild identyczny; brak identyfikacji finalnej paczki produkcyjnej dostarczonej do ACP.')
setrow('SE06 SE07 SE08 SE09','NIE','Lokalny Python i /api/*; brak produkcyjnego RGS, authenticate/play/end-round i stawek z auth.')
setrow('QA16','NIE','Waluta PLN wpisana w UI i pełne stawki PLN; brak wielowalutowego kontraktu portfela RGS.')
setrow('QA17','NIE','B03: odświeżenie nie zachowuje widocznej stawki; produkcyjne wznowienie RGS nie istnieje.')
setrow('QA18','NIEZWERYFIKOWANE','Lokalny retry zwykle bezpieczny; B01 ujawnia lukę zapisu. Brak produkcyjnej ścieżki recovery RGS.')
setrow('QA19','NIEZWERYFIKOWANE','Lokalne testy HTTP/network PASS; end-round, sesje i awarie produkcyjnego RGS nie są dostępne.')
setrow('QA20','NIE','Równoległe obciążenia lokalne rozliczane poprawnie; B01/B02 pozostają otwarte dla awarii i dwóch kart.')
setrow('QA21','NIE','UI zachowuje pending przy błędach transportu, lecz B05: wadliwe pozycje mogą przejść walidację i utracić pending przed prezentacją.')
setrow('QA22','NIEZWERYFIKOWANE','W testowanej konsoli brak ostrzeżeń/błędów przy zwykłym UI; brak produkcyjnych tokenów/RGS do sprawdzenia.')
setrow('SE10','NIE','Tabela/RTP/max dostępne, ale B07: niepełne zasady Wildów i remisów.')
setrow('SE11','NIE','Prawidłowe sumy wygranych, lecz B02: historyczne saldo może zastąpić bieżące.')
setrow('SE12','NIEZWERYFIKOWANE','Spacja i potwierdzenie AUTO sprawdzone. Aktualny frontend nie zawiera aktywnego audio/mute; test docelowego dźwięku niemożliwy.')
setrow('SE13','NIE DOTYCZY','Jeden tryb base kosztujący 1×; brak trybu kosztującego ponad2×.')
setrow('SE14','NIE','B04 przy802px; sprawdzono dodatkowo320×568,390×700,600×400 i1280×720. Brak fizycznego telefonu i rzeczywistego popout platformy.')
setrow('SE15','NIEZWERYFIKOWANE','Logika normal/quick/turbo/instant przechodzi; pełnej oceny czytelności kwot i kombinacji przy maksymalnym tempie nie zakończono.')
setrow('SE16','NIEZWERYFIKOWANE','Testowane zasoby lokalne kompletne; hosting/CDN produkcji i prawa do finalnych materiałów niepotwierdzone.')
setrow('SE17','NIE','Wybór EN działa, lecz lang z adresu uruchomienia jest ignorowany; brak kompletnego kontraktu językowego platformy.')
setrow('QA23','TAK','Ustawienia prezentacji nie wpływają na selekcję matematyki; skin jest mapowaniem tych samych kodów. Nie jest to pełna macierz zmian na każdym etapie bonusu.')
setrow('QA24','TAK','13 testów AUTO i30 network VM obejmują STOP po bieżącej rundzie, retry i brak automatycznego restartu po awarii.')
setrow('QA25','NIEZWERYFIKOWANE','Prawdziwa runda max: kwota i trwała informacja poprawne. Podgląd linii pokazuje wartości surowe bez rozdziału części objętej cap; ocena komunikacji pozostaje otwarta.')
setrow('QA26','TAK','UI rozróżnia przegraną, częściowy zwrot, zwrot stawki i zysk; scenariusz0,60PLN przy2PLN pokazuje częściowy zwrot.')
setrow('QA27','NIEZWERYFIKOWANE','Viewporty, przewijanie tabeli i dostępne kontrolki sprawdzone; brak pełnych testów dotyku, tła na fizycznym urządzeniu i docelowego audio.')
setrow('QA28','TAK','Scenariusze są oznaczone i nie obciążają salda; tools ukryte bez studio. To izolacja lokalnego demo, brak zatwierdzonej paczki produkcyjnej.')
setrow('SE18 SE19 SE20 SE21 SE22','NIE','Brak trybu replay platformy. replay=true jest ignorowane; dostępne pozostają zwykłe SPIN/AUTO i portfel demo.')
setrow('QA29','NIE','Brak replay i brak bonus-cap w banku. Są dodatnie rekordy8/10/12FS, middle i max bazy.')
setrow('QA30','NIEZWERYFIKOWANE','Brak wersjonowanego odtwarzania historycznych wyników RGS.')
setrow('SE23 SE24','NIE','social=true ignorowane, brak pełnych zamian słownika i obsługi SC/GC; waluta stale PLN.')
setrow('SE25','TAK','Pełna runda stanowi jeden niezależnie wybrany book; brak jackpot/gamble/continuation/cashout w aktualnym silniku.')
setrow('SE26 QA31','NIEZWERYFIKOWANE','Jest opis pochodzenia grafik. Nie wykonano prawnego clearance, weryfikacji unikalności nazwy ani pełnego przeglądu treści.')
setrow('SE27','NIE','Zasady mają notę o RTP/demo; brak kompletnego docelowego disclaimeru o awariach/recovery/rozstrzygnięciu RGS.')
setrow('SE28 SE29 SE30 SE31','NIEZWERYFIKOWANE','Brak dostępu do finalnego zgłoszenia, kafelka i stanów Approved/Active w ACP; brak dowodu zamrożenia/akceptacji konkretnej wersji.')

plan = (ROOT/'ZALOZENIA_I_PLAN_WERYFIKACJI_STAKE_ENGINE_PL.md').read_text(encoding='utf-8-sig')
requirements = re.findall(r'^- \[ \] ([A-Z]+\d+) — (.+)$',plan,re.M)
assert len(requirements)==81, len(requirements)
assert set(status)=={x[0] for x in requirements}, (set(status)^set(x[0] for x in requirements))
checklist=['# Status81 punktów weryfikacji POLSKA GUROM', '', 'Data domknięcia:21.10.2026. Wersja:0.5.0-any-start. Dowody lokalne wykonano20–21.10.2026.', '', 'TAK oznacza dowód w opisanym zakresie lokalnym. NIE oznacza wykrytą sprzeczność lub brak implementacji. NIEZWERYFIKOWANE oznacza brak pełnego dowodu — nie jest zaliczeniem. NIE DOTYCZY wymaga podanego uzasadnienia. Wiersze łączące kilka wymagań są ocenione łącznie, więc częściowy sukces nie daje TAK.', '', '| Punkt | Wynik | Dowód / uzasadnienie |', '|---|---|---|']
rows=[]
for key,requirement in requirements:
    value,note=status[key]
    rows.append({'id':key,'requirement':requirement,'status':value,'evidence_or_reason':note})
    checklist.append(f'| {key} | {value} | {note} |')
checklist += ['', '## Dowody wspólne', '', evidence('Pełny bank i kalkulator','math/independent_full_bank_results.json')+' · '+evidence('Regresje API','server/suite_results.json')+' · '+evidence('Reprodukcje serwera','server/extended_server_results.json')+' · '+evidence('Reprodukcje UI','frontend/extended_frontend_results.json')+' · '+evidence('Prawdziwa przeglądarka','frontend/browser_checks_2026_10_21.json')+' · '+evidence('Publiczny SDK','release/official_validation_report.json'), '', 'Pełne brzmienie wymagań zachowano w CHECKLISTA_81.json i w dokumencie wejściowym. Statystyki tej checklisty nie są oceną akceptacji platformy.']
(OUT/'CHECKLISTA_81_PL.md').write_text(readable('\n'.join(checklist)+'\n'),encoding='utf-8')
(OUT/'CHECKLISTA_81.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')

lines=['# POLSKA GUROM — pełny audyt gry i matematyki', '', '**Wersja:0.5.0-any-start. Domknięcie:21.10.2026. Badana gra:test-interface-any-start.**', '',
'**Wynik: nie wykryto błędów obliczania wypłat w całym aktualnym banku. Wykryto błędy odporności rozliczeń, stanu interfejsu, układu i dokumentacji. Gra jest lokalnym demonstratorem; nie ma kompletnej integracji pozwalającej uznać ją za gotową do publikacji na Stake Engine.**', '',
'Przeprowadzono audyt, dopisano izolowane testy reprodukujące luki i utworzono dowody. Kod gry oraz materiały sources nie były zmieniane. Zgodność źródeł z dowodami sprawdzono ponownie21.10.2026.', '',
'##1. Co faktycznie sprawdzono', '', '| Kontrola | Wynik i zakres |', '|---|---|',
'| Istniejące testy Python | 47/47: HTTP 10, kaskady 10, bonus 12 API 10, network 17 |',
'| Istniejące testy JavaScript | 53/53: AUTO 13, network 30, bonus 12 frontend 7, any-start 3; rzeczywisty app.js w Node VM z atrapami DOM/API |',
'| Pełna matematyka | 100 049/100 049 rund, 212 009 etapów, 107 598 przejść, 367 959 wypłat linii; 6 582 479 asercji |',
'| Wszystkie ciągi jednej linii |100000 kombinacji10 symboli na5 polach;0 rozbieżności |',
'| Selekcja według wag |200098 skrajnych biletów dla100049 przedziałów;0 rozbieżności |',
'| Testy dodatkowe |14 prób serwera i5 prób frontendu; część celowo potwierdza błędy, więc PASS reprodukcji nie oznacza poprawności gry |',
'| Limit i kaskady |Wymuszone częściowe wypłaty, cap bazy i cap bonusu oraz10000 naturalnych rund kontrolnych:PASS |',
'| Symulacje |100000 pełnych rund faktycznego selektora oraz1000000 dodatkowych losowań wag |',
'| Publiczny walidator |PASS, bez ostrzeżeń; niezmodyfikowany SDK commit a6dccd86de740cc5d318079483cb6204cc5c19bc |',
'| Odtworzenie eksportu |Books,CSV,index,selection identyczne bajtowo; mathematics.json identyczny po pominięciu czasu budowania |',
'| Paczka przenośna |Nowy audytowy ZIP:29 plików,CRC i zgodność źródeł poprawne,27/27 smoke checks |',
'| Przeglądarka |Rzeczywista gra:320×568,390×700,600×400,802×829,1280×720; tabela,ustawienia,AUTO,scenariusz0,60PLN,reload oraz parametry adresu |', '',
'Nie uruchamiano historycznych testów v0.2/v0.4 jako dowodu poprawności v0.5. Nie symulowano fizycznego telefonu, rzeczywistego portfela, prywatnego uploadera ani oceny ACP.', '',
'##2. Matematyka końcowego rozkładu', '',
'Dla wag wᵢ i wypłat pᵢ zapisanych w skali100: RTP=Σ(wᵢpᵢ)/(100·Σwᵢ·koszt). Tutaj suma wag=1000000000000, suma ważonych wypłat=96000000000000, koszt=1, zatem **RTP=24/25=96% dokładnie**. Wartość nie pochodzi z oszacowania Monte Carlo.', '',
'| Parametr | Dokładny wynik / wartość |', '|---|---:|',
f"| Rekordy z dodatnią wagą |{metrics['positive_weight_records']} |",
f"| Różne całkowite wypłaty |{metrics['distinct_payouts']} |",
'| Dodatnia wypłata |>0:15,622691917%, średnio1:6,40095 |',
'| Brak wypłaty |84,377308083% |',
'| Częściowy zwrot,0<wygrana<stawka |5,2029732632% |',
'| Zwrot równy stawce |0,6133185822% |',
'| Zysk,wygrana>stawka |9,8064000716%, około1:10,20 |',
'| Bonus dowolny |0,496993554%, średnio1:201,20985 |',
'| 8FS |473 rekordy;0,4679041094%,1:213,719 |',
'| 10FS |29 rekordów;0,028687567%,1:3485,831 |',
'| 12FS |24 rekordy;0,0004018776%,1:248831,983 |',
'| Maksimum5000× |4 rekordy,łączna szansa1:8000000 |',
'| Wariancja / odchylenie standardowe |99,023619919066 /9,95106124587 stawki |',
'| Największa szansa pojedynczego rekordu |0,0022017407% |',
'| Ekspansje na wykonany FS |25,4510664211% |', '',
'RTP bazy wynosi45,60774143986 punktu procentowego, a bonusu50,39225856014 punktu. W tych liczbach bazy i bonusu zawarte są odpowiednio wypłaty Scatterów0,6193794964 i0,0187953025 punktu. Suma daje96%. Średnia wypłata całej części bonusowej po wyzwoleniu to101,39418943×.', '',
'Bank zawiera61 726 płatnych rekordów, czyli61,6958% liczby rekordów, ale po uwzględnieniu wag dodatni wynik trafia tylko w15,6227% rund. Liczba rekordów i prawdopodobieństwo ich trafienia są różnymi miarami.', '',
'Generator kandydatów ma inne prawdopodobieństwa niż bank. Nieważona próbka100000 kandydatów ma zwrot223,8389%; nie wolno używać tego generatora bez końcowych wag jako produkcyjnego modelu96%. Obecny selektor korzysta z końcowych wag.25% ekspansji dotyczy generatora, końcowy rozkład daje25,4511%. Wybór bębnów2/3/4 po ekspansji ma udziały32,5964%/31,9140%/35,4896%.', '',
'### Rozkład wysokości wypłat', '', '| Wypłata | Prawdopodobieństwo | Wkład w RTP,p.p. |', '|---|---:|---:|']
order=['0','(0,1)','1','(1,5)','[5,20)','[20,100)','[100,500)','[500,1000)','[1000,2000)','[2000,3000)','[3000,4000)','[4000,5000)','5000']
for name in order:
    b=metrics['buckets'][name]
    lines.append(f"| {name}× | {b['probability']*100:.10g}% | {b['rtp_contribution']*100:.10g} |")
lines += ['',
'Wyniki≥100× występują w0,2195629896% rund i dostarczają37,0812% całego oczekiwanego zwrotu. Wyniki≥20× dostarczają58,6967% zwrotu. To wyjaśnia, dlaczego krótka sesja może znacznie odbiegać od96%. Samo maksimum dostarcza0,0625 punktu RTP, czyli0,0651042% oczekiwanego zwrotu.', '',
'### Symulacje i niepewność', '',
'100000 pełnych rund dało92,9898% zwrotu; przybliżony przedział normalny z próbki:87,6303–98,3493%. Dodatkowy milion losowań końcowych wag dał95,74338%; dokładne odchylenie rozkładu daje błąd standardowy około0,9951 punktu procentowego dla miliona rund. Rozkład ma ciężki rzadki ogon, więc normalne przedziały są przybliżeniem. Dokładne RTP wyznaczają wagi.', '',
'Przy częstości maksimum1:8mln brak trafienia w milionie losowań ma prawdopodobieństwo około88,25%. Brak maksimum w tej próbce nie jest niezaliczonym testem; jego częstość sprawdzono analitycznie.', '',
'##3. Znalezione błędy i luki', '',
'P1 oznacza ryzyko błędnego rozliczenia przy opisanej awarii;P2 błąd zachowania/komunikacji lub odporności;P3 problem instrukcji/paczki. Próby z celową awarią są oznaczone osobno.', '']
for issue in issues:
    lines += [f"### {issue['id']} — {issue['priority']}: {issue['title']}", '',
              '**Odtworzenie.** '+issue['reproduction'], '',
              '**Skutek i granice dowodu.** '+issue['impact'], '',
              '**Naprawa.** '+issue['recommendation'], '',
              link('Miejsce w kodzie',Path('test-interface-any-start')/issue['source'],issue['line'])+' · '+evidence('Dowód',issue['evidence']), '']
lines += ['##4. Ograniczenia projektu matematycznego wymagające decyzji', '',
'**Znaczne przerwy między wysokimi wygranymi.** W finalnym banku nie ma wyników pomiędzy995,3 a1986,9×,2018,4 a2968,3×,3010,9 a4027,4× oraz4029,6 a5000×. Pomiędzy wysokimi progami występują małe grupy kilku scenariuszy. To rzeczywiste ograniczenie różnorodności banku; nie błąd sumowania. Publiczna dokumentacja zaleca kontrolę takich luk. [Wymagania matematyki](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/math-requirements/%2Bpage.svx).', '',
'**Maksimum jest osiągalne tylko w bazie.** Wszystkie cztery rekordy5000× pochodzą z bazowych receptur. Dodatnia szansa maksimum w bonusie wynosi0. Najwyższa cała runda z8FS ma528,8×, z10FS237×, z12FS328,9×. Ogólny limit5000× jest poprawny; wymuszone testy silnika potwierdzają jego działanie w bonusie. Nie należy jednak przedstawiać bonus-cap jako scenariusza dostępnego w obecnym banku. Jeżeli taka ścieżka ma być częścią projektu, potrzebne są nowe poprawne pełne rundy z dodatnią wagą oraz ponowna kalibracja.', '',
'**Mała liczba wariantów rzadkich funkcji.**12FS ma24 kompletne realizacje, a maksimum4. Wagi nie zwiększają różnorodności ich przebiegu. Nie stwierdzono dominacji pojedynczego wyniku w całej grze, ale rzadkie funkcje mogą powtarzać te same sekwencje przy dużej liczbie odtworzeń.', '',
'##5. Brakujące elementy wersji produkcyjnej', '',
'Obecny frontend wysyła /api/config,/api/state,/api/spin do lokalnego serwera. Nie ma uruchomienia według sessionID/rgs_url, uwierzytelnienia, portfela produkcyjnego ani kończenia rundy przez RGS. Są to brakujące implementacje, a nie zaliczone integracje. [Przepływ RGS](https://stakeengine.org/docs/rgs).', '',
'Parametr replay=true jest ignorowany: nadal dostępne są zwykłe SPIN,AUTO i saldo demo. Brakuje odczytu konkretnego wyniku z endpointu replay, trybu bez portfela i odtwarzania wersji historycznej. [Wymagania replay](https://github.com/engineio/docs/blob/main/src/routes/docs/api/bet-replay/%2Bpage.svx).', '',
'Parametry lang i social z adresu również nie tworzą wymaganego kontraktu uruchomieniowego. Język wybrany w ustawieniach działa, lecz waluta jest stale PLN; brak wielowalutowych stawek z auth,SC/GC i słownika social. W teście z social=true pozostał angielski napis Bet; ustawiony w URL lang=de nie zmienił zapisanej wersji EN. [Social mode](https://github.com/engineio/docs/blob/main/src/routes/docs/reference/social-mode/%2Bpage.svx).', '',
'Docelowe audio/wyciszenie, pełny disclaimer, prawa do finalnych zasobów, kafelek, hosting/CDN i statusy ACP pozostają do wdrożenia lub potwierdzenia. Lokalna walidacja formatu nie nadaje Approved/Active. Review dotyczy konkretnej finalnej wersji. [Core Requirements](https://stakeengine.org/docs/approval-guidelines).', '',
'##6. Dowody, checklista i kolejność dalszych prac', '',
evidence('Pełna checklista81 punktów','CHECKLISTA_81_PL.md')+' · '+evidence('Matematyka — niezależny raport','math/RAPORT_MATEMATYKA_PL.md')+' · '+evidence('Serwer — raport','server/RAPORT_SERWER_PL.md')+' · '+evidence('10 przykładów do inspekcji','math/DZIESIEC_PRZYKLADOW.md')+' · '+evidence('Lista błędów JSON','BLEDY.json'), '',
'1.Naprawić atomowość zapisu rundy i dodać regresję oczekującą braku drugiego obciążenia po awarii.',
'2.Uzgodnić aktualny portfel po recovery i zachować stawkę/etap prezentacji przy reload.',
'3.Poprawić panel przy802px, walidację współrzędnych i timeout ładowania ilustracji.',
'4.Uzupełnić jednoznaczne zasady, instrukcję i zawartość ZIP.',
'5.Podjąć decyzję o rozkładzie wysokich wygranych i możliwości maksimum w bonusie przed zamrożeniem matematyki.',
'6.Wdrożyć i przetestować prawdziwe RGS,replay,waluty i wymagane tryby jurysdykcyjne; dopiero na tej samej finalnej paczce wykonać upload oraz review ACP.', '',
'Nie wykonano napraw produkcyjnego kodu w ramach tego audytu. Gdy powstaną poprawki wpływające na matematykę lub kontrakt zdarzeń, konieczne będzie ponowne sprawdzenie zmienionej paczki; wyniki tego raportu dotyczą wyłącznie wskazanych skrótów.', '',
'##7. Zrzuty ekranu', '',
'Błąd panelu przy pośredniej szerokości:', '',
f"![Ucięty panel bonusu]({(OUT/'frontend/browser_initial.png').as_posix()})", '',
'Prawdziwy telefoniczny viewport390×700 — przewijalna tabela wypłat:', '',
f"![Tabela wypłat w390×700]({(OUT/'frontend/real_paytable_390x700.png').as_posix()})", '']

# Normalize compact data notation in report headings and selected labels.
text=readable('\n'.join(lines)+'\n')
text=re.sub(r'^(#{1,3})\s*(\d+)\.',r'\1 \2.',text,flags=re.M)
(OUT/'RAPORT_KONCOWY_PL.md').write_text(text,encoding='utf-8')
counts=Counter(v[0] for v in status.values())
summary={'completed_date':'2026-10-21','version':'0.5.0-any-start','audit_completed_with_open_findings':True,
         'production_ready':False,'production_code_changed':False,'issues':len(issues),
         'checklist_statuses':dict(counts),'full_bank_passed':math['success'],
         'exact_rtp':metrics['exact_rtp'],'official_sdk_status':official['status'],
         'rebuild_identical':release['rebuild_identical'],'existing_regressions_passed':100,
         'limits':'No private ACP/uploader, real RGS wallet, physical-device or final IP clearance validation.'}
(OUT/'PODSUMOWANIE.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
