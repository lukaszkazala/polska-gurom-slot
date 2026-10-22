import sys
sys.dont_write_bytecode = True
sys.path.insert(0, r'D:\Kazaluka_slots\polska_gurom_phase2_v0.1')
import runpy
from polska_gurom import game

# In-memory mutations only: original files remain untouched.
actual_evaluate_lines = game.evaluate_lines
actual_scatter_payout = game.scatter_payout
actual_apply_expanding_wild = game.apply_expanding_wild

for mutation_name in ('double_line_payout', 'zero_scatter_payout', 'expansion_does_nothing'):
    game.evaluate_lines = actual_evaluate_lines
    game.scatter_payout = actual_scatter_payout
    game.apply_expanding_wild = actual_apply_expanding_wild
    if mutation_name == 'double_line_payout':
        game.evaluate_lines = lambda grid: 2.0 * actual_evaluate_lines(grid)
    if mutation_name == 'zero_scatter_payout':
        game.scatter_payout = lambda count: 0.0
    if mutation_name == 'expansion_does_nothing':
        game.apply_expanding_wild = lambda grid, reel: grid

    tests = runpy.run_path(r'D:\Kazaluka_slots\polska_gurom_phase2_v0.1\tests\test_math.py')
    passed = 0
    for name, function in tests.items():
        if name.startswith('test_') and callable(function):
            function()
            passed += 1
    print(f'{mutation_name}: all {passed} existing test functions pass.')
