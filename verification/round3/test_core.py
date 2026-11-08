"""Sanity tests of core.py on the round-2 counterexample grid and on the 1x1 pinwheel."""
import sys, time, math
sys.path.insert(0, '/path/to/jps-wa/verification/round3')
from core import *

BLOCKED = [(3, 1), (6, 3), (1, 4), (4, 6), (1, 6)]
S = (0, 2); HOLE = [(3, 3), (4, 3), (3, 4), (4, 4)]
g = Grid(8, 8, BLOCKED)
print(grid_to_str(g, S, None, HOLE))
for t in HOLE:
    for w in (1.0, 2.0, 1e6):
        t0 = time.time()
        st, v, order = min_slack(g, S, t, w, cap=400_000)
        print(f't={t} w={w}: min_slack -> {st} {v:.3f}  ({time.time()-t0:.1f}s)')
        if st == 'FAIL' and order:
            print('  failing order', order)
            print('  reproduce (inf = failure):', reproduce(g, S, t, w, order))
# 1x1 pinwheel: is there ANY order failing (slack inf allowed)?
for L in (2, 3, 4):
    gg, c = pinwheel1(N=9)
    for s in [(0, 0), (0, 4), (1, 1), (8, 8), (4, 0)]:
        if not gg.free(*s): continue
        st, v, order = min_slack(gg, s, c, 1.0, cap=300_000)
        print(f'1x1 pinwheel N=9 s={s}: {st} {v}')
print(grid_to_str(pinwheel1(N=9)[0], (0, 0), (4, 4)))
