"""Randomised DFS adversary: find failing orders (Open empties, t never stepped on) on pinwheel-family instances,
many different orders per instance, and run the Lemma 4.3 checker on each terminal configuration."""
import sys, math, random
sys.path.insert(0, '/path/to/jps-wa/verification/round3'); sys.path.insert(0, '.')
from core import Model, pinwheel1, _succ_state
from lemma_frontier_test import replay_scans, check_lemma

def rand_fail(M, s, t, rng, limit=150000, want=10):
    """goal-restricted DFS (branches stepping on t pruned), randomised child order; yields up to `want` failing orders"""
    start = (frozenset(), ((s, 0.0, None),))
    seen = set(); stack = [(start, [])]; n = 0; out = []
    while stack and n < limit and len(out) < want:
        (closed, open_), order = stack.pop()
        key = (closed, open_)
        if key in seen: continue
        seen.add(key); n += 1
        if not open_: out.append(order); continue
        od = {c: (g, p) for c, g, p in open_}
        items = list(od.items()); rng.shuffle(items)
        for x, (gx, px) in items:
            if x == t: continue
            nc, no, vis = _succ_state(M, closed, od, x, gx, px)
            if t in vis: continue
            stack.append(((nc, tuple(sorted((c, g, p) for c, (g, p) in no.items()))), order + [x]))
    return out

rng = random.Random(int(sys.argv[1])); ninst = int(sys.argv[2]); per = int(sys.argv[3])
tested = edges = viol = 0
for it in range(ninst):
    N = rng.choice((7, 8, 9, 10, 11))
    centre = (rng.randrange(2, N-2), rng.randrange(2, N-2))
    extra = {(rng.randrange(N), rng.randrange(N)) for _ in range(rng.randrange(0, 5))}
    g, t = pinwheel1(N=N, centre=centre, extra=extra)
    if not g.free(*t): continue
    s = rng.choice([c for c in g.free_cells() if c != t])
    M = Model(g, s)
    if t not in M.component(): continue
    seen_orders = set()
    for order in rand_fail(M, s, t, rng, want=per):
        visited, closed, scans, pending = replay_scans(g, s, order)
        assert not pending
        unvis, bad = check_lemma(g, s, visited, closed, scans)
        assert t in unvis
        tested += 1
        edges += sum(1 for p in visited for u in [(1,0),(-1,0),(0,1),(0,-1)]
                     if g.free(p[0]+u[0], p[1]+u[1]) and (p[0]+u[0], p[1]+u[1]) in unvis)
        if bad:
            viol += 1; print('LEMMA VIOLATION', N, centre, sorted(g.blocked), s, order, bad, flush=True)
print(f'terminal configs tested {tested}, frontier edges {edges}, violations {viol}')
