"""Gap check: 'visited' vs 'pushed'.  The SAT encoding (and core.py) count a run as a success as soon as some executed
scan STEPS ON t -- including a sub-jump of a diagonal scan.  In the reference algorithm a sub-jump that reaches t makes
the diagonal return its current cell y (not t); t is pushed only if y is later expanded with a direction whose
successors contain that straight direction.  This script runs the reference semantics exactly (jumps stop at t, as in
jpswa.py) with success := t is RETURNED BY A TOP-LEVEL SCAN (hence pushed), over (a) all pop orders and (b) WA*-consistent
pop orders, and looks for instances where t is stepped on but never pushed (Open empties).
usage: python3 pushed_adversary.py seed n_inst"""
import sys, random, math
sys.path.insert(0, '/path/to/jps-wa/ref'); sys.path.insert(0, '/path/to/jps-wa/verification/round3')
from jpswa import Grid, CanonicalJPS, octile, dijkstra, SQ2
from core import pinwheel1
EPS = 1e-9


class ModelT:
    """expand(x, d) -> (list of (cell, cost), visited) with the REAL target: scans stop at t (reference jump)."""
    def __init__(self, grid, s, t):
        self.J = CanonicalJPS(grid, s, t, 1.0, 'hig'); self.grid = grid; self.t = t; self.cache = {}

    def dir_from(self, x, p):
        if p is None: return (0, 0)
        return ((x[0] > p[0]) - (x[0] < p[0]), (x[1] > p[1]) - (x[1] < p[1]))

    def expand(self, x, d):
        key = (x, d)
        if key in self.cache: return self.cache[key]
        J = self.J; g = self.grid; vis = set(); out = []
        def jr(x0, y0, dx, dy, gg):
            while True:
                if not g.legal(x0, y0, dx, dy): return None
                x0 += dx; y0 += dy; gg += SQ2 if (dx and dy) else 1.0; vis.add((x0, y0))
                if (x0, y0) == self.t: return (x0, y0, gg)
                if dx and dy:
                    if jr(x0, y0, dx, 0, gg) is not None or jr(x0, y0, 0, dy, gg) is not None: return (x0, y0, gg)
                elif J.has_forced(x0, y0, dx, dy): return (x0, y0, gg)
        for e in J.successor_dirs(x[0], x[1], d[0], d[1]):
            r = jr(x[0], x[1], e[0], e[1], 0.0)
            if r is not None: out.append(((r[0], r[1]), r[2]))
        self.cache[key] = (tuple(out), frozenset(vis))
        return self.cache[key]


def adversary(grid, s, t, w=None, limit=300_000):
    """w=None: any pop order; else WA*-consistent.  Returns ('FAIL_unvisited'|'FAIL_visited_not_pushed', order) or
    ('complete'|'limit', None).  Failure = Open empties with t never pushed (t pushed <=> returned by a top-level scan)."""
    M = ModelT(grid, s, t)
    h = lambda c: octile(c[0], c[1], t[0], t[1])
    start = (frozenset(), ((s, 0.0, None),), False)
    seen = set(); stack = [(start, [])]; n = 0
    while stack:
        (closed, open_, tv), order = stack.pop()
        key = (closed, open_, tv)
        if key in seen: continue
        seen.add(key); n += 1
        if n > limit: return 'limit', None
        if not open_: return ('FAIL_visited_not_pushed' if tv else 'FAIL_unvisited'), order
        od = {c: (g, p) for c, g, p in open_}
        if t in od: continue   # t pushed: success branch
        fmin = min(g + w * h(c) for c, (g, p) in od.items()) if w is not None else None
        for x, (gx, px) in od.items():
            if w is not None and gx + w * h(x) > fmin + EPS: continue
            jps, vis = M.expand(x, M.dir_from(x, px))
            nc = closed | {x}; no = dict(od); del no[x]
            for (j, c) in jps:
                if j in nc: continue
                if gx + c < no.get(j, (math.inf,))[0] - 1e-12: no[j] = (gx + c, x)
            stack.append(((nc, tuple(sorted((c, g, p) for c, (g, p) in no.items())), tv or (t in vis)), order + [x]))
    return 'complete', None


def main(seed, n_inst):
    rng = random.Random(seed)
    stats = {}
    found = []
    tried = 0
    while tried < n_inst:
        N = rng.choice([6, 7, 7])
        t = (N // 2, N // 2) if rng.random() < 0.5 else (rng.randrange(N), rng.randrange(N))
        if rng.random() < 0.6:
            g0, _ = pinwheel1(N=N, centre=t); bl = set(g0.blocked)
            for _ in range(rng.randrange(0, 5)): bl.add((rng.randrange(N), rng.randrange(N)))
        else:
            bl = {(x, y) for x in range(N) for y in range(N) if rng.random() < rng.choice([0.15, 0.3])}
        bl.discard(t); s = (rng.randrange(N), rng.randrange(N))
        if s in bl or s == t: continue
        grid = Grid(N, N, bl)
        if math.isinf(dijkstra(grid, s, t)): continue
        tried += 1
        r, order = adversary(grid, s, t, None)
        stats[r] = stats.get(r, 0) + 1
        if r == 'FAIL_visited_not_pushed':
            found.append((N, sorted(bl), s, t, 'any', order))
            print('VISITED-BUT-NOT-PUSHED (any order):', N, sorted(bl), s, t, order, flush=True)
        for w in (1.0, 2.0, 5.0):
            rw, ow = adversary(grid, s, t, w)
            stats[('wa', rw)] = stats.get(('wa', rw), 0) + 1
            if rw.startswith('FAIL'):
                found.append((N, sorted(bl), s, t, w, ow))
                print('WA* FAILURE under pushed criterion:', rw, N, sorted(bl), s, t, w, ow, flush=True)
    print('tried', tried, 'stats', stats)
    print('found', len(found))


if __name__ == '__main__':
    main(int(sys.argv[1]), int(sys.argv[2]))
