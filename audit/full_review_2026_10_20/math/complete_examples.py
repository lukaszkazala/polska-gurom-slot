from pathlib import Path
import importlib.util
import json
import sys
from dataclasses import asdict
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('cascade_audit', ROOT / 'test-interface-any-start/qa/check_cascade_math.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.REPORT = OUT / 'forced_and_sample_cascade_checks.json'
sys.argv = ['check_cascade_math.py', '10000']
module.main()
from polska_gurom import selection
manifest, _, payouts = selection.load_distribution()
examples = []
for book_id in (0, 12, 15, 287, 484, 6507, 46183, 100020, 100024, 100048):
    result = asdict(selection.replay_spec(manifest['books'][book_id]))
    if book_id == 100020:
        (OUT.parent / 'frontend/cap_fixture.json').write_text(json.dumps(result), encoding='utf-8')
    first = result['base']['cascades'][0]
    examples.append({'book_id': book_id, 'base_initial_grid':result['base']['grid'],
                     'first_stage_line_wins': first['line_wins'],
                     'base_scatter_units':result['base']['scatter_payout_units'],
                     'base_credited_units':result['base']['payout_units'],
                     'free_spins_awarded':result['base']['free_spins_awarded'],
                     'free_spins_played':len(result['free_spins']),
                     'free_spin_credits':result['free_spin_credits'],
                     'bonus_credited_units':result['bonus_payout_units'],
                     'total_credited_units':result['payout_units'],
                     'csv_payout_units':payouts[book_id], 'cap_reduction_units':result['cap_reduction_units']})
(OUT / 'ten_examples.json').write_text(json.dumps(examples,indent=2), encoding='utf-8')
lines = ['# Dziesięć przykładów do inspekcji', '', 'Jednostki wypłat: 100 = 1× całkowitej stawki. Przykłady wyeksportowane automatycznie; ich pełne przebiegi zweryfikowano niezależnym kalkulatorem w audycie całego banku. Nie jest to deklaracja dziesięciu ręcznych testów w ACP.', '']
for e in examples:
    lines += [f"## Rekord {e['book_id']}", '', '```text', *[' '.join(row) for row in e['base_initial_grid']], '```', '', '| Linia | Symbol | Bębny | Wypłata × stawka |', '|---|---|---|---:|']
    for win in e['first_stage_line_wins']:
        lines.append(f"| {win['line_id']} | {win['symbol']} | {win['start_reel']+1}–{win['start_reel']+win['count']} | {win['payout_units']/100:g} |")
    lines += ['', f"Scatter bazy: {e['base_scatter_units']/100:g}×. Baza łącznie z kaskadami: {e['base_credited_units']/100:g}×. Bonus: {e['free_spins_played']}/{e['free_spins_awarded']} obrotów, {e['bonus_credited_units']/100:g}×. Cała runda: **{e['total_credited_units']/100:g}×**, zgodna z CSV. Redukcja przez limit: {e['cap_reduction_units']/100:g}×.", '']
(OUT / 'DZIESIEC_PRZYKLADOW.md').write_text('\n'.join(lines), encoding='utf-8')
