def board_from_stops(cfg, stops):
    """Reel-major board, stop is the top visible symbol, rows are 0/1/2."""
    if len(stops) != 5 or any(type(stop) is not int or not 0 <= stop < len(reel) for stop,reel in zip(stops,cfg.reels)):
        raise ValueError("Five valid integer stop positions required")
    return tuple(tuple(reel[(stop+row) % len(reel)] for row in range(3)) for reel,stop in zip(cfg.reels,stops))
