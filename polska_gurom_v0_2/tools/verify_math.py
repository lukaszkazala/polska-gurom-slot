"""Independent v0.2 round mathematics from exhaustive joint histograms.

Run: python tools/verify_math.py
Requires numpy. No game scorer or theory implementation is imported. Exact
rational moments preserve shared-line and base/trigger correlations. Decimal
MGFs bound cap loss; FFT is used only for descriptive quantiles and tails.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from decimal import Decimal as Dec, localcontext, ROUND_CEILING
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import json
import math
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from polska_gurom import config as c
from tools.math_config import compute_config_fingerprint

EXPECTED_ASSUMPTIONS = {
    'uniform_independent_reel_stops': True,
    'expansion_independent_of_grid': True,
    'uniform_expanding_reel_choice': True,
    'free_spins_independent': True,
    'retriggers_enabled': False,
    'scatter_evaluated_before_expansion': True,
}


def require(condition, message):
    """Keep validation active even if Python is invoked with -O."""
    if not condition:
        raise ValueError(message)


def validate_config():
    require(c.MATH_ASSUMPTIONS == EXPECTED_ASSUMPTIONS,
            'Unsupported model assumptions; this verifier must be adapted before use.')
    require(c.ROWS == 3 and c.REELS == 5, 'This verifier supports a 5x3 grid.')
    require(c.PAYOUT_SCALE == 100, 'The histogram payout lattice must be 0.01 total bet.')
    require(c.MAX_WIN_UNITS == round(c.MAX_WIN * c.PAYOUT_SCALE), 'Inconsistent cap units.')
    require(c.MAX_WIN_UNITS > 0, 'Round cap must be positive.')
    require(len(c.PAYLINES) == 20 and len(set(c.PAYLINES)) == 20, 'Expected 20 unique fixed paylines.')
    require(all(len(line) == c.REELS and all(0 <= r < c.ROWS for r in line) for line in c.PAYLINES),
            'Invalid payline geometry.')
    require(tuple(c.EXPANDING_REELS) == (1, 2, 3), 'Supported expansion reels are 2, 3 and 4.')
    require(len(c.REEL_STRIPS) == c.REELS and all(len(s) == 36 for s in c.REEL_STRIPS),
            'This histogram version requires five 36-stop strips.')
    require(all(set(s) <= set(c.SYMBOLS) for s in c.REEL_STRIPS), 'Unknown strip symbol.')
    require(c.WILD not in c.REGULAR_SYMBOLS and c.SCATTER not in c.REGULAR_SYMBOLS, 'Invalid symbol roles.')
    require(isinstance(c.FS_LINE_MULTIPLIER, int) and c.FS_LINE_MULTIPLIER >= 1, 'FS multiplier must be a positive integer.')
    require(isinstance(c.EXPANDING_WILD_NUMERATOR, int) and isinstance(c.EXPANDING_WILD_DENOMINATOR, int)
            and 0 <= c.EXPANDING_WILD_NUMERATOR <= c.EXPANDING_WILD_DENOMINATOR
            and c.EXPANDING_WILD_DENOMINATOR > 0, 'Invalid rational expansion probability.')
    require(c.EXPANDING_WILD_PROBABILITY == c.EXPANDING_WILD_NUMERATOR / c.EXPANDING_WILD_DENOMINATOR,
            'Display and settlement expansion probabilities differ.')
    require(c.FREE_SPINS == {3: 8, 4: 10, 5: 12}, 'This frozen verifier supports 8/10/12 FS without retrigger.')
    for symbol in c.REGULAR_SYMBOLS:
        row = c.PAYTABLE_UNITS[symbol]
        require(set(row) == {3, 4, 5} and all(isinstance(v, int) and v > 0 for v in row.values()),
                'Expected positive integer awards for 3/4/5 matching symbols.')
        require(row[3] <= row[4] <= row[5], 'Paytable must be nondecreasing by match length.')
        require(all(F(str(c.PAYTABLE[symbol][n])) * c.PAYOUT_SCALE == row[n] for n in row),
                'Display paytable does not match integer settlement table.')
    require(all(F(str(c.SCATTER_PAYTABLE[k])) * c.PAYOUT_SCALE == v
                for k, v in c.SCATTER_PAYTABLE_UNITS.items()), 'Inconsistent Scatter payout units.')


def independent_sequence_award(seq):
    """Best interpretation via payable prefixes, independent of the engine scorer."""
    best = 0
    for length in (3, 4, 5):
        regular = set(seq[:length]) - {c.WILD}
        if not regular:
            best = max(best, *(c.PAYTABLE_UNITS[s][length] for s in c.REGULAR_SYMBOLS))
        elif len(regular) == 1:
            symbol = next(iter(regular))
            if symbol in c.REGULAR_SYMBOLS:
                best = max(best, c.PAYTABLE_UNITS[symbol][length])
    return best


def independent_line_mean(forced=None):
    counts = [Counter(s) for s in c.REEL_STRIPS]
    pools = [[c.WILD] if r == forced else c.SYMBOLS for r in range(c.REELS)]
    numerator = 0
    denominator = c.PAYOUT_SCALE
    for reel, strip in enumerate(c.REEL_STRIPS):
        if reel != forced:
            denominator *= len(strip)
    for seq in product(*pools):
        weight = 1
        for reel, symbol in enumerate(seq):
            if reel != forced:
                weight *= counts[reel][symbol]
        numerator += independent_sequence_award(seq) * weight
    return F(numerator * len(c.PAYLINES), denominator)


def scatter_counts_exact():
    distribution = {0: 1}
    for strip in c.REEL_STRIPS:
        stop_counts = Counter(sum(strip[(st + row) % len(strip)] == c.SCATTER for row in range(c.ROWS))
                              for st in range(len(strip)))
        nxt = defaultdict(int)
        for a, na in distribution.items():
            for b, nb in stop_counts.items():
                nxt[a + b] += na * nb
        distribution = dict(nxt)
    return distribution


def load_histograms(path):
    expected = compute_config_fingerprint(c)
    with np.load(path, allow_pickle=False) as archive:
        require('__math_config_sha256__' in archive, 'Histogram has no config fingerprint; regenerate it.')
        require(str(archive['__math_config_sha256__'].item()) == expected,
                'Stale histogram: config fingerprint differs. Regenerate exhaustive distributions.')
        require('__format_version__' in archive and int(archive['__format_version__'].item()) == 1,
                'Unsupported histogram format.')
        hist = {name: archive[name].copy() for name in ['base', *(f'forced_{r}' for r in c.EXPANDING_REELS)]}
    denominator = math.prod(len(s) for s in c.REEL_STRIPS)
    scatter_counts = scatter_counts_exact()
    for name, h in hist.items():
        require(h.ndim == 2 and h.shape[1] == 6 and np.issubdtype(h.dtype, np.integer)
                and np.all(h >= 0), f'Invalid integer joint histogram: {name}.')
        require(int(h.sum()) == denominator, f'Invalid probability mass: {name}.')
        require(all(int(h[:, k].sum()) == scatter_counts.get(k, 0) for k in range(6)),
                f'Original Scatter counts differ from independent enumeration: {name}.')
        line_numerator = sum(int(line) * int(h[line, sc]) for line, sc in zip(*np.nonzero(h)))
        line_mean = F(line_numerator, denominator * c.PAYOUT_SCALE)
        forced = None if name == 'base' else int(name.split('_')[1])
        require(line_mean == independent_line_mean(forced), f'Independent marginal EV check failed: {name}.')
    return hist, denominator, expected


def scatter_units(count):
    return c.SCATTER_PAYTABLE_UNITS.get(min(count, 5), 0) if count >= 3 else 0


def payout_counts(hist, multiplier):
    result = Counter()
    for line, sc in zip(*np.nonzero(hist)):
        result[multiplier * int(line) + scatter_units(int(sc))] += int(hist[line, sc])
    return result


def moment(counts, denominator, order):
    return F(sum(x ** order * n for x, n in counts.items()), denominator * c.PAYOUT_SCALE ** order)


def dense_probabilities(counts, denominator):
    result = np.zeros(max(counts) + 1, dtype=np.float64)
    for payout, count in counts.items():
        result[payout] = count / denominator
    return result


def cap_bound_decimal(base, denominator, fs_counts, fs_denominator):
    """Outward-rounded finite MGF bound; no FFT or rare-tail subtraction."""
    with localcontext() as ctx:
        ctx.prec = 60
        ctx.rounding = ROUND_CEILING
        t = Dec('0.024')
        def exp_upper(x):
            return x.exp().next_plus()
        fs_mgf = Dec(0)
        for payout, numerator in fs_counts.items():
            fs_mgf += Dec(numerator) * exp_upper(t * Dec(payout) / c.PAYOUT_SCALE) / Dec(fs_denominator)
        triggered_round_mgf = Dec(0)
        for sc, n in c.FREE_SPINS.items():
            base_mgf = Dec(0)
            for line in np.flatnonzero(base[:, sc]):
                payout = int(line) + scatter_units(sc)
                base_mgf += Dec(int(base[line, sc])) * exp_upper(t * Dec(payout) / c.PAYOUT_SCALE) / Dec(denominator)
            fs_power = Dec(1)
            for _ in range(n):
                fs_power *= fs_mgf
            triggered_round_mgf += base_mgf * fs_power
        probability_bound = exp_upper(-t * Dec(c.MAX_WIN_UNITS) / c.PAYOUT_SCALE) * triggered_round_mgf
        loss_bound = probability_bound / t
        return {
            'method': 'Outward-rounded Decimal finite MGFs; tail-integral Chernoff bound.',
            'precision': ctx.prec, 'rounding': ctx.rounding, 't': str(t),
            'cap_probability_upper_bound_decimal': str(probability_bound),
            'cap_rtp_loss_upper_bound_decimal': str(loss_bound),
            'rtp_note': 'Capped RTP lies between uncapped RTP minus this bound and uncapped RTP.',
        }


def fft_description(base_by_sc, fs_pmf, q, max_round_units):
    nfft = 1 << int(max_round_units).bit_length()
    ffz = np.fft.rfft(fs_pmf, nfft)
    full = np.zeros(nfft // 2 + 1, dtype=np.complex128)
    bonus = np.zeros_like(full)
    for sc, base_pmf in enumerate(base_by_sc):
        n = c.FREE_SPINS.get(sc, 0)
        power = ffz ** n
        full += np.fft.rfft(base_pmf, nfft) * power
        if n:
            bonus += float(base_pmf.sum()) / float(q) * power
    raw = np.fft.irfft(full, nfft)[:max_round_units + 1]
    raw_bonus = np.fft.irfft(bonus, nfft)[:max_round_units + 1]
    def summarize(values):
        negative_mass = float(-values[values < 0].sum())
        pmf = np.maximum(values, 0)
        pmf /= pmf.sum()
        cdf = np.cumsum(pmf)
        return {
            'quantiles': {str(v): int(np.searchsorted(cdf, v)) / c.PAYOUT_SCALE
                          for v in (.5, .75, .9, .95, .99, .999, .9999, .99999)},
            'probability_payout_strictly_above': {
                str(v): float(pmf[int(v * c.PAYOUT_SCALE) + 1:].sum())
                for v in (1, 5, 10, 20, 50, 100, 250, 500, 1000)},
            'numerical_negative_mass_before_clipping': negative_mass,
        }
    result = {'method': 'Numerical FFT approximation before cap; negative roundoff is clipped and mass normalized.',
              'warning': 'Do not use FFT values to infer ultra-rare cap events. Use the Decimal Chernoff bound.',
              'paid_round': summarize(raw), 'bonus_given_trigger': summarize(raw_bonus)}
    require(max(result['paid_round']['numerical_negative_mass_before_clipping'],
                result['bonus_given_trigger']['numerical_negative_mass_before_clipping']) < 1e-10,
            'Excessive FFT numerical error.')
    return result


def verify(input_path):
    validate_config()
    hist, denominator, fingerprint = load_histograms(input_path)
    base = hist['base']
    scale = c.PAYOUT_SCALE
    p = F(c.EXPANDING_WILD_NUMERATOR, c.EXPANDING_WILD_DENOMINATOR)
    m = len(c.EXPANDING_REELS)
    # Integer mixture coefficients avoid floating probabilities in all moments.
    fs_counts = Counter()
    fs_denominator = denominator * p.denominator * m
    for payout, count in payout_counts(base, c.FS_LINE_MULTIPLIER).items():
        fs_counts[payout] += count * (p.denominator - p.numerator) * m
    for reel in c.EXPANDING_REELS:
        for payout, count in payout_counts(hist[f'forced_{reel}'], c.FS_LINE_MULTIPLIER).items():
            fs_counts[payout] += count * p.numerator
    fs_counts = Counter({x: n for x, n in fs_counts.items() if n})
    require(sum(fs_counts.values()) == fs_denominator, 'Invalid free-spin mixture mass.')
    require(max(fs_counts) < c.MAX_WIN_UNITS, 'Per-FS cap could bind; frozen moment formulas require adaptation.')
    base_counts = payout_counts(base, 1)
    require(max(base_counts) < c.MAX_WIN_UNITS, 'Base cap could bind; frozen moment formulas require adaptation.')
    mu = moment(fs_counts, fs_denominator, 1)
    z2 = moment(fs_counts, fs_denominator, 2)
    ex = moment(base_counts, denominator, 1)
    ex2 = moment(base_counts, denominator, 2)
    sc_counts = [int(base[:, sc].sum()) for sc in range(6)]
    q = F(sum(sc_counts[sc] for sc in c.FREE_SPINS), denominator)
    en = F(sum(sc_counts[sc] * c.FREE_SPINS.get(sc, 0) for sc in range(6)), denominator)
    enn1 = F(sum(sc_counts[sc] * c.FREE_SPINS.get(sc, 0) * (c.FREE_SPINS.get(sc, 0) - 1)
                  for sc in range(6)), denominator)
    exn = F(sum(int(base[line, sc]) * (int(line) + scatter_units(int(sc))) * c.FREE_SPINS.get(int(sc), 0)
                for line, sc in zip(*np.nonzero(base))), denominator * scale)
    mean = ex + en * mu
    second = ex2 + 2 * mu * exn + en * z2 + enn1 * mu ** 2
    variance = second - mean ** 2
    bonus_mean = en * mu / q
    bonus_second = (en * z2 + enn1 * mu ** 2) / q
    # Triggered base awards are at least one total bet. All untriggered rounds
    # cannot receive a bonus, so partial-return and net-win rates are exact.
    require(all(scatter_units(sc) >= scale for sc in c.FREE_SPINS),
            'Net-profit formula requires triggered Scatter awards >= one total bet.')
    zero_fs = F(fs_counts.get(0, 0), fs_denominator)
    profit = F(sum(n for x, n in base_counts.items() if x > scale), denominator)
    for sc, n in c.FREE_SPINS.items():
        line = scale - scatter_units(sc)
        if line >= 0 and line < len(base):
            profit += F(int(base[line, sc]), denominator) * (1 - zero_fs ** n)
    hit = F(sum(n for x, n in base_counts.items() if x > 0), denominator)
    partial = F(sum(n for x, n in base_counts.items() if 0 < x < scale), denominator)
    even = hit - partial - profit
    base_by_sc = []
    max_base_by_sc = []
    for sc in range(6):
        counts = {int(line) + scatter_units(sc): int(base[line, sc]) for line in np.flatnonzero(base[:, sc])}
        require(bool(counts), f'No supported Scatter outcomes for {sc}.')
        base_by_sc.append(dense_probabilities(counts, denominator))
        max_base_by_sc.append(max(counts))
    max_round_units = max(max_base_by_sc[sc] + c.FREE_SPINS.get(sc, 0) * max(fs_counts) for sc in range(6))
    cap = cap_bound_decimal(base, denominator, fs_counts, fs_denominator)
    cap_loss = Dec(cap['cap_rtp_loss_upper_bound_decimal'])
    require(cap_loss < Dec('1e-12'), 'Cap-loss bound exceeds frozen calibration tolerance; recalculate capped mathematics.')
    require(abs(mean - F(96, 100)) < F(1, 10**7), 'Calibrated RTP is outside 96% +/- 1e-7.')
    fft = fft_description(base_by_sc, dense_probabilities(fs_counts, fs_denominator), q, max_round_units)
    return {
        'math_config_sha256': fingerprint, 'histogram_source': str(input_path),
        'model_assumptions': EXPECTED_ASSUMPTIONS,
        'parameters': {'payout_scale': scale, 'free_spin_line_multiplier': c.FS_LINE_MULTIPLIER,
                       'expanding_probability': float(p), 'expanding_probability_fraction': str(p),
                       'round_cap': c.MAX_WIN},
        'base_rtp': float(ex), 'bonus_rtp': float(en * mu), 'rtp_uncapped': float(mean),
        'rtp_uncapped_fraction': str(mean), 'rtp_capped_rounded_10_decimals': round(float(mean), 10),
        'cap_bound': cap,
        'base_standard_deviation': math.sqrt(float(ex2 - ex**2)),
        'paid_round_standard_deviation_uncapped': math.sqrt(float(variance)),
        'paid_round_variance_uncapped': float(variance),
        'paid_round_variance_uncapped_fraction': str(variance),
        'free_spin_mean': float(mu), 'free_spin_standard_deviation': math.sqrt(float(z2 - mu**2)),
        'mean_bonus_given_trigger': float(bonus_mean),
        'bonus_standard_deviation_given_trigger': math.sqrt(float(bonus_second - bonus_mean**2)),
        'positive_return_probability': float(hit), 'positive_below_bet_probability': float(partial),
        'net_profit_probability': float(profit), 'break_even_probability': float(even),
        'free_spin_zero_probability': float(zero_fs),
        'zero_bonus_probability_given_trigger': float(sum(F(sc_counts[sc], denominator) * zero_fs**n
                                                         for sc, n in c.FREE_SPINS.items()) / q),
        'trigger_probability': float(q), 'rounds_per_bonus': float(1 / q),
        'mean_free_spins_per_trigger': float(en / q),
        'max_base_by_scatter': [x / scale for x in max_base_by_sc],
        'max_free_spin': max(fs_counts) / scale, 'max_round_before_cap': max_round_units / scale,
        'payout_distribution_numerical_fft': fft,
        'notes': [
            'All payout values multiply total bet. A paid round includes its full triggered bonus.',
            'Positive payout frequency includes returns below total bet; net-profit frequency is reported separately.',
            'Moments before cap use exact fractions including E[XN]; cap correction is bounded separately.',
            'No universal numeric boundary defines volatility classes; use reported SD and quantiles.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'verification' / 'joint_counts.npz')
    parser.add_argument('--output', type=Path, default=ROOT / 'verification' / 'math_validation.json')
    args = parser.parse_args()
    result = verify(args.input.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('math_config_sha256', 'base_rtp', 'bonus_rtp', 'rtp_uncapped',
                       'paid_round_standard_deviation_uncapped', 'positive_return_probability',
                       'net_profit_probability', 'rounds_per_bonus')}, indent=2))
    print(f'Cap RTP-loss upper bound: {result["cap_bound"]["cap_rtp_loss_upper_bound_decimal"]}')
    print(f'Saved: {args.output.resolve()}')


if __name__ == '__main__':
    main()
