"""Re-run (2026-11-03) of the WA* adversary at w = 1e6 with a tolerance relative to the magnitude of f_w.
With f_w of order 1e7, one ulp of a double is about 2e-9, so the absolute tolerance EPS = 1e-9 of core.wa_adversary
could in principle separate two mathematically equal f_w values. Here two values count as tied when they differ by
at most TOL = 1e-9 + 1e-12*|f|. A larger tolerance only adds runs (more entries count as minimal), so 'complete'
under it implies 'complete' under exact comparison. Also records, for every instance, the status of the bounded
unrestricted search (core.min_slack at w=1, same caps as the original runs): FAIL (a failing run exists) / LB (cap) /
complete (no failing run).
usage: rerun_tol.py designed | exh N extras [pin1|pin2]"""
import sys, time, math, random, collections
sys.path.insert(0, '/path/to/jps-wa/verification/round3')
from core import *
from core import _succ_state

def wa_adv_rel(grid, s, t, w, limit, M):
    h = lambda c: octile(c[0], c[1], t[0], t[1])
    start = (frozenset(), ((s, 0.0, None),))
    seen = set(); stack = [start]; n = 0
    while stack:
        closed, open_ = stack.pop()
        key = (closed, open_)
        if key in seen: continue
        seen.add(key); n += 1
        if n > limit: return 'limit'
        if not open_: return 'FAIL'
        od = {c: (g, p) for c, g, p in open_}
        fmin = min(g + w * h(c) for c, (g, p) in od.items())
        tol = 1e-9 + 1e-12 * abs(fmin)
        for x, (gx, px) in od.items():
            if gx + w * h(x) > fmin + tol: continue
            if x == t: continue
            nc, no, vis = _succ_state(M, closed, od, x, gx, px, t)
            if t in no: continue
            stack.append((nc, tuple(sorted((c, g, p) for c, (g, p) in no.items()))))
    return 'complete'

def instances():
    mode = sys.argv[1]
    if mode == 'designed':
        sys.argv = ['x', '11', '0']
        src = open('/path/to/jps-wa/verification/round3/search_designed.py').read()
        g_ = {}; exec(src[:src.index('t0 = time.time(); n_inst')], g_)
        k = 0
        while k < 4370:
            inst = g_['instance']()
            if inst is None: continue
            k += 1; fam, g, s, t = inst; yield g, s, t, 20_000, 300_000
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
                    yield g, s, t, 5_000, 200_000

tag = '_'.join(sys.argv[1:])
out = open(f'/path/to/jps-wa/verification/round3/logs_v2/rerun_tol_{tag}.log', 'w')
cnt = collections.Counter(); ms = collections.Counter(); n = 0; t0 = time.time()
for g, s, t, cap, lim in instances():
    n += 1; M = Model(g, s)
    st, v, _ = min_slack(g, s, t, 1.0, cap=cap, M=M); ms[st] += 1
    r = wa_adv_rel(g, s, t, 1e6, lim, M); cnt[r] += 1
    if r != 'complete': print('NONCOMPLETE', r, g.W, s, t, sorted(g.blocked), file=out, flush=True)
    if n % 1000 == 0: print(f'{time.time()-t0:.0f}s {n} wa1e6={dict(cnt)} unrestricted={dict(ms)}', file=out, flush=True)
print(f'DONE {tag} instances={n} wa1e6={dict(cnt)} unrestricted={dict(ms)} {time.time()-t0:.0f}s', file=out, flush=True)
