"""Verify the pinwheel counterexample with a FAITHFUL re-implementation of jpswa.CanonicalJPS.search
(g-values, parent = best-g generator, stale-entry skipping, closed-cell policy) where the only freedom is
WHICH cell to pop next among cells having a non-stale open entry.  The order is taken from a DFS over
orders that prunes states visiting the hole, run on the *faithful* model (so g-updates are respected)."""
import sys, math
sys.path.insert(0, '/path/to/jps-wa/ref')
from jpswa import Grid, CanonicalJPS, grid_to_str, SQ2
from pinwheel import build
from common import Model

def faithful_dfs(grid, s, hole, limit=5_000_000):
    """State: (closed frozenset of cells, tuple of (cell,g,parent) for open cells with best g).
    Expansion of x uses direction from its best-g parent.  Prune when a scan touches the hole."""
    J = CanonicalJPS(grid, s, (-99, -99), 1.0, 'hig')
    hole = set(hole)
    def expand(x, parent, gx):
        if parent is None: d = (0, 0)
        else: d = ((x[0] > parent[0]) - (x[0] < parent[0]), (x[1] > parent[1]) - (x[1] < parent[1]))
        out = []; vis = set()
        for e in J.successor_dirs(x[0], x[1], d[0], d[1]):
            # replicate jump but collect visited
            def jr(x0, y0, dx, dy, gg):
                while True:
                    if not grid.legal(x0, y0, dx, dy): return None
                    x0 += dx; y0 += dy; gg += SQ2 if (dx and dy) else 1.0; vis.add((x0, y0))
                    if dx and dy:
                        if jr(x0, y0, dx, 0, gg) is not None or jr(x0, y0, 0, dy, gg) is not None: return (x0, y0, gg)
                    elif J.has_forced(x0, y0, dx, dy): return (x0, y0, gg)
            r = jr(x[0], x[1], e[0], e[1], gx)
            if r is not None: out.append(r)
        return out, vis, d
    # open: dict cell -> (g, parent)
    start = (frozenset(), ((s, 0.0, None),))
    seen = set(); stack = [(start, [])]; n = 0
    while stack:
        (closed, open_), order = stack.pop()
        key = (closed, open_)
        if key in seen: continue
        seen.add(key); n += 1
        if n > limit: return 'limit', None, None
        if not open_:
            return 'found', order, closed
        od = {c: (g, p) for c, g, p in open_}
        for x, (gx, px) in od.items():
            jps, vis, d = expand(x, px, gx)
            if vis & hole or x in hole: continue
            nc = closed | {x}
            no = dict(od); del no[x]
            for (jx, jy, jg) in jps:
                j = (jx, jy)
                if j in nc: continue
                if jg < no.get(j, (math.inf,))[0] - 1e-12: no[j] = (jg, x)
            stack.append(((nc, tuple(sorted((c, g, p) for c, (g, p) in no.items()))), order + [(x, d, round(gx, 3))]))
    return 'none', None, None

def replay(grid, s, order):
    """Run the reference algorithm's loop verbatim, except pops follow `order` (list of cells)."""
    J = CanonicalJPS(grid, s, (-99, -99), 1.0, 'hig')
    gval = {s: 0.0}; parent = {s: None}; closed = set(); visited = {s}
    open_ = {s: 0.0}
    for cell in order:
        assert cell in open_ and cell not in closed, cell
        gn = open_.pop(cell); closed.add(cell)
        x, y = cell; p = parent[cell]
        if p is None: dx = dy = 0
        else: dx = (x > p[0]) - (x < p[0]); dy = (y > p[1]) - (y < p[1])
        for ddx, ddy in J.successor_dirs(x, y, dx, dy):
            # jump with visited tracking
            def jr(x0, y0, ex, ey, gg):
                while True:
                    if not grid.legal(x0, y0, ex, ey): return None
                    x0 += ex; y0 += ey; gg += SQ2 if (ex and ey) else 1.0; visited.add((x0, y0))
                    if ex and ey:
                        if jr(x0, y0, ex, 0, gg) is not None or jr(x0, y0, 0, ey, gg) is not None: return (x0, y0, gg)
                    elif J.has_forced(x0, y0, ex, ey): return (x0, y0, gg)
            r = jr(x, y, ddx, ddy, gn)
            if r is None: continue
            jx, jy, jg = r; j = (jx, jy)
            if j in closed: continue
            if jg < gval.get(j, math.inf) - 1e-12:
                gval[j] = jg; parent[j] = cell; open_[j] = jg
    assert not open_, open_
    return visited, closed, gval, parent

if __name__ == '__main__':
    g, s, hole, sh = build()
    M = Model(g, s); comp = M.component()
    res, order, closed = faithful_dfs(g, s, hole)
    print('faithful DFS:', res)
    if order:
        print('order (cell, arrival dir, g):');
        for o in order: print('  ', o)
        visited, cl, gval, parent = replay(g, s, [o[0] for o in order])
        print('replay: visited', len(visited), 'of component', len(comp))
        print('unvisited reachable cells:', sorted(comp - visited))
        print(grid_to_str(g, s, None, sorted(comp - visited)))
