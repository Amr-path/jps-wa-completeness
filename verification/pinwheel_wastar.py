"""Is the pinwheel failure realisable under a Weighted A* ordering?  For each target t in the hole and each
weight w, run (1) the reference CanonicalJPS with the four built-in tie rules, (2) an exhaustive adversary
over orders that is RESTRICTED to WA*: the popped non-stale entry must have minimal f_w = g + w*h(t)
among the open entries (ties, within 1e-9, broken adversarially).  Failure = open empties without t popped.
Model is the faithful one (g-values, parent = best-g generator, cell closing)."""
import sys, math
sys.path.insert(0, '/path/to/jps-wa/ref')
from jpswa import Grid, CanonicalJPS, grid_to_str, octile, SQ2
from pinwheel import build

def wastar_adversary(grid, s, t, w, limit=3_000_000):
    J = CanonicalJPS(grid, s, t, w, 'hig')
    def expand(x, parent, gx):
        if parent is None: d = (0, 0)
        else: d = ((x[0] > parent[0]) - (x[0] < parent[0]), (x[1] > parent[1]) - (x[1] < parent[1]))
        out = []
        for e in J.successor_dirs(x[0], x[1], d[0], d[1]):
            r = J.jump(x[0], x[1], e[0], e[1], gx)
            if r is not None: out.append(r)
        return out
    start = (frozenset(), ((s, 0.0, None),))
    seen = set(); stack = [(start, [])]; n = 0
    while stack:
        (closed, open_), order = stack.pop()
        key = (closed, open_)
        if key in seen: continue
        seen.add(key); n += 1
        if n > limit: return 'limit', None
        if not open_: return 'FAIL', order
        od = {c: (g, p) for c, g, p in open_}
        fmin = min(g + w * octile(*c, *t) for c, (g, p) in od.items())
        for x, (gx, px) in od.items():
            if gx + w * octile(*x, *t) > fmin + 1e-9: continue
            if x == t: continue              # t popped: success along this branch
            jps = expand(x, px, gx)
            nc = closed | {x}
            no = dict(od); del no[x]
            for (jx, jy, jg) in jps:
                j = (jx, jy)
                if j in nc: continue
                if jg < no.get(j, (math.inf,))[0] - 1e-12: no[j] = (jg, x)
            stack.append(((nc, tuple(sorted((c, g, p) for c, (g, p) in no.items()))), order + [x]))
    return 'complete', None

if __name__ == '__main__':
    g, s, hole, sh = build()
    ws = [1.0, 1.01, 1.1, 1.2, 1.3, 1.5, 1.7, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0, 10.0, 20.0, 50.0, 100.0, 1000.0]
    # (1) built-in tie rules
    fails = 0
    for t in hole:
        for w in ws:
            for tie in ('hig', 'log', 'fifo', 'lifo'):
                c, path = CanonicalJPS(g, s, t, w, tie).search()
                if c == math.inf: fails += 1; print('BUILTIN FAIL', t, w, tie)
    print('built-in tie rules: failures', fails)
    # (2) adversarial tie-breaking within WA*
    for t in hole:
        for w in ws:
            res, order = wastar_adversary(g, s, t, w)
            print(f't={t} w={w}: {res}' + (f' order={order}' if order else ''))
            sys.stdout.flush()
