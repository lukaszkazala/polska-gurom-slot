from .symbols import SCATTER

def count_scatters(board):
    return sum(s == SCATTER for reel in board for s in reel)

def scatter_award(count, cfg, is_free=False):
    if not 0 <= count <= 5:
        raise ValueError("Configuration restricts the board to <=5 Scatters")
    return cfg.scatter_pays.get(count, 0), 0 if is_free else cfg.fs_awards.get(count, 0)
