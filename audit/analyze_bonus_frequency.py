"""Read-only exact bonus frequencies and aggregation of existing Monte Carlo draws."""
from collections import Counter
from fractions import Fraction
import hashlib
import io
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
MATH = ROOT / "test-interface/stake_math"
OUT = ROOT / "audit/bonus_frequency_2026_10_19"
sys.path.insert(0,str(ROOT / "audit/stake_cascades_v04/dependencies"))
import zstandard


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    lut = [tuple(map(int,line.split(','))) for line in (MATH/'lookUpTable_base_0.csv').read_text().splitlines()]
    meta = json.loads((MATH/'mathematics.json').read_text(encoding='utf-8'))
    total = sum(row[1] for row in lut)
    assert total == meta['total_weight']
    book_types, type_weight, type_books, scatter_weight = [], Counter(), Counter(), Counter()
    bonus_credit_sum = free_spin_sum = bonus_with_expansion_weight = 0
    with (MATH/'books_base.jsonl.zst').open('rb') as source:
        with zstandard.ZstdDecompressor().stream_reader(source) as reader:
            for i,line in enumerate(io.TextIOWrapper(reader,encoding='utf-8')):
                book = json.loads(line)
                assert book['id'] == lut[i][0] == i
                round_result = book['events'][0]['data']
                base = round_result['base']
                n = base['free_spins_awarded']
                assert bool(n) == base['bonus_triggered'] == bool(round_result['free_spins'])
                book_types.append(n)
                weight = lut[i][1]
                type_weight[n] += weight
                type_books[n] += 1
                scatter_weight[base['scatter_count']] += weight
                if n:
                    bonus_credit_sum += weight*round_result['bonus_payout_units']
                    free_spin_sum += weight*len(round_result['free_spins'])
                    if any(spin['expanding_reel'] is not None for spin in round_result['free_spins']):
                        bonus_with_expansion_weight += weight
    assert len(book_types) == len(lut)
    bonus_weight = sum(weight for n,weight in type_weight.items() if n)
    p_exact = Fraction(bonus_weight,total)
    p = float(p_exact)
    assert p == meta['bonus_frequency']
    types = []
    for n,scatters in ((8,3),(10,4),(12,5)):
        w = type_weight[n]
        types.append({'scatters':scatters,'free_spins':n,'books':type_books[n],'weight':w,
                      'probability_fraction':str(Fraction(w,total)),
                      'probability':w/total,'one_in':total/w if w else None,
                      'share_of_bonuses':w/bonus_weight})
    runs = []
    for size in (10_000_000,50_000_000,100_000_000):
        path = ROOT / f'audit/stake_cascades_v04/fast_sim/weighted_results/outcome_counts_{size}.csv'
        counts = Counter()
        import csv
        with path.open(newline='',encoding='utf-8') as f:
            rows = csv.DictReader(f)
            header = rows.fieldnames
            for row in rows:
                index,count = int(row['id']),int(row['observed_count'])
                assert int(row['weight']) == lut[index][1] and int(row['payout_units']) == lut[index][2]
                counts[book_types[index]] += count
        assert sum(counts.values()) == size
        hits = sum(count for n,count in counts.items() if n)
        runs.append({'rounds':size,'bonuses':hits,'bonus_frequency':hits/size,'one_in':size/hits,
                     'by_free_spins':dict(counts),'expected_bonuses':size*p,
                     'binomial_z':(hits-size*p)/math.sqrt(size*p*(1-p)),
                     'histogram_file':str(path),'histogram_header':header})
    series = [{'paid_rounds':n,'expected_bonus_count':n*p,
               'probability_at_least_one_bonus':-math.expm1(n*math.log1p(-p)),
               'probability_no_bonus':math.exp(n*math.log1p(-p))}
              for n in (25,50,100,200,500,1000)]
    quantiles = {str(q):math.ceil(math.log1p(-q)/math.log1p(-p)) for q in (.5,.9,.95,.99)}
    result = {'scope':'Exact current finite weighted complete-round model; no game rules or weights changed',
              'math_version':meta['math_version'],'lut_sha256':hashlib.sha256((MATH/'lookUpTable_base_0.csv').read_bytes()).hexdigest(),
              'total_weight':total,'bonus_weight':bonus_weight,'probability_fraction':str(p_exact),
              'bonus_probability':p,'mean_paid_rounds_to_bonus':1/p,
              'waiting_time_quantiles':quantiles,'bonus_types':types,
              'series_probabilities':series,'previous_simulations_aggregated':runs,
              'mean_awarded_free_spins_per_bonus':free_spin_sum/bonus_weight,
              'bonus_with_at_least_one_expansion_probability':bonus_with_expansion_weight/bonus_weight,
              'conditional_mean_credited_free_spin_return_x_bet':bonus_credit_sum/bonus_weight/100,
              'free_spin_rtp_contribution':bonus_credit_sum/total/100,
              'missing_declared_bonus_types':[x for x in types if x['weight']==0],
              'note':'Waiting-time probabilities count independent paid rounds; free spins and cascades inside a round do not count as new trigger trials.'}
    (OUT/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    lines = ["# Częstość bonusów — aktualny model POLSKA GUROM", "",
             "Analiza 19.10.2026, model v0.4.0-weighted. Sprawdzono wszystkie 100 024 pełne rundy i ich końcowe wagi, a następnie przyporządkowano zapisane wyniki wcześniejszych symulacji do typów bonusu.", "",
             f"Bonus uruchamia się z dokładnym prawdopodobieństwem **{p*100:.9f}%** na płatną rundę: średnio **raz na {1/p:.2f} płatnych rund**.", "",
             "To częstość wynikająca z końcowego rozkładu gry. Parametry naturalnego generatora kandydatów nie określają bezpośrednio szans po nadaniu wag.", "",
             "## Poszczególne bonusy", "",
             "| Początkowe Scattery | Darmowe obroty | Szansa na płatną rundę | Średnio raz na | Udział w bonusach |",
             "|---:|---:|---:|---:|---:|"]
    for row in types:
        frequency = f"{row['one_in']:.2f}" if row['one_in'] else "Nie występuje"
        lines.append(f"| {row['scatters']} | {row['free_spins']} | {100*row['probability']:.9f}% | {frequency} | {100*row['share_of_bonuses']:.2f}% |")
    lines += ["", "**Wykryta luka:** w konfiguracji są 12 darmowych obrotów za 5 Scatterów, ale w aktualnym skończonym zestawie wyników nie ma żadnej takiej rundy. Ten bonus ma obecnie szansę 0%. Wcześniejsza odpowiedź potwierdzająca dostępność całego zakresu 8/10/12 opierała się na regule konfiguracji; końcowy eksport nie pokrywa jej w całości.",
              "Wśród wyników są 473 różne rundy bonusowe z 8 obrotami i 29 z 10 obrotami. Nie ma wyniku z 12 obrotami. To błąd pokrycia zadeklarowanych możliwości gry, a nie kwestia braku szczęścia podczas krótkiego testu. Walidator formatu i porównanie wypłat nie sprawdzają, czy każdy zadeklarowany typ bonusu ma dodatnią wagę. Potrzebna jest osobna kontrola tego pokrycia.", "",
              "## Jak często bonus pojawi się w serii", "",
              "| Płatne rundy | Szansa na co najmniej jeden bonus | Szansa na brak bonusu |", "|---:|---:|---:|"]
    for row in series:
        lines.append(f"| {row['paid_rounds']} | {100*row['probability_at_least_one_bonus']:.2f}% | {100*row['probability_no_bonus']:.2f}% |")
    lines += ["", "Przy 100 płatnych obrotach brak bonusu ma prawdopodobieństwo około 60,76%. Średnio raz na 201 rund nie oznacza gwarancji trafienia w takim odstępie. Każde kolejne płatne losowanie ma tę samą szansę; poprzednie porażki jej nie podnoszą.",
              "Mediana czasu do bonusu to 140 płatnych rund. Dla szansy co najmniej 90% potrzeba 463 rund; dla 95% — 602; dla 99% — 925. Są to własności rozkładu geometrycznego, bez gwarancji wyniku konkretnej sesji.",
              "Jedna płatna runda obejmuje wszystkie jej kaskady i ewentualne darmowe obroty. Bonus nie uruchamia kolejnych darmowych obrotów. Stawka, szybkość animacji i AUTO nie zmieniają wag.", "",
              "## Porównanie z wykonanymi wcześniej symulacjami", "",
              "Poniższe wartości odczytano z pełnych histogramów zapisanych symulacji. Nie wykonywano ponownie 160 mln losowań na potrzeby tej analizy.", "",
              "| Płatne rundy | Liczba bonusów | Częstość zmierzona | Średni odstęp w próbce |", "|---:|---:|---:|---:|"]
    for row in runs:
        lines.append(f"| {row['rounds']:,} | {row['bonuses']:,} | {100*row['bonus_frequency']:.6f}% | {row['one_in']:.2f} |".replace(',',' '))
    lines += ["", "Częstości z prób są przybliżeniami. Dokładne prawdopodobieństwo wynika z wag: suma wag rund bonusowych 4 969 935 540 / suma wszystkich wag 1 000 000 000 000. W próbce 50 mln odchylenie liczby bonusów od oczekiwania wynosi −1,99 odchylenia standardowego, nieznacznie poza normalnym pasmem 95%; w próbce 100 mln wynosi −1,55. Nie dobierano nowych seedów ani nie zmieniano modelu na podstawie tych wyników.", "",
              "## Wnioski", "",
              "- Ogólna częstość bonusu to około 1:201,21.",
              "- Około 94,22% trafionych bonusów przyznaje 8 darmowych obrotów, a 5,78% przyznaje 10.",
              "- Bonus 12 obrotów wymaga poprawienia pokrycia eksportu oraz ponownego wyliczenia wag i kontroli RTP.",
              "- Ta analiza nie zmieniła reguł, wag ani bieżącej gry. Dokładne RTP obecnego rozkładu pozostaje 96%, mimo wykrytej luki w pokryciu zasad bonusu.", "",
              f"[Dokładne liczby i źródła histogramów](<{(OUT/'results.json').as_posix()}>)", ""]
    (OUT/'RAPORT_PL.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__ == '__main__':main()
