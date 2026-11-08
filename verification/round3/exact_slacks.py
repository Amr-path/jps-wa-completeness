"""Exact (large-cap) min_slack for the best hill-climb instances and the pinwheel, corrected criterion."""
import time
from core import Grid, wa_adversary, min_slack

cands = [
    ('climb1', 1.0, (6, 1), (2, 8), [(0, 7), (1, 5), (2, 3), (2, 7), (3, 0), (3, 6), (3, 8), (4, 3), (4, 4), (5, 1), (5, 7), (6, 0), (6, 3), (6, 5), (7, 1), (8, 1), (8, 2), (8, 3), (8, 5), (8, 6), (8, 7)]),
    ('climb7', 1.5, (1, 1), (7, 7), [(0, 0), (0, 8), (1, 3), (3, 1), (3, 3), (3, 8), (4, 5), (5, 0), (5, 7), (6, 2), (8, 1), (8, 5)]),
    ('climb2', 2.0, (1, 7), (6, 0), [(0, 3), (0, 6), (0, 8), (1, 1), (1, 8), (2, 3), (2, 6), (3, 4), (4, 4), (4, 7), (5, 0), (5, 1), (6, 4), (6, 5), (7, 0), (7, 2), (7, 7), (8, 0), (8, 2)]),
    ('climb4', 3.0, (2, 5), (6, 1), [(0, 1), (1, 4), (1, 6), (3, 1), (3, 3), (3, 5), (4, 6), (5, 0), (5, 5), (6, 0), (6, 3), (6, 7), (7, 6)]),
    ('pinwheel', 1.0, (1, 1), (4, 4), [(2, 3), (5, 2), (6, 5), (3, 6)]),
    ('pinwheel', 2.0, (1, 1), (4, 4), [(2, 3), (5, 2), (6, 5), (3, 6)]),
]
for name, w, s, t, bl in cands:
    N = 8 if name == 'climb4' else 9
    g = Grid(N, N, bl)
    t0 = time.time()
    r = wa_adversary(g, s, t, w, limit=3_000_000)
    print(name, 'w', w, 'wa_adversary:', r[0], f'{time.time()-t0:.0f}s', flush=True)
    t0 = time.time()
    r = min_slack(g, s, t, w, cap=4_000_000)
    print(name, 'w', w, 'min_slack:', r[0], round(r[1], 4) if r[1] is not None else None, f'{time.time()-t0:.0f}s', flush=True)
print('EXACT_SLACKS_DONE')
