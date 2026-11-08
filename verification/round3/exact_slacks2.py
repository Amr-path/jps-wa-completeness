"""Exact min_slack (large cap) + exhaustive WA* adversary at the hill-climb endpoints (parsed verbatim from
logs_v2/climb_*.log by parse_climbs.py) and at the pinwheel; corrected criterion (core.py).
Pinwheel first: sanity check against the published 8.00 (w=1) and 7.66 (w=2)."""
import time, json, sys
from core import Grid, wa_adversary, min_slack
CAP = int(sys.argv[1]) if len(sys.argv) > 1 else 3_000_000
pin = [(2, 3), (5, 2), (6, 5), (3, 6)]
cands = [dict(name='pinwheel', w=1.0, N=9, s=(1, 1), t=(4, 4), bl=pin), dict(name='pinwheel', w=2.0, N=9, s=(1, 1), t=(4, 4), bl=pin)]
eps = json.load(open('logs_v2/climb_endpoints.json'))
order = ['climb1', 'climb7', 'climb2', 'climb4', 'climb3', 'climb6']
cands += sorted(eps, key=lambda o: order.index(o['name']))
for c in cands:
    g = Grid(c['N'], c['N'], [tuple(b) for b in c['bl']]); s, t, w = tuple(c['s']), tuple(c['t']), c['w']
    t0 = time.time(); r = min_slack(g, s, t, w, cap=CAP)
    print(c['name'], 'w', w, 'min_slack:', r[0], repr(r[1]), f'{time.time()-t0:.0f}s', flush=True)
    t0 = time.time(); a = wa_adversary(g, s, t, w, limit=CAP)
    print(c['name'], 'w', w, 'wa_adversary:', a[0], f'{time.time()-t0:.0f}s', flush=True)
print('EXACT_SLACKS_DONE', flush=True)
