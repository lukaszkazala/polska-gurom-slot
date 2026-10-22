"""Construct attainable forced-Wild states for engine and cap regression checks."""
import json
from itertools import product
from pathlib import Path

import numpy as np

from exact_distribution import LINES, SCATTER, SYMBOL_IDS, WILD, all_stops, c, make_lut, make_windows

lut = make_lut()
windows = make_windows()
result = {}
for forced in (1, 2, 3):
    stops = all_stops([r for r in range(5) if r != forced])
    totals = np.zeros(len(stops), dtype=np.int32)
    for line in LINES:
        code = np.zeros(len(stops), dtype=np.int32)
        for reel in range(5):
            code *= 10
            code += WILD if reel == forced else windows[reel][stops[:, reel], line[reel]]
        totals += lut[code]
    idx = int(np.argmax(totals))
    selected = stops[idx].tolist()
    # The omitted original reel does not affect line awards; choose no Scatter.
    selected[forced] = int(np.where((windows[forced] != SCATTER).all(axis=1))[0][0])
    grid = [[c.SYMBOLS[int(windows[r][selected[r], row])] for r in range(5)] for row in range(3)]
    result[str(forced)] = {
        "stops": selected,
        "original_grid": grid,
        "forced_reel_zero_based": forced,
        "line_win_before_multiplier": int(totals[idx]) / 100,
        "line_win_after_multiplier_four": int(totals[idx]) * 4 / 100,
        "original_scatter_count": sum(s == c.SCATTER for row in grid for s in row),
    }
stops = np.array(list(product(*[np.where((window == SCATTER).any(axis=1))[0].tolist() for window in windows])), dtype=np.uint8)
totals = np.zeros(len(stops), dtype=np.int32)
for line in LINES:
    code = np.zeros(len(stops), dtype=np.int32)
    for reel in range(5):
        code = code * 10 + windows[reel][stops[:, reel], line[reel]]
    totals += lut[code]
idx = int(np.argmax(totals))
selected = stops[idx].tolist()
grid = [[c.SYMBOLS[int(windows[r][selected[r], row])] for r in range(5)] for row in range(3)]
result["base_five_scatter"] = {
    "stops": selected,
    "original_grid": grid,
    "line_win": int(totals[idx]) / 100,
    "scatter_win": 20.0,
    "total_win": int(totals[idx]) / 100 + 20.0,
    "original_scatter_count": 5,
    "free_spins_awarded": 12,
}
(Path(__file__).resolve().parent / "maximum_witness.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
