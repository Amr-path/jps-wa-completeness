"""Exact-arithmetic re-run (2026-11-17, review) of the WA* adversary on the four families of Sec. 7 at their nine
weights each (designed: search_designed.WS; exhaustive: exhaustive_pin1.WS), same state limits as the original runs
(designed 300k, exhaustive 200k). Uses core_exact.wa_adversary_x: exact priorities Q g + P h with costs a + b sqrt2,
pops only entries of exactly minimal priority, strict improvement. Instances are generated exactly as in rerun_tol.py.
usage: rerun_exact.py designed | exh N extras [pin1|pin2]"""
import sys, time, math, collections
sys.path.insert(0, '/path/to/jps-wa/verification/round3')
from core import Grid, pinwheel1, dijkstra
from core_exact import wa_adversary_x, ModelX
WS_D = [1.0, 1.2, 1.5, 2.0, 3.0, 5.0, 10.0, 100.0, 1e6]
WS_E = [1.0, 1.1, 1.5, 2.0, 3.0, 5.0, 10.0, 100.0, 1e6]

def instances():
    mode = sys.argv[1]
    if mode == 'designed':
        argv = sys.argv; sys.argv = ['x', '11', '0']
        src = open('/path/to/jps-wa/verification/round3/search_designed.py').read()
        g_ = {}; exec(src[:src.index('t0 = time.time(); n_inst')], g_); sys.argv = argv
        assert g_['WS'] == WS_D
        k = 0
        while k < 4370:
            inst = g_['instance']()
            if inst is None: continue
            k += 1; fam, g, s, t = inst; yield g, s, t, 300_000, WS_D
    else:
        N = int(sys.argv[2]); extras = int(sys.argv[3]); core_ = sys.argv[4] if len(sys.argv) > 4 else 'pin1'
        if core_ == 'pin1': base, t = pinwheel1(N=N); holes = [t]
        else: base = Grid(8, 8, [(3, 1), (6, 3), (1, 4), (4, 6), (1, 6)]); holes = [(3, 3), (4, 3), (3, 4), (4, 4)]
        cells = [c for c in Grid(N, N, []).free_cells() if c not in base.blocked and c not in holes]
        for ex in ([()] if extras == 0 else [(c,) for c in cells]):
            g = Grid(N, N, sorted(base.blocked | set(ex)))
            for s in g.free_cells():
                if s in holes: continue
                for t in holes:
                    if dijkstra(g, s, t) == math.inf: continue
                    yield g, s, t, 200_000, WS_E

tag = '_'.join(sys.argv[1:])
out = open(f'/path/to/jps-wa/verification/round3/logs_v2/rerun_exact_{tag}.log', 'w')
cnt = collections.Counter(); n = 0; t0 = time.time()
for g, s, t, lim, ws in instances():
    n += 1; M = ModelX(g, s)
    for w in ws:
        r = wa_adversary_x(g, s, t, w, lim, M); cnt[r] += 1
        if r != 'complete': print('NONCOMPLETE', r, w, g.W, s, t, sorted(g.blocked), file=out, flush=True)
    if n % 500 == 0: print(f'{time.time()-t0:.0f}s {n} {dict(cnt)}', file=out, flush=True)
print(f'DONE {tag} instances={n} runs={sum(cnt.values())} {dict(cnt)} {time.time()-t0:.0f}s', file=out, flush=True)
