from dataclasses import dataclass
from .symbols import REGULAR, SYMBOLS, WILD

@dataclass(frozen=True)
class LineWin:
    symbol: str
    count: int
    payout_units: int
    line_index: int = -1

def evaluate_line(symbols, cfg):
    if len(symbols) != 5 or any(s not in SYMBOLS for s in symbols):
        raise ValueError("A line must contain five known symbols")
    best = None
    for target in REGULAR:
        count = 0
        for symbol in symbols:
            if symbol != target and symbol != WILD:
                break
            count += 1
        if count >= 3:
            payout = cfg.paytable[target][count]
            if payout > 0 and (best is None or payout > best.payout_units):
                best = LineWin(target, count, payout)
    return best

def evaluate_board(board, cfg):
    if len(board) != 5 or any(len(reel) != 3 for reel in board):
        raise ValueError("A board must be five reels by three rows")
    wins = []
    for index, line in enumerate(cfg.paylines):
        win = evaluate_line(tuple(board[reel][row] for reel,row in enumerate(line)), cfg)
        if win is not None:
            wins.append(LineWin(win.symbol,win.count,win.payout_units,index))
    return tuple(wins)
