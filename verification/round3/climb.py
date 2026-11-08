"""Hill-climbing / mutation search minimising min_slack (distance from a WA*-realisable failure).
usage: python3 climb.py SEED W SECONDS [N] [init]   init in {pin1, pin2, rand}
Objective (to minimise): minimal slack of a failing order (bottleneck search); 'complete' (no failing order
at all) counts as +inf.  A value 0 would be a WA*-realisable failure -> reproduced with ReplayJPS and the
six built-in tie rules of the reference implementation and printed loudly."""
import sys, time, math, random
sys.path.insert(0, '/path/to/jps-wa/verification/round3')
from core import *

seed = int(sys.argv[1]); w = float(sys.argv[2]); secs = float(sys.argv[3])
N = int(sys.argv[4]) if len(sys.argv) > 4 else 9
init = sys.argv[5] if len(sys.argv) > 5 else 'pin1'
rng = random.Random(seed)
CAP = 150_000

def evaluate(bl, s, t):
    g = Grid(N, N, bl)
    if not g.free(*s) or not g.free(*t) or dijkstra(g, s, t) == math.inf: return math.inf, None, None
    st, v, order = min_slack(g, s, t, w, cap=CAP)
    if st == 'complete': return math.inf, None, None
    return v, st, order

def initial():
    if init == 'pin1':
        g, c = pinwheel1(N=N); bl = set(g.blocked); t = c
        s = rng.choice([(0, 0), (N - 1, N - 1), (0, N - 1), (N - 1, 0)])
    elif init == 'pin2':
        bl = {(3, 1), (6, 3), (1, 4), (4, 6), (1, 6)}; s = (0, 2); t = rng.choice([(3, 3), (4, 3), (3, 4), (4, 4)])
        bl = {(x + (N - 8) // 2, y + (N - 8) // 2) for x, y in bl}; s = (s[0] + (N - 8) // 2, s[1] + (N - 8) // 2)
        t = (t[0] + (N - 8) // 2, t[1] + (N - 8) // 2)
    else:
        bl = {(rng.randrange(N), rng.randrange(N)) for _ in range(rng.randint(4, 12))}
        s = (rng.randrange(N), rng.randrange(N)); t = (rng.randrange(N), rng.randrange(N))
        bl -= {s, t}
    return bl, s, t

def mutate(bl, s, t):
    bl = set(bl); r = rng.random()
    if r < 0.6:
        c = (rng.randrange(N), rng.randrange(N))
        if c in (s, t): return bl, s, t
        if c in bl: bl.remove(c)
        else: bl.add(c)
    elif r < 0.8:
        s = (rng.randrange(N), rng.randrange(N))
    elif r < 0.9:
        t = (rng.randrange(N), rng.randrange(N))
    else:   # move an obstacle by one
        if bl:
            c = rng.choice(sorted(bl)); bl.remove(c)
            d = rng.choice(DIRS8); c2 = (c[0] + d[0], c[1] + d[1])
            if 0 <= c2[0] < N and 0 <= c2[1] < N and c2 not in (s, t): bl.add(c2)
            else: bl.add(c)
    return bl, s, t

t0 = time.time(); evals = 0
bl, s, t = initial(); cur, st, order = evaluate(sorted(bl), s, t); evals += 1
best = (cur, sorted(bl), s, t, st)
print(f'init {init} w={w} N={N}: value {cur}', flush=True)
T = 1.0
while time.time() - t0 < secs:
    nbl, ns, nt = mutate(bl, s, t)
    v, nst, norder = evaluate(sorted(nbl), ns, nt); evals += 1
    if v == 0.0 and nst == 'FAIL':
        g = Grid(N, N, sorted(nbl))
        print('!!!!! WA*-REALISABLE FAILURE CANDIDATE', 'w=', w, 's=', ns, 't=', nt, 'blocked=', sorted(nbl), flush=True)
        print(grid_to_str(g, ns, nt)); print('order', norder)
        print('reproduce:', reproduce(g, ns, nt, w, norder), flush=True)
    # accept rule: downhill, or sideways/uphill with small probability (simulated annealing-ish)
    if v <= cur or (v < math.inf and rng.random() < math.exp(-(v - cur) / max(T, 1e-9))):
        bl, s, t, cur = nbl, ns, nt, v
        if v < best[0]:
            best = (v, sorted(nbl), ns, nt, nst)
            print(f'[{time.time()-t0:5.0f}s ev={evals}] best {v:.4f} ({nst}) s={ns} t={nt} blocked={sorted(nbl)}', flush=True)
    T = max(0.05, 1.0 * (1 - (time.time() - t0) / secs))
    if rng.random() < 0.01 and cur == math.inf:   # restart if stuck in 'complete' land
        bl, s, t = initial(); cur, st, order = evaluate(sorted(bl), s, t)
print('DONE', best[:1], 'evals', evals, 's=', best[2], 't=', best[3], 'blocked=', best[1])
