"""Checks of core_exact.wa_adversary_x (2026-11-17): (1) on the pinwheel it agrees with core.wa_adversary at the ten
weights; (2) with the WA* restriction lifted (anyorder=True) it finds a failing run on the pinwheel and, on every 7th
instance of the 7x7 '+1' family, agrees with the bounded unrestricted search core.min_slack wherever that finished."""
import sys, time, math, collections
sys.path.insert(0, '/path/to/jps-wa/verification/round3')
from core import *
from core_exact import wa_adversary_x
g, t = pinwheel1(); s = (1, 1)
for w in [1, 1.1, 1.2, 1.5, 2, 3, 5, 10, 100, 1e6]:
    print('pinwheel w', w, wa_adversary_x(g, s, t, w, 2_000_000), wa_adversary(g, s, t, w, 2_000_000)[0])
print('pinwheel anyorder', wa_adversary_x(g, s, t, 1, 2_000_000, anyorder=True))
N = 7; base, t = pinwheel1(N=N); holes = [t]
cells = [c for c in Grid(N, N, []).free_cells() if c not in base.blocked and c not in holes]
cnt = collections.Counter(); k = 0
for ex in cells:
    gg = Grid(N, N, sorted(base.blocked | {ex}))
    for s in gg.free_cells():
        if s in holes or dijkstra(gg, s, t) == math.inf: continue
        k += 1
        if k % 7: continue
        st, v, _ = min_slack(gg, s, t, 1.0, cap=5000, M=Model(gg, s))
        cnt[('min_slack', st, 'exact anyorder', wa_adversary_x(gg, s, t, 1, 200_000, anyorder=True))] += 1
print(dict(cnt))
