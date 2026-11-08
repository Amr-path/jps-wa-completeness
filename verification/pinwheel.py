"""Round 2: attempt to realise the 4-cycle of the strip recursion ("pinwheel").
Grid coordinates (x,y), y up in the design; we shift to non-negative and flip nothing (the
algorithm is symmetric under all grid symmetries).  Hole H = 2x2 block that the four rays spiral around.
Targeted adversary: DFS over expansion orders that prunes every state visiting a hole cell."""
import sys
sys.path.insert(0, '/path/to/jps-wa/ref')
from jpswa import Grid, grid_to_str
from common import Model

def rot(c):            # 90 deg rotation about (1.5,0.5): (x,y) -> (y+1, 2-x)
    x, y = c; return (y + 1, 2 - x)

def orbit(c):
    out = []
    for _ in range(4): out.append(c); c = rot(c)
    return out

def build(extra_blocked=(), extra_free=()):
    base = [(-1, 1), (-1, 2), (-1, 3)]            # arm-0 blocked cells (see report)
    blocked = set()
    for b in base:
        for c in orbit(b): blocked.add(c)
    for b in extra_blocked:
        for c in orbit(b): blocked.add(c)
    for b in extra_free:
        for c in orbit(b): blocked.discard(c)
    # grid window x in [-2,5], y in [-3,4]  -> shift by (+2,+3)
    sh = lambda c: (c[0] + 2, c[1] + 3)
    g = Grid(8, 8, [sh(c) for c in blocked])
    s = sh((-2, -1))
    hole = [sh(c) for c in [(1, 0), (2, 0), (1, 1), (2, 1)]]
    return g, s, hole, sh

def targeted(M, hole, limit=2_000_000):
    """DFS over orders, pruning states whose visited set touches the hole.  Returns a terminal closed dict or None."""
    hole = set(hole)
    start = (frozenset(), frozenset({(M.s, (0, 0))}))
    seen = set(); stack = [start]; n = 0
    while stack:
        st = stack.pop()
        if st in seen: continue
        seen.add(st); n += 1
        if n > limit: return 'limit', None
        closed, open_ = st
        cc = {c for c, _ in closed}
        pend = [(x, d) for (x, d) in open_ if x not in cc]
        if not pend:
            return 'found', dict(closed)
        for (x, d) in pend:
            jps, vis = M.scan(x, d)
            if vis & hole: continue
            if x in hole: continue
            nc = closed | {(x, d)}
            no = set(e for e in open_ if e[0] != x)
            for (y, e) in jps:
                if y not in cc: no.add((y, e))
            stack.append((nc, frozenset(no)))
    return 'none', None

if __name__ == '__main__':
    g, s, hole, sh = build()
    print(grid_to_str(g, s, None, hole))
    M = Model(g, s)
    comp = M.component()
    print('component', len(comp), 'hole in comp', all(h in comp for h in hole))
    res, cd = targeted(M, hole)
    print(res)
    if cd:
        V = {s}
        for x, d in cd.items(): V |= M.scan(x, d)[1]
        print('unvisited', sorted(comp - V))
        print('closed', cd)
