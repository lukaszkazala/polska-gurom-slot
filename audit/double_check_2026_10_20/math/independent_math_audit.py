"""Second independent export/rules audit; never calls production evaluators.

Rules are read from current config. Integer weights are read directly from CSV.
Every exported line, tumble, free spin and RNG draw is reconstructed here.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from fractions import Fraction
import bisect
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import random
import runpy
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
MATH = ROOT / 'test-interface/stake_math'
ENGINE = ROOT / 'test-interface/engine/polska_gurom'
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'audit/stake_cascades_v04/dependencies'))
import zstandard

C = runpy.run_path(str(ENGINE / 'config.py'))
COUNTS = Counter()

def require(ok, message):
    if not ok:
        raise AssertionError(message)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def emit(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()

def load_lut(path):
    with path.open(encoding='utf-8', newline='') as stream:
        rows = [tuple(map(int, row)) for row in csv.reader(stream)]
    for expected, row in enumerate(rows):
        require(len(row) == 3, '3 CSV fields')
        i, w, p = row
        require(i == expected and 0 <= i < 2**64, 'contiguous uint64 ID')
        require(0 < w < 2**64 and 0 <= p <= C['MAX_WIN_UNITS'] and p % 10 == 0,
                'positive uint64 weight / quantized capped payout')
    return rows

def natural_grid(rng):
    columns = []
    for strip in C['REEL_STRIPS']:
        stop = rng.randrange(len(strip))
        columns.append([strip[(stop + r) % len(strip)] for r in range(3)])
    return [[columns[c][r] for c in range(5)] for r in range(3)]

class WitnessRandom(random.Random):
    """Reimplemented draw recipe, independent of selection.RecipeRandom."""
    def __init__(self, spec):
        self.recipe = spec.get('recipe')
        super().__init__(spec['seed'] if 'seed' in spec else self.recipe['fallback_seed'])
        self.next_stops = iter(self.recipe['stops']) if self.recipe else None
        self.stops_remaining = 5 if self.recipe else 0
        self.wilds_remaining = self.recipe['wild_refill_limit'] if self.recipe else 0

    def randrange(self, stop, *args):
        if self.stops_remaining:
            self.stops_remaining -= 1
            value = next(self.next_stops)
            require(not args and 0 <= value < stop, 'legal recipe stop')
            return value
        return super().randrange(stop, *args)

    def choice(self, population):
        if self.recipe and 'WILD' in population and (self.wilds_remaining is None or self.wilds_remaining > 0):
            if self.wilds_remaining is not None:
                self.wilds_remaining -= 1
            return 'WILD'
        return super().choice(population)

def wins_for_grid(grid, multiplier):
    """Enumerate every legal payable prefix, then choose maximum award once."""
    result = []
    for number, rows in enumerate(C['PAYLINES'], 1):
        sequence = [grid[row][reel] for reel, row in enumerate(rows)]
        candidates = []
        for n in (3, 4, 5):
            prefix = set(sequence[:n]) - {'WILD'}
            for order, symbol in enumerate(C['REGULAR_SYMBOLS']):
                if prefix <= {symbol}:
                    candidates.append((C['PAYTABLE_UNITS'][symbol][n], -order, n, symbol))
        if candidates:
            units, _, n, symbol = max(candidates)
            result.append({'line_id': number, 'rows': list(rows), 'symbol': symbol,
                           'count': n, 'payout_units': units * multiplier,
                           'line_multiplier': multiplier})
    return result

def grid_valid(grid):
    require(len(grid) == 3 and all(len(row) == 5 for row in grid), '3x5 grid')
    require(all(s in C['SYMBOLS'] for row in grid for s in row), 'known symbols')

def check_spin(spin, rng, free, limit):
    grid = natural_grid(rng)
    require(spin['grid'] == grid, 'initial grid exactly matches independent RNG and reel strips')
    sc = sum(s == 'SCATTER' for row in grid for s in row)
    scatter = C['SCATTER_PAYTABLE_UNITS'].get(min(sc, 5), 0)
    award = 0 if free else C['FREE_SPINS'].get(min(sc, 5), 0)
    require(spin['scatter_count'] == sc and spin['scatter_payout_units'] == scatter,
            'Scatter original-grid count and unmultiplied award')
    require(spin['free_spins_awarded'] == award and spin['bonus_triggered'] == bool(award),
            '3/4/5 Scatter awards 8/10/12 base only; no free retrigger')
    expanded = None
    if free and rng.randrange(C['EXPANDING_WILD_DENOMINATOR']) < C['EXPANDING_WILD_NUMERATOR']:
        expanded = rng.choice(C['EXPANDING_REELS'])
    require(spin['expanding_reel'] == expanded, 'expansion exactly matches independent RNG')
    current = [row[:] for row in grid]
    if expanded is not None:
        for row in current:
            row[expanded] = 'WILD'
        COUNTS['expansions'] += 1
    require(spin['evaluation_grid'] == current, 'expansion only chosen reel before cascades')
    multiplier = C['FS_LINE_MULTIPLIER'] if free else 1
    require(spin['line_multiplier'] == multiplier, 'base x1 / free x4 line multiplier')
    steps = spin['cascades']
    require(bool(steps) and spin['line_wins'] == steps[0]['line_wins'], 'first cascade compatibility')
    require(not spin['cascade_limit_reached'], 'no exported round hits cascade safeguard')
    credit = min(scatter, limit)
    raw_lines = 0
    for stage_no, step in enumerate(steps):
        grid_valid(step['evaluation_grid'])
        require(step['evaluation_grid'] == current, 'stage grid matches independently reconstructed transition')
        wins = wins_for_grid(current, multiplier)
        require(step['line_wins'] == wins, 'independent prefix awards equal every line')
        raw = sum(win['payout_units'] for win in wins)
        require(step['line_payout_units'] == raw, 'cascade raw award total')
        require(step['payout_units'] == min(raw, limit - credit), 'remaining whole-round cap')
        credit += step['payout_units']
        raw_lines += raw
        continues = bool(wins) and credit < limit
        if continues:
            require(stage_no + 1 < len(steps), 'uncapped win must cascade')
            removed = sorted({(win['rows'][reel], reel) for win in wins for reel in range(win['count'])})
            require(step['removed_positions'] == list(map(list, removed)), 'unique union of winning positions')
            after = [row[:] for row in current]
            movements = []
            for reel in range(5):
                surviving = [(r, current[r][reel]) for r in range(3) if (r, reel) not in removed]
                holes = 3 - len(surviving)
                for dest in range(holes):
                    symbol = rng.choice(C['REFILL_STRIPS'][reel])
                    require(symbol != 'SCATTER', 'Scatter cannot refill')
                    after[dest][reel] = symbol
                    movements.append({'symbol': symbol, 'from_row': dest-holes, 'to_row': dest, 'reel': reel})
                    COUNTS['new_symbols'] += 1
                for offset, (old_row, symbol) in enumerate(surviving):
                    dest = holes + offset
                    after[dest][reel] = symbol
                    if old_row != dest:
                        require(old_row < dest, 'survivor falls down')
                        movements.append({'symbol': symbol, 'from_row': old_row, 'to_row': dest, 'reel': reel})
                        COUNTS['falling_survivors'] += 1
            require(step['movements'] == movements, 'all and only deterministic downward/refill moves')
            current = after
            COUNTS['cascade_transitions'] += 1
        else:
            require(stage_no == len(steps)-1, 'no extra cascade after terminal grid/cap')
            require(not step['removed_positions'] and not step['movements'], 'terminal stage no unplayed moves')
        COUNTS['cascade_stages'] += 1
        COUNTS['line_awards'] += len(wins)
    require(spin['line_payout_units'] == raw_lines, 'spin line aggregation')
    require(spin['raw_payout_units'] == raw_lines + scatter, 'raw lines plus Scatter')
    require(spin['payout_units'] == credit == min(raw_lines + scatter, limit), 'spin credited settlement')
    COUNTS['free_spins' if free else 'paid_spins'] += 1
    return spin['raw_payout_units'], credit

def check_round(result, spec):
    rng = WitnessRandom(spec)
    raw, total = check_spin(result['base'], rng, False, C['MAX_WIN_UNITS'])
    award = result['base']['free_spins_awarded']
    require(len(result['free_spins']) == len(result['free_spin_credits']) <= award, 'one credit per awarded FS')
    bonus = 0
    for spin, declared_credit in zip(result['free_spins'], result['free_spin_credits']):
        require(total < C['MAX_WIN_UNITS'], 'bonus must stop at max win')
        spin_raw, credit = check_spin(spin, rng, True, C['MAX_WIN_UNITS']-total)
        require(declared_credit == credit, 'free spin credited once')
        raw += spin_raw
        total += credit
        bonus += credit
    require(len(result['free_spins']) == award or total == C['MAX_WIN_UNITS'], 'all FS played unless capped')
    require(result['raw_payout_units'] == raw, 'round raw total')
    require(result['payout_units'] == total == min(raw, C['MAX_WIN_UNITS']), 'round capped total')
    require(result['bonus_payout_units'] == bonus, 'round bonus total')
    require(result['cap_reduction_units'] == raw-total, 'cap reduction total')

def exact_scatter_probabilities():
    generating = [Fraction(1)]
    windows = []
    for strip in C['REEL_STRIPS']:
        counts = Counter(sum(strip[(stop+r)%len(strip)] == 'SCATTER' for r in range(3))
                         for stop in range(len(strip)))
        windows.append(dict(counts))
        convolution = [Fraction(0)] * (len(generating) + max(counts))
        for before, before_mass in enumerate(generating):
            for count, n in counts.items():
                convolution[before+count] += before_mass * Fraction(n, len(strip))
        generating = convolution
    return windows, generating

def main():
    started = time.perf_counter()
    report = {'status': 'FAIL', 'audit': 'Fresh independent full export and draw-trace reconstruction',
              'production_evaluator_called': False,
              'command': 'python audit/double_check_2026_10_20/math/independent_math_audit.py'}
    try:
        rows = load_lut(MATH / 'lookUpTable_base_0.csv')
        weights = [row[1] for row in rows]
        payouts = [row[2] for row in rows]
        total = sum(weights)
        manifest = json.loads((MATH/'selection.json').read_text(encoding='utf-8'))
        declared = json.loads((MATH/'mathematics.json').read_text(encoding='utf-8'))
        require(total < 2**64 and total == manifest['total_weight'] == declared['total_weight'], 'weight totals')
        require(len(rows) == len(manifest['books']) == declared['book_count'], 'all book counts equal')
        require(manifest['lut_sha256'] == sha(MATH/'lookUpTable_base_0.csv'), 'LUT checksum')
        fingerprints = {name: sha(ENGINE/name) for name in ('config.py','game.py','selection.py')}
        require(fingerprints == manifest['source_fingerprint'] == declared['source_fingerprint'], 'source fingerprints')
        require(manifest['math_version'] == declared['math_version'] == C['MATH_VERSION'], 'version')
        for name, info in declared['files'].items():
            require(sha(MATH/name) == info['sha256'] and (MATH/name).stat().st_size == info['bytes'], 'file hash/size '+name)
        cdf, running = [], 0
        for weight in weights:
            running += weight
            cdf.append(running)
        for i, upper in enumerate(cdf):
            low = cdf[i-1] if i else 0
            require(bisect.bisect_right(cdf, low) == bisect.bisect_right(cdf, upper-1) == i, 'integer-ticket boundaries')
        bonus_ids = defaultdict(list)
        bonus_weights = Counter()
        bonus_returns = Counter()
        raw_scatter_counts = Counter()
        book_hashes = set()
        expansion_mass = 0
        rounds = 0
        with (MATH/'books_base.jsonl.zst').open('rb') as stream:
            with zstandard.ZstdDecompressor().stream_reader(stream) as reader:
                for line in io.TextIOWrapper(reader, encoding='utf-8'):
                    book = json.loads(line)
                    i = rounds
                    require(book['id'] == i and book['payoutMultiplier'] == payouts[i], 'CSV/book ID and payout match')
                    require(len(book['events']) == 1 and book['events'][0]['type'] == 'roundResult'
                            and book['events'][0]['index'] == 0, 'event sequence structure')
                    digest = hashlib.sha256(emit(book['events'])).hexdigest()
                    require(digest not in book_hashes, 'unique complete event sequences')
                    book_hashes.add(digest)
                    result = book['events'][0]['data']
                    require(result['payout_units'] == payouts[i], 'event payout matches CSV')
                    check_round(result, manifest['books'][i])
                    fs = result['base']['free_spins_awarded']
                    raw_scatter_counts[result['base']['scatter_count']] += 1
                    if fs:
                        bonus_ids[fs].append(i)
                        bonus_weights[fs] += weights[i]
                        bonus_returns[fs] += weights[i] * payouts[i]
                    expansion_mass += weights[i] * sum(spin['expanding_reel'] is not None for spin in result['free_spins'])
                    rounds += 1
                    if rounds % 25000 == 0:
                        print(json.dumps({'books_checked': rounds, 'elapsed_seconds': round(time.perf_counter()-started,2)}), flush=True)
        require(rounds == len(rows), 'all compressed books checked')
        for fs, ids in bonus_ids.items():
            group = manifest['bonus_coverage'][str(fs)]
            require(group['book_ids'] == ids and group['total_weight'] == bonus_weights[fs]
                    and C['FREE_SPINS'][group['scatters']] == fs, 'coverage metadata equals actual full export')
        require(set(bonus_ids) == set(C['FREE_SPINS'].values()), 'all declared bonus types selectable')
        rtp = Fraction(sum(w*p for w,p in zip(weights,payouts)), total*C['PAYOUT_SCALE'])
        second = Fraction(sum(w*p*p for w,p in zip(weights,payouts)), total*C['PAYOUT_SCALE']**2)
        variance = second-rtp**2
        cap_probability = Fraction(sum(w for w,p in zip(weights,payouts) if p == C['MAX_WIN_UNITS']), total)
        exact = {'rtp_fraction':str(rtp), 'rtp':float(rtp),'variance_fraction':str(variance),
                 'standard_deviation':math.sqrt(variance),'max_win_units':max(payouts),
                 'max_win_probability_fraction':str(cap_probability),
                 'hit_probability':sum(w for w,p in zip(weights,payouts) if p>0)/total,
                 'net_profit_probability':sum(w for w,p in zip(weights,payouts) if p>100)/total,
                 'expansions_per_paid_round':expansion_mass/total,
                 'distinct_payouts':len(set(payouts)), 'largest_book_probability':max(weights)/total}
        require(rtp == Fraction(24,25) and cap_probability == Fraction(1,8000000), 'exact target RTP and cap probability')
        require(str(variance) == declared['variance_fraction'], 'reported exact variance')
        for our, key in [('hit_probability','hit_frequency'),('net_profit_probability','net_profit_frequency'),
                         ('expansions_per_paid_round','expansions_per_paid_round'),('distinct_payouts','distinct_payouts'),
                         ('largest_book_probability','largest_single_book_probability')]:
            require(exact[our] == declared[key], 'reported metric '+key)
        before = ROOT/'audit/bonus12_fix_2026_10_20/before/test-interface/stake_math'
        old = json.loads((before/'mathematics.json').read_text(encoding='utf-8'))
        require(Fraction(str(old['bonus_frequency'])) == Fraction(sum(bonus_weights.values()),total), 'overall bonus probability preserved')
        windows, probs = exact_scatter_probabilities()
        comparison = []
        for scatters, fs in C['FREE_SPINS'].items():
            p = Fraction(bonus_weights[fs], total)
            comparison.append({'scatters':scatters,'free_spins':fs,'books':len(bonus_ids[fs]),
                               'integer_weight':bonus_weights[fs], 'published_probability_fraction':str(p),
                               'published_probability':float(p),'one_in':float(1/p),
                               'natural_probability_fraction':str(probs[scatters]),
                               'natural_probability':float(probs[scatters]),
                               'published_vs_natural_relative_difference':float(p/probs[scatters]-1),
                               'conditional_mean_payout_multiple':float(Fraction(bonus_returns[fs],bonus_weights[fs]*100))})
        five = Fraction(bonus_weights[12],total)
        require(abs(five-probs[5]) <= Fraction(1,2*total), '12FS calibration nearest integer ticket of exact reel probability')
        witnesses = json.loads((ROOT/'audit/bonus12_fix_2026_10_20/bonus12_witnesses.json').read_text(encoding='utf-8'))
        require(len(witnesses) == len(bonus_ids[12]) == 24, 'all 24 witness seeds exported')
        witness_seeds = {w['seed'] for w in witnesses}
        require({manifest['books'][i]['seed'] for i in bonus_ids[12]} == witness_seeds, '12FS only real natural-seeded specs')
        pos_vectors = []
        for witness in witnesses:
            rng = random.Random(witness['seed'])
            stops = [rng.randrange(len(strip)) for strip in C['REEL_STRIPS']]
            require(stops == witness['stops'], '12FS witness stops independently reproduce')
            positions = []
            for strip, stop in zip(C['REEL_STRIPS'],stops):
                positions.append(next(r for r in range(3) if strip[(stop+r)%len(strip)] == 'SCATTER'))
            pos_vectors.append(positions)
        report.update(status='PASS', math_version=C['MATH_VERSION'], lut_sha256=manifest['lut_sha256'],
                      source_fingerprint=fingerprints, compressed_file_sha256=sha(MATH/'books_base.jsonl.zst'),
                      books_checked=rounds, unique_event_sequences=len(book_hashes), total_weight=total,
                      integer_ticket_boundaries_checked=2*len(rows), exact=exact, bonus_types=comparison,
                      total_bonus_probability=float(Fraction(sum(bonus_weights.values()),total)),
                      baseline_bonus_probability=old['bonus_frequency'], total_bonus_preserved=True,
                      natural_scatter_window_counts=windows, natural_trigger_probability=float(sum(probs[3:])),
                      twelve_spin_witnesses={'count':24,'all_natural_seeds':True,
                                            'distinct_initial_scatter_row_vectors':len(set(map(tuple,pos_vectors))),
                                            'scatter_row_counts_per_reel':[dict(Counter(v[c] for v in pos_vectors)) for c in range(5)]},
                      independent_checks=dict(COUNTS), findings=[
                          {'severity':'info','topic':'generator_vs_published',
                           'detail_pl':'Rozkład końcowy jest ważonym bankiem pełnych rund. Proporcje 8/10FS zachowano z próbki473:29; nie są identyczne z naturalnym generatorem. 12FS skalibrowano do dokładnego 1/248832 z pasków. To jawny wybór matematyki, a nie dowód odtworzenia całego naturalnego rozkładu.'},
                          {'severity':'info','topic':'conditional_bonus_model',
                           'detail_pl':'24 dodatnio ważone naturalne rundy gwarantują pokrycie12FS. Nie wyczerpują wszystkich możliwych wyników ani nie dowodzą naturalnego warunkowego RTP12FS; końcowy model ma własny dokładnie obliczony RTP.'},
                          {'severity':'minor_documentation','topic':'historical_math_review_wording',
                           'path':'audit/bonus12_fix_2026_10_20/math_review.md',
                           'detail_pl':'Archiwalny przegląd propozycji wspomina sekwencje wild_refill_limit=0 obok naturalnego świadka. Faktycznie eksportowane24wyniki12FS mają wyłącznie naturalne seed; bieżący RAPORT_PL.md i eksport opisują stan końcowy.'}],
                      limitations_pl=['Walidacja lokalna publicznego formatu i reguł nie stanowi zatwierdzenia gry przez Stake.',
                                      'Przeliczenie wszystkich wyników daje dokładne statystyki skończonego banku; nie dowodzi jakości ani certyfikacji RNG środowiska produkcyjnego.',
                                      'Nie zmieniano kodu produkcyjnego, eksportu ani dawnych raportów.'])
    except Exception as error:
        report['error'] = repr(error)
        raise
    finally:
        report['elapsed_seconds'] = round(time.perf_counter()-started,3)
        report['audit_source_sha256'] = sha(Path(__file__))
        (OUT/'independent_math_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'status':report['status'],'books_checked':report.get('books_checked'),
                          'elapsed_seconds':report['elapsed_seconds'],'error':report.get('error')}),flush=True)

if __name__ == '__main__':
    main()
