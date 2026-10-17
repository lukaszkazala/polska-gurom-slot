"""Build the Polish audit report from actual saved runs; never run/tune math."""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from polska_gurom.simulation import _code_hash

def read(name):
    return json.loads((ROOT / "reports/results" / name).read_text(encoding="utf-8"))

def number(value, places=6):
    return f"{value:.{places}f}".replace(".",",")

def pct(value, places=6):
    return number(100*value,places)+"%"

def percent_bound(fraction, upper=False, places=10):
    """Format an exact rational percentage with outward interval rounding."""
    factor = 10 ** places
    scaled = Fraction(fraction) * 100 * factor
    integer = -(-scaled.numerator // scaled.denominator) if upper else scaled.numerator // scaled.denominator
    return f"{integer // factor},{integer % factor:0{places}d}"

def table(headers, rows):
    def cell(value):
        return str(value).replace("|", r"\|")
    return "\n".join(["| "+" | ".join(map(cell,headers))+" |", "|"+"|".join("---" for _ in headers)+"|"]+
                     ["| "+" | ".join(map(cell,row))+" |" for row in rows])+"\n"

def main():
    a = read("analysis.json")
    sims = [read(f"simulation_{n}.json") for n in (10000,100000,1000000)]
    last = sims[-1]
    proof = read("max_win_proof.json")
    cross = read("vector_scalar_crosscheck.json")
    repro = read("simulation_reproducibility.json")
    test_path = ROOT/"reports/results/tests.json"
    tests = json.loads(test_path.read_text(encoding="utf-8")) if test_path.exists() else None
    code_hash = _code_hash()
    for result in sims:
        if result["code_sha256"] != code_hash or result["config_hash"] != a["config_hash"]:
            raise ValueError("Saved Monte Carlo does not match final source/configuration")
        if not all(result["accounting_assertions"].values()):
            raise ValueError("Monte Carlo accounting failed")
        if abs(sum(b["rtp_contribution"] for b in result["paid_round_payout_bins"])-result["rtp_post_cap"]["total"])>1e-12:
            raise ValueError("Histogram RTP mismatch")
    val = lambda name: a[name]["value"]
    sections = ["# POLSKA GUROM — raport matematyczny\n\n**PROTOTYPE / NOT MATH-FROZEN**. Audyt i uruchomienia: 17.10.2026. Nowa implementacja / rekonstrukcja z jawnymi założeniami. Wszystkie kwoty brutto w ×TOTAL BET, B=1.\n",
    "## Wynik i zakres\n\nModel działa i pozwala odtworzyć pełną rundę. **Nie spełnia celu RTP ani hit frequency.** Dokładne RTP przed cap wynosi **"+pct(val("total_rtp_pre_cap"),10)+"**, a hit base z 1M to **"+pct(last["frequency"]["hit_base"],4)+"**. Parametry nie zostały dostrojone. Nie wykonano Math Freeze, frontendu, SDK/RGS run, wag books, płatności ani publikacji.\n\nKatalog zastano pusty; nie było AGENTS.md, oryginalnego kodu/pasków, testów ani dokumentacji. Nie istniał katalog sources/. Historyczne liczności, kwoty i Charge25% wykorzystano jako parametry prototypowe. Paski pogrupowane według ID oraz20 konkretnych linii to nowe jawne założenia, nie dowód odtworzenia v0.1. Reguły, cele, parametry, dane historyczne i nierozstrzygnięte kwestie rozdzielono w GDD.\n",
    "## Cel → wynik → metoda → odchylenie → interpretacja\n\n"]
    sections.append(table(["Cel","Wynik","Metoda","Odchylenie","Interpretacja"],[
        ["Total RTP96%; zakres95,5–96,5%",pct(val("total_rtp_pre_cap"),8)+" przed cap","EXACT",number(100*val("total_rtp_pre_cap")-96,6)+" pp względem96%","Poza zakresem; cap pomijalnie obniża wynik"],
        ["Base≈73,5pp",number(100*val("base_rtp_pre_cap"),8)+" pp","EXACT; także po cap",number(100*val("base_rtp_pre_cap")-73.5)+" pp","Blisko założenia orientacyjnego"],
        ["Bonus≈22,5pp",number(100*val("bonus_rtp_pre_cap"),8)+" pp przed cap","EXACT",number(100*val("bonus_rtp_pre_cap")-22.5)+" pp","Główna luka w RTP"],
        ["Hit base25–30%",pct(last["frequency"]["hit_base"],4),"MONTE CARLO1M",number(100*last["frequency"]["hit_base"]-25,4)+" pp do dolnej granicy","Stosy skupiają wygrane na mniejszej liczbie rund"],
        ["Bonus1/150–250; środek1/200","1/"+number(val("bonus_mean_interval_paid_rounds")),"EXACT",number(val("bonus_mean_interval_paid_rounds")-200)+" rund do200","Cel częstości spełniony"],
        ["Medium-high","s²="+number(last["sample_variance"])+"; s="+number(last["sample_standard_deviation"]),"MONTE CARLO1M","Brak zatwierdzonego progu kategorii","Liczbowa charakterystyka poniżej; nazwa kategorii niecertyfikowana"],
        ["Cap5000× osiągalny","Rawmax12324×; paidmax5000×","EXACT: bound + świadek","0× względem limitu","Dodatnie prawdopodobieństwo; brak trafień w1M nie przeczy osiągalności"]]))
    sections += ["## Analityka naturalnego generatora\n\nPełne paski i paylines: `configs/reconstruction_v0_1.json`; statystyki każdego paska: `reports/results/analysis.json`. Pięć identycznych pasków36-stopowych, wspólnych dla base i FS, z historycznymi licznościami i nowym pogrupowanym porządkiem. Każdy stop jest równomierny; trzy pola to kolejne pozycje cykliczne. P(SC w oknie)=3/36, najwyżej jedenSC na bęben. Dla tej konfiguracji rozkład jest dwumianowy, lecz kod analityki splata faktyczne histogramy okien każdego bębna.\n\n",
        table(["Wielkość","Wartość","Klasyfikacja"], [
            ["P(3SC)",pct(a["trigger_distribution"]["3"]["value"],9),"EXACT"],
            ["P(4SC)",pct(a["trigger_distribution"]["4"]["value"],9),"EXACT"],
            ["P(5SC)",pct(a["trigger_distribution"]["5"]["value"],9),"EXACT"],
            ["P(bonus)",str(a["bonus_probability"]["fraction"])+" = "+pct(val("bonus_probability"),9),"EXACT"],
            ["E[liczba FS | bonus]",number(val("mean_free_spins_given_bonus"),9),"EXACT"],
            ["E[liczba FS na rundę]",number(val("mean_free_spins_per_paid_round"),9),"EXACT"],
            ["Średnia wypłata FS",number(val("free_spin_mean"),9)+"×","EXACT przed cap"],
            ["E[wypłata bonusu | trigger]",number(val("mean_bonus_given_trigger_pre_cap"),9)+"×","EXACT przed cap"],
            ["Wymagana średnia wypłata bonusu dla 22,5 pp",number(val("required_mean_bonus_for_22_5pp"),9)+"×","EXACT cel, nie wynik gry"],
            ["Wymagana średnia wypłata FS dla 22,5 pp",number(.225/val("mean_free_spins_per_paid_round"),9)+"×","EXACT cel"],
            ["Wkład Scatter base+FS",number(100*val("scatter_rtp_pre_cap"),9)+" pp","EXACT przed cap"]]),
        "RTP bonusu = P(bonus) · E[wypłata bonusu | trigger] = E[liczba FS na rundę] · E[wypłata FS]. Linie mogą być skorelowane; liniowości użyto tylko do średnich. Charge oceniany jest po zliczeniu naturalnych Scatterów; Scatter payout w FS nie przyznaje kolejnych FS.\n\n",
        table(["Charge","Wkład bonusu do RTP","Total RTP przed cap","Metoda"], [[pct(row["charge_probability"]["value"],0),"Bonus RTP "+number(100*row["bonus_rtp_pre_cap"]["value"],6)+" pp",pct(row["rtp_pre_cap"]["value"],8),"EXACT kontrfaktyczne"] for row in a["charge_sweep_pre_cap"]]),
        "Średnia wypłata FS bez Charge = "+number(val("free_spin_mean_no_charge"),9)+"×; warunkowo przy Charge = "+number(val("free_spin_mean_conditional_charge"),9)+"×. Obecne Charge dodaje do średniej FS "+number(val("charge_increment_per_free_spin"),9)+"×. Osiągnięcie 96% samym Charge wymagałoby "+pct(val("charge_probability_required_for_96pct_pre_cap"),6)+", co jest niemożliwe. Wagi bębnów 2/3/4 są punktem startowym, a nie wyprowadzonym optimum.\n"]
    sections += ["## Cap i maksimum\n\nExact post-cap RTP: **NOT CALCULATED** jako pojedyncza dokładna wartość. Zamiast utożsamienia jej z pre-cap wyznaczono **EXACT RIGOROUS BOUND**: wypłata pojedynczego spina≤1020×, średniaFS znana dokładnie, a FS są niezależne. Przez wypukłość `(x−5000)+` każdą wypłatęFS∈[0,M] można zastąpić zmienną M·Bernoulli(EFS/M), uzyskując górne ograniczenie oczekiwanej redukcji. Suma po możliwych liczbachFS i triggerach liczona jest ułamkami. To dowód ograniczenia, nie dokładne prawdopodobieństwo cap.\n\nGórna granica ubytku RTP: **"+format(a["cap"]["rtp_loss_upper_bound"]["value"],".12g")+"×** (= "+format(100*a["cap"]["rtp_loss_upper_bound"]["value"],".12g")+" pp). Zatem przy prezentacji10 miejsc RTPpaid mieści się w **["+percent_bound(a["cap"]["post_cap_rtp_lower_bound"]["fraction"])+"%; "+percent_bound(a["cap"]["post_cap_rtp_upper_bound"]["fraction"],upper=True)+"%]**. Końce zaokrąglono na zewnątrz przedziału, operując na dokładnych ułamkach; dokładne granice zapisano w JSON. Base nigdy nie osiąga cap, a bonus po cap mieści się w odpowiednim przedziale JSON; paidbase+paidbonus=paidtotal.\n\nOsobny, mocniejszy dowód maksimum (`scripts/verify_bounds.py`) wykazujeFS≤1000×. Dla≥3 naturalnychSC po najwyżej jednym Charge zostają≥2 nieprzykryteSC; co najmniej jeden jest na bębnie1–4. Pozioma linia przez niego płaci≤2×, więc spin≤19·50+2+20=972×. Przy<3SC limit wynosi20·50=1000× i jest osiągalny na stopach(31,31,31,31,31). Pełna enumeracja243 base plansz5SC daje maksimum324× przy stopach(33,33,33,33,33). Rundy3SC i4SC mają ograniczenia9020× i11020×; runda5SC ma maksimum324+12·1000=12324× i je osiąga.\n\nŚwiadek: baseall33 oraz12FSall31 bez Charge. P tej konkretnej ścieżki=(3/4)^12·36^−65≈"+format(proof["witness_probability"]["decimal_approximation"],".8g")+">0. Maksymalna przyznana wypłata5000×, redukcja7324×. `reports/max_win_witness.json` zawiera naturalne/końcowe plansze, linie i resolved settlement_trace. WszystkieFS są rozgrywane po cap; późniejsza przyznana część wynosi0. Ta ścieżka jest dowodem osiągalności, nie estymacją częstości wszystkich trafień cap.\n",
    "## Rzeczywiste symulacje pełnych rund — MONTE CARLO\n\nBackend `"+last["algorithm_version"]+"`, Python"+last["python_version"]+", NumPy"+last["numpy_version"]+". Cztery osobne strumieniePCG64 dla base stops,FS stops,Charge i wyboru bębna. Charge i wagi losowane całkowitoliczbowo. Skrypt używa seed=20261017+liczba_rund; próby są odrębne. FS nie zwiększają sumy stawek. Wszystkie osiągalne FS są rozgrywane.\n\n",
        table(["Rundy","Seed","StawkaB","WypłataB","Raw RTP=paid RTP","Basepp","Bonuspp","Scatterpp","95%CI"], [[d["paid_rounds"],d["seed"],d["total_bet"],number(d["total_payout"],2),pct(d["rtp_post_cap"]["total"],6),number(100*d["rtp_post_cap"]["base"]),number(100*d["rtp_post_cap"]["bonus"]),number(100*d["rtp_post_cap"]["scatter"]),pct(d["rtp_95pct_ci"][0],5)+"–"+pct(d["rtp_95pct_ci"][1],5)] for d in sims]),
        "Scatter to podzbiór base+bonus, nie dodatkowa składowa sumowana drugi raz. W każdej próbie redukcja cap=0, osiągnięcia cap=0; dlatego w tych próbach raw=paid. JSON zachowuje oddzielne pola i dokładne sumy w jednostkach1/100.\n\n",
        table(["Rundy","s² pełnej rundy","s","Hitbase","Hitround","X>1","0<X<1","X=1","MaxX"], [[d["paid_rounds"],number(d["sample_variance"]),number(d["sample_standard_deviation"]),pct(d["frequency"]["hit_base"],4),pct(d["frequency"]["hit_complete_round"],4),pct(d["frequency"]["payout_gt_bet"],4),pct(d["frequency"]["positive_payout_lt_bet"],4),pct(d["frequency"]["exact_stake_return"],4),number(d["maximum_observed_paid_round_payout"],2)+"×"] for d in sims]),
        "Hitbase to wypłatabase>0 przedFS — robocza definicja celu25–30%. Hitround to wypłatacałejrundy>0. Są tutaj równe, ponieważ każdy trigger ma dodatni Scatter payout.\n\n",
        table(["Rundy","Bonusy","1/p","Ebonus|bonus","FS","EFS|bonus","Charge/FS","Charge/bonus"], [[d["paid_rounds"],d["bonus_count"],number(d["bonus_mean_interval_paid_rounds"],5),number(d["mean_bonus_payout_given_bonus"],6)+"×",d["free_spin_count"],number(d["mean_free_spins_given_bonus"]),pct(d["charge_frequency_per_free_spin"],5),number(d["mean_charge_count_per_bonus"])] for d in sims]),
        table(["Rundy","Charge razem","Bęben2: n / udział","Bęben3: n / udział","Bęben4: n / udział"], [[d["paid_rounds"],d["charge_count"],*[str(d["charge_reel_selection_counts_1_based"][str(r)])+" / "+pct(d["charge_reel_selection_probabilities_given_charge"][str(r)],4) for r in (2,3,4)]] for d in sims]),
        "Bębny1 i5:0 ekspansji w każdej próbie. Teoretycznie Charge/bonus=EFS|bonus·0,25="+number(val("mean_free_spins_given_bonus")*.25,8)+"; selekcja2/3/4 po1/3. Nie ma niezależnego losowania triggera1/200.\n"]
    sections += ["## Rozkład wypłat — MONTE CARLO\n\nPrawdopodobieństwa i wkłady do RTP dla rozłącznych przedziałów, osobno dla każdej próby.\n\n",
        table(["PrzedziałX","P10k","RTP10kpp","P100k","RTP100kpp","P1M","RTP1Mpp"], [[sims[0]["paid_round_payout_bins"][i]["interval"],*[value for d in sims for value in (pct(d["paid_round_payout_bins"][i]["probability"],6),number(100*d["paid_round_payout_bins"][i]["rtp_contribution"],6))]] for i in range(9)]),
        "Wiersze sumują się do100% prawdopodobieństwa i RTP danej próby. Dokładny zwrotX=1 jest zawarty w[1;5); oddzielna częstość w tabeli powyżej nie stanowi dodatkowego przedziału.\n\n",
        table(["Ogon bonusu warunkowo na trigger","10k","100k","1M"], [[label,*[pct(d["bonus_paid_tail_probabilities_given_bonus"][key],6) for d in sims]] for key,label in (("lt_1","P(bonus<1×)"),("gt_20","P(bonus>20×)"),("gt_100","P(bonus>100×)"),("gt_500","P(bonus>500×)"),("gt_1000","P(bonus>1000×)"))]),
        "Mianownik ogona bonusu to liczba triggerów, a wypłata to przyznana część bonusowa z wyłączeniem base. Brak obserwacji>1000× nie dowodzi zerowego prawdopodobieństwa.\n"]
    sections += ["## Naturalne Wildy i Scattery\n\nEXACT: P(Wild w ustalonym polu)=1/18=5,555556%; P(≥1Wild w oknie jednego bębna)=1/9=11,111111%. Naturalnych Wildów nie zastępujemy liczbą Wildów po Charge. Pełne dane per bęben i wszystkie rozkłady z każdej próby zapisano w JSON.\n\n",
        table(["Próba","Wildpole base","Wildokno base","WildpoleFS","WildoknoFS"], [[d["paid_rounds"],pct(d["natural_board_stats"]["base"]["natural_wild_cell_frequency"],6),pct(d["natural_board_stats"]["base"]["natural_wild_reel_window_frequency"],6),pct(d["natural_board_stats"]["free_spins"]["natural_wild_cell_frequency"],6),pct(d["natural_board_stats"]["free_spins"]["natural_wild_reel_window_frequency"],6)] for d in sims]),
        table(["LiczbaSC","EXACT P","1M base: n / P","FS w próbie1M: n / P"], [[k,pct(a["scatter_distribution"][str(k)]["value"],8),str(last["natural_board_stats"]["base"]["scatter_histogram"][k])+" / "+pct(last["natural_board_stats"]["base"]["scatter_distribution"][str(k)],6),str(last["natural_board_stats"]["free_spins"]["scatter_histogram"][k])+" / "+pct(last["natural_board_stats"]["free_spins"]["scatter_distribution"][str(k)],6)] for k in range(6)]),
        "Więcejniż5SC jest niemożliwe konstrukcyjnie i sprawdzane przy wczytaniu konfiguracji. FS mają mniejszą liczebność niż1M; ich rozkład jest osobną, mniej precyzyjną estymacją.\n"]
    diag = a["diagnostics_exact_pre_cap"]
    sections += ["## Wnioski o historii, Wildach i zmienności\n\nHistoryczne średnie80,5417%,74,4530%,6,0887% odtworzono do zaokrąglenia jako **EXACT przed cap dla obecnych jawnych zasad i marginałów**. Sama zbieżność nie weryfikuje starego kodu. Hit49,6463% i max130× z dawnej1M pozostają **REPORTED / UNVERIFIED**; oryginalne paski iseed są niedostępne. Obecne hit13,8555% i max755,5× dotyczą innych, jawnych pasków. Nie ma podstaw do przypisywania tej różnicy naprawie dawnego błędu.\n\nBonus wnosi za mało, ponieważ trigger występuje raz na196,55 rundy, przyznaje średnio8,09FS, a obecnyFS ma średnią tylko1,47926×. Do22,5pp potrzeba5,46643× naFS lub44,22370× na uruchomiony bonus. Nawet100%Charge nie wystarcza.\n\nDiagnostyka **EXACT kontrfaktyczna**, bez zmiany konfiguracji: naturalne Wildy potraktowane jako blokery zamiast zastępstwa dają baseRTP"+pct(diag["base_rtp_natural_wilds_treated_as_blockers"]["value"],8)+", wobec obecnych"+pct(val("base_rtp_pre_cap"),8)+"; różnica"+number(100*diag["base_rtp_increment_from_natural_wild_substitution"]["value"],8)+"pp. To pokazuje silną rolę substytucji w EV, nie niezależny przyczynowy pomiar hit frequency. Po wyłączeniu wyłącznie Scatter payouts wFS TotalRTP wynosiłoby"+pct(diag["total_rtp_without_scatter_payout_in_free_spins"]["value"],8)+", spadek"+number(100*diag["free_spin_scatter_rtp_contribution"]["value"],8)+"pp. Historyczne średnie są zgodne z obecnością tego payout, lecz brak oryginalnego kodu pozostaje.\n\nCzęste małe historyczne wypłaty nie zostały niezależnie odtworzone. Możliwe przyczyny to marginały niskich symboli, Wild substitution i rozproszone okna zwiększające liczbę różnych trafiających linii; kolejność pasków decyduje o zależnościach. W obecnej grupowanej rekonstrukcji wiele linii trafia razem:86,1445% rund nie wypłaca,1,9921% wypłaca(0;1), a około3/8 całego RTP pochodzi z[5;20). Nie wolno traktować20 linii jako20 niezależnych prób.\n\nWariancja24,412779 iSD4,940929 w×B, ogon do755,5× w1M oraz wkład przedziałów≥20× pokazują szeroki rozkład i duże skupienie RTP w rzadkich wypłatach. Określenie medium-high pozostaje hipotezą projektową: nie uzgodniono progu ani benchmarku, więc nie oznaczamy tej kategorii jako udowodnionej. Wartości liczbowe i histogram stanowią weryfikowalne uzasadnienie charakteru rozkładu.\n\n95%CI: normalny przedział średniej pełnych rund, z wariancją próbkowąn−1.10k dało wynik poza nominalnymCI względem teorii (niska próba; rzadkie duże wypłaty powodują niestabilną wariancję i niedokładne pokrycie). Sprawdzono cykliczne okna, wspólne linie, LUT100000 kombinacji i zgodność scalar/vector2048 plansz oraz rozliczenia.100k i1M obejmują teoretyczneRTP swoimiCI. Nie wykryto rozbieżności zasad ani zmieniono paytable; pojedynczy95% przedział nie ma gwarancji pokrycia, zwłaszcza dla10k. Zgodność1M z teorią nie wyznacza dokładnie ogona.\n"]
    sections += ["## Testy i odtwarzalność\n\n"]
    if tests:
        sections.append("Rzeczywisty wynik testów deterministycznych: `"+json.dumps(tests,ensure_ascii=False)+"`. Pełny zapis `reports/results/tests.txt`, przypadki i mapowanie wymagań: `docs/TEST_PLAN.md`.\n\n")
    else:
        sections.append("Status testów deterministycznych: NOT CALCULATED — brak pliku tests.json w chwili generowania tego raportu.\n\n")
    sections += ["Crosscheck scalar/vector: `"+json.dumps(cross,ensure_ascii=False)+"`.\n\nPowtarzalność symulacji: `"+json.dumps(repro,ensure_ascii=False)+"`.\n\nWszystkie trzy raporty mają prawdziwe asercje sumy paidbase+paidbonus, pokrycia histogramu i liczbyFS zgodnej z awards. Seeded scalar i niezależny prosty evaluator objęte są testami; świadek maksimum został faktycznie oceniony przez ten sam core.\n\n",
        table(["Element","Wersja / hash"], [["Silnik","0.1.0-reconstruction"],["Konfiguracja",a["config_version"]],["SHA256 parametrów",a["config_hash"]],["SHA256 pakietu Python",code_hash],["RNG",last["algorithm_version"]+" / "+last["rng"]]]),
        "Dokładna odtwarzalność wymaga tych samych wersji, seedu, liczby rund i konfiguracji. NumPy backend i random.Random backend są odrębnymi algorytmami; nie oczekujemy identycznych sekwencji między nimi. Zmiana batchsize nie zmienia wyników. Nie inicjalizuje się stanu rozgrywki z poprzedniej płatnej rundy.\n",
        "## Stake Engine\n\nAktualne oficjalne źródła odczytano 17.10.2026; odnośniki i zakres w `docs/STAKE_COMPLIANCE.md`. Naturalny generator i ewentualny przyszły ważony zestaw books to dwa różne rozkłady. Nie powstały books ani wagi, więc ważone RTP: **NOT CALCULATED / NOT APPLICABLE w tej fazie**. Nie uruchomiono SDK/RGS; nie deklarujemy zgodności publikacyjnej. Własny evaluator jest potrzebny, aby zachować wszystkie regularne interpretacje Wildów. W odczytanym bieżącym walidatorze SDK znaleziono wymóg końcowej wypłaty co 0,10×, podczas gdy model zachowuje 0,01×; niczego nie zaokrąglano. Faktycznie uruchomiony lokalny `play_round` z `random.Random`, seedem `20261017`, dał w rundzie o indeksie `147` osiągalną wypłatę **0,45×**, która nie jest wielokrotnością 0,10×. Pełny świadek i parametry odtworzenia: `reports/sdk_payout_step_witness.json`. Status względem odczytanego walidatora: **BLOCKED_BY_CURRENT_SDK_PAYOUT_STEP**. Jest to potwierdzona niezgodność kroku wypłaty z odczytaną regułą, a nie wynik wykonania SDK. Przyszła integracja wymaga przypięcia wersji SDK i rozstrzygnięcia kroku wypłat.\n",
        "## Trzy niewdrożone warianty tuningu v0.2\n\nPoniższe propozycje nie zostały zastosowane ani zmierzone. Cel pozostaje niespełniony. Każda wymaga nowej wersji pełnych pasków, oddzielnej analityki, testów,10k/100k/1M i ponownego dowodu maksimum/cap. Nie dodajemy nowej mechaniki.\n\n",
        table(["Wariant","Obecne → proponowane","Powód i przewidywany wpływ","Ryzyko i walidacja"],[
            ["1. Układ pasków przy stałych marginałach","Grupowanie z L1run7 iWild33,34 → regularne stosy≤2; Wild8,26; P4na6,7; SC35; liczności36 bez zmian; wszystkie5 pasków nadal wspólne","Rozproszyć trafienia i zmniejszyć jednoczesne linie; wzrost hit jest przewidywaniem. Base i bonus EVprzedcap pozostaną dokładnie takie same przy tych marginałach/SC; zachowany klasterP4,P4,W umożliwia1000×FS","Hit nie jest gwarantowany; zmienność może spaść. Skonstruować pełne listy, potwierdzić Pbonus bez zmian, zmierzyć hit/variance i ponownie osiągalnośćcap. Sam ten wariant nie naprawia RTP"],
            ["2. Osobne mocniejsze paskiFS + Charge","Wspólne36-stopoweW2,L1=7 iCharge25% → osobneFS36-stopoweW4,L1=5,pozostałe liczności bez zmian,Charge75%; base bez zmian","Podnieść bonus bez zwiększenia basehit/baseRTP. SC1/36 oraz brak retriggerów pozostają; wymagany próg EFS≈5,46643× służy jako warunek analityczny, nie przewidywany wynik kandydata","WięcejWildów może zwiększyć hitFS i ogon, a silnyCharge obniżyć różnorodność. Najpierw dokładne EVFS/charge i spacingSC, potem wariancja,bonusowe ogony i cap. Nie zakładać, że4Wildy osiągną cel"],
            ["3. Rebalans częstotliwości i paytable","Wspólne paski36→33 poprzezL1 7→4 (SC1,W2 bez zmian); regularne paytable×1,00 → próbnie×0,80 w obu fazach, skala100 pozostaje dokładna; Charge25%→100%; Scatter1/5/20 bez zmian","CzęstszySC po skróceniu zwiększy bonusy i naturalneWildmarginały; redukcja tabeli ma przeciwdziałać wzrostowi base. Sama zmianaCharge nie wystarcza. Kierunek łącznegoRTP wymaga obliczeń; nie obiecujemy96%","1/33SC daje więcejtriggerów i może podejść do granicy1/150; hit może wzrosnąć. Wyliczyć dokładne Pbonus i EV przed symulacją, sprawdzić krokSDK, odrzucić jeśli cel częstości/base lub osiągalność5000 pogarsza się"]]),
        "Warianty należy rozpatrywać osobno, z porównaniem zmienianych parametrów. Ze względu na niewystarczający bonus i zbyt niskihit konieczna będzie co najmniej praca nad rozkładem pasków oraz siłą bonusu; samo strojenieCharge ma udowodniony limit. Nie uruchomiono pętli optymalizacyjnych i nie wdrożono powyższych propozycji.\n",
        "## Artefakty i ograniczenia\n\n`reports/results/analysis.json`: dokładne ułamki, histrogramy pasków, diagnostyka i ograniczenia. `simulation_*.json`: wszystkie metryki i sumy. `vector_scalar_crosscheck.json`, `simulation_reproducibility.json`, `tests.*`: rzeczywiste weryfikacje. `max_win_proof.json` i `reports/max_win_witness.json`: dowód i pełny trace. Raport wygenerowano przez `scripts/build_report.py` z tych plików; generator sprawdza zgodność hashy i sum.\n\nNOT CALCULATED: dokładny pełny rozkład/wariancja/hit po cap pozaMC oraz dokładna częstośćcap. REPORTED / UNVERIFIED: historycznyhit,max i oryginalna implementacja. Zatwierdzenie kategorii zmienności, finalne parametry i integracjaStake pozostają pracą kolejnej fazy. Model jest sprawdzalnym prototypem; jego obecna matematyka odbiega od celów.\n"]
    path = ROOT/"reports/MATH_REPORT.md"
    report = "\n".join(sections)
    readability = {
        "×TOTAL BET":"× TOTAL BET", "B=1":"B = 1", "oraz20":"oraz 20",
        "RTP96%":"RTP 96%", "zakres95,5":"zakres 95,5", "względem96%":"względem 96%",
        "Base≈73,5pp":"Base ≈ 73,5 pp", "Bonus≈22,5pp":"Bonus ≈ 22,5 pp",
        "base25":"base 25", "CARLO1M":"CARLO 1M", "Bonus1/150":"Bonus 1/150",
        "środek1/200":"środek 1/200", "do200":"do 200", "Cap5000":"Cap 5000",
        "Rawmax12324":"Raw max 12324", "paidmax5000":"paid max 5000", "w1M":"w 1M",
        "pasków36":"pasków 36", "jedenSC":"jeden SC", "P(3SC)":"P(3 SC)",
        "P(4SC)":"P(4 SC)", "P(5SC)":"P(5 SC)", "EFS|bonus":"E[liczba FS | bonus]",
        "średniaFS":"średnia wypłata FS", "wypłatęFS":"wypłatę FS", "wypłatyFS":"wypłaty FS",
        "wypłataFS":"wypłata FS", "liczbachFS":"liczbach FS", "EFS/M":"E[wypłata FS] / M",
        "spina≤":"spina ≤ ", "FS∈":"FS ∈ ", "prezentacji10":"prezentacji 10",
        "RTPpaid":"RTP paid", "paidbase":"paid base", "paidbonus":"paid bonus",
        "paidtotal":"paid total", "wykazujeFS≤1000":"wykazuje FS ≤ 1000",
        "≥3 naturalnychSC":"≥3 naturalnych SC", "zostają≥2":"zostają ≥2",
        "nieprzykryteSC":"nieprzykryte SC", "bębnie1–4":"bębnie 1–4",
        "płaci≤2":"płaci ≤2", "spin≤19":"spin ≤19", "Przy<3SC":"Przy <3 SC",
        "wynosi20":"wynosi 20", "stopach(":"stopach (", "enumeracja243":"enumeracja 243",
        "plansz5SC":"plansz 5 SC", "maksimum324":"maksimum 324", "Rundy3SC":"Rundy 3 SC",
        "i4SC":"i 4 SC", "ograniczenia9020":"ograniczenia 9020", "i11020":"i 11020",
        "runda5SC":"runda 5 SC", "maksimum324+":"maksimum 324 + ",
        "baseall33":"base: wszystkie zatrzymania 33", "oraz12FSall31":"oraz 12 FS: wszystkie zatrzymania 31",
        "wypłata5000":"wypłata 5000", "redukcja7324":"redukcja 7324",
        "WszystkieFS":"Wszystkie FS", "wynosi0":"wynosi 0", "Python":"Python ",
        "NumPy":"NumPy ", "strumieniePCG64":"strumienie PCG64", "base stops,FS":"base stops, FS",
        "stops,Charge":"stops, Charge", "StawkaB":"Stawka B", "WypłataB":"Wypłata B",
        "Basepp":"Base pp", "Bonuspp":"Bonus pp", "Scatterpp":"Scatter pp", "95%CI":"95% CI",
        "jednostkach1/100":"jednostkach 1/100", "Hitbase":"Hit base", "Hitround":"Hit round",
        "MaxX":"Max X", "wypłatabase":"wypłata base", "przedFS":"przed FS",
        "celu25":"celu 25", "wypłatacałejrundy":"wypłata całej rundy",
        "Ebonus|bonus":"E[wypłata bonusu | bonus]", "Bęben2":"Bęben 2",
        "Bęben3":"Bęben 3", "Bęben4":"Bęben 4", "Bębny1 i5:0":"Bębny 1 i 5: 0",
        "selekcja2/3/4 po1/3":"selekcja 2/3/4 po 1/3", "triggera1/200":"triggera 1/200",
        "PrzedziałX":"Przedział X", "P10k":"P 10k", "P100k":"P 100k", "P1M":"P 1M",
        "RTP10kpp":"RTP 10k pp", "RTP100kpp":"RTP 100k pp", "RTP1Mpp":"RTP 1M pp",
        "do100%":"do 100%", "zwrotX=1":"zwrot X = 1", "w[1;5)":"w [1;5)",
        "obserwacji>1000":"obserwacji >1000", "P(≥1Wild":"P(≥1 Wild",
        "WildpoleFS":"Wild — pole FS", "WildoknoFS":"Wild — okno FS",
        "Wildpole":"Wild — pole", "Wildokno":"Wild — okno", "LiczbaSC":"Liczba SC",
        "próbie1M":"próbie 1M", "próba1M":"próba 1M", "Więcejniż5SC":"Więcej niż 5 SC",
        "niż1M":"niż 1M", "średnie80":"średnie 80", "paski iseed":"paski i seed",
        "Hit49":"Hit 49", "max130":"max 130", "dawnej1M":"dawnej 1M",
        "hit13":"hit 13", "max755":"max 755", "na196":"na 196",
        "średnio8,09FS":"średnio 8,09 FS", "obecnyFS":"obecny FS", "tylko1":"tylko 1",
        "Do22,5pp":"Do 22,5 pp", "potrzeba5":"potrzeba 5", "naFS":"na FS", "lub44":"lub 44",
        "Nawet100%Charge":"Nawet 100% Charge", "baseRTP":"base RTP", "obecnych74":"obecnych 74",
        "różnica":"różnica ", "pp.":" pp.", "wFS":"w FS", "TotalRTP":"Total RTP",
        "wynosiłoby80":"wynosiłoby 80", "spadek0":"spadek 0", "wypłaty86":"wypłaty 86",
        "razem:86":"razem: 86", ",1,9921%":", 1,9921%", "wypłaca(0;1)":"wypłaca (0;1)",
        "traktować20":"traktować 20", "jako20":"jako 20", "Wariancja24":"Wariancja 24",
        "iSD4":"i SD 4", "do755":"do 755", "w1M":"w 1M", "przedziałów≥":"przedziałów ≥",
        "próbkowąn−1.10k":"próbkową n−1. 10k", "nominalnymCI":"nominalnym CI",
        "LUT100000":"LUT 100000", "scalar/vector2048":"scalar/vector 2048",
        "rozliczenia.100k":"rozliczenia. 100k", "i1M":"i 1M", "teoretyczneRTP":"teoretyczne RTP",
        "swoimiCI":"swoimi CI", "pojedynczy95%":"pojedynczy 95%", "dla10k":"dla 10k",
        "Zgodność1M":"Zgodność 1M", "liczbyFS":"liczby FS", "Seeded scalar":"Silnik skalarny z seedem",
        "batchsize":"rozmiaru partii", "testów,10k":"testów, 10k",
        "L1run7":"serią L1 długości 7", "stosy≤2":"stosy ≤2", "Wild33,34":"Wild 33,34",
        "Wild8,26":"Wild 8,26", "P4na6,7":"P4 na 6,7", "SC35":"SC 35", "liczności36":"liczności 36",
        "wszystkie5":"wszystkie 5", "EVprzedcap":"EV przed cap", "marginałach/SC":"marginałach / SC",
        "klasterP4,P4,W":"klaster P4,P4,W", "umożliwia1000×FS":"umożliwia 1000× w FS",
        "osiągalnośćcap":"osiągalność cap", "paskiFS":"paski FS", "Wspólne36":"Wspólne 36",
        "W2,L1":"W 2, L1", "iCharge25":"i Charge 25", "osobneFS36":"osobne FS 36",
        "W4,L1":"W 4, L1", ",pozostałe":", pozostałe", ",Charge75":", Charge 75",
        "basehit/baseRTP":"hit base / RTP base", "SC1/36":"SC 1/36", "EFS≈":"E[wypłata FS] ≈ ",
        "WięcejWildów":"Więcej Wildów", "hitFS":"hit FS", "silnyCharge":"silny Charge",
        "EVFS/charge":"EV FS / Charge", "spacingSC":"rozmieszczenie SC", "potem wariancja,bonusowe":"potem wariancja, bonusowe",
        "że4Wildy":"że 4 Wildy", "paski36":"paski 36", "poprzezL1":"poprzez L1",
        "SC1,W2":"SC 1, W 2", "paytable×1":"paytable ×1", "skala100":"skala 100", "Charge25":"Charge 25",
        "CzęstszySC":"Częstszy SC", "naturalneWildmarginały":"naturalne marginały Wildów",
        "zmianaCharge":"zmiana Charge", "łącznegoRTP":"łącznego RTP", "obiecujemy96":"obiecujemy 96",
        "1/33SC":"1/33 SC", "więcejtriggerów":"więcej triggerów", "granicy1/150":"granicy 1/150",
        "Pbonus":"P(bonus)", "krokSDK":"krok SDK", "osiągalność5000":"osiągalność 5000",
        "niskihit":"niski hit", "strojenieCharge":"strojenie Charge", "histrogramy":"histogramy",
        "pozaMC":"poza MC", "częstośćcap":"częstość cap", "historycznyhit,max":"historyczny hit, max",
        "integracjaStake":"integracja Stake", "s²=":"s² = ", "s=":"s = ",
        "EFS\\|bonus":"E[liczba FS \\| bonus]", "Ebonus\\|bonus":"E[wypłata bonusu \\| bonus]",
        "iWild":"i Wild", "stopoweW":"stopowe W", "próbnie×":"próbnie ×",
        "Scatter1/5/20":"Scatter 1/5/20", "Dla≥3":"Dla ≥3",
    }
    for before, after in sorted(readability.items(), key=lambda item: -len(item[0])):
        report = report.replace(before, after)
    path.write_text(report,encoding="utf-8")
    # Inventory hashes let reviewers detect edits without depending on a Git checkout.
    inventory = {}
    for folder in ("polska_gurom","configs","scripts","tests","docs"):
        for file in sorted((ROOT/folder).rglob("*")):
            if file.is_file() and "__pycache__" not in file.parts:
                inventory[file.relative_to(ROOT).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
    (ROOT/"reports/results/artifact_manifest.json").write_text(json.dumps({"config_hash":a["config_hash"],"package_sha256":code_hash,"files":inventory},indent=2),encoding="utf-8")
    print(json.dumps({"report":str(path),"package_sha256":code_hash,"simulations":len(sims),"tests_metadata_present":tests is not None}))

if __name__ == "__main__":
    main()
