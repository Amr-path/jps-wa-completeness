"""Independent re-verification of the pinwheel counterexample using ONLY the reference code paths
(CanonicalJPS.successor_dirs and CanonicalJPS.jump from ref/jpswa.py).  Visited cells are recorded by
instrumenting Grid.legal: the reference jump steps onto (x+dx,y+dy) exactly when legal() returns True.
The search loop is the reference loop with the pop order prescribed (= adversarial tie-breaking)."""
import sys, math
sys.path.insert(0, '/path/to/jps-wa/ref')
import jpswa
from jpswa import Grid, CanonicalJPS, grid_to_str, dijkstra
from pinwheel import build

ORDER = [(0, 2), (4, 2), (4, 0), (0, 7), (2, 7), (7, 7), (7, 5), (7, 0), (5, 0), (5, 4), (7, 4), (6, 5),
         (6, 4), (5, 1), (4, 1), (3, 5), (3, 7), (3, 6), (2, 6), (2, 3), (1, 3), (1, 2), (0, 3), (0, 0)]

class RecGrid(Grid):
    def __init__(self, *a):
        super().__init__(*a); self.stepped = set()
    def legal(self, x, y, dx, dy):
        ok = super().legal(x, y, dx, dy)
        if ok: self.stepped.add((x + dx, y + dy))
        return ok

def run(grid, s, order, t=(-99, -99)):
    J = CanonicalJPS(grid, s, t, 1.0, 'hig')
    gval = {s: 0.0}; parent = {s: None}; closed = set(); open_ = {s: 0.0}
    for n in order:
        assert n in open_ and n not in closed, ('illegal pop', n)
        gn = open_.pop(n); closed.add(n)
        x, y = n; p = parent[n]
        if p is None: dx = dy = 0
        else: dx = (x > p[0]) - (x < p[0]); dy = (y > p[1]) - (y < p[1])
        for ddx, ddy in J.successor_dirs(x, y, dx, dy):
            r = J.jump(x, y, ddx, ddy, gn)          # reference jump
            if r is None: continue
            jx, jy, jg = r; j = (jx, jy)
            if j in closed: continue
            if jg < gval.get(j, math.inf) - 1e-12:
                gval[j] = jg; parent[j] = n; open_[j] = jg
    assert not open_, ('open not empty', open_)
    return grid.stepped | {s}, closed, gval, parent

if __name__ == '__main__':
    g0, s, hole, sh = build()
    g = RecGrid(8, 8, list(g0.blocked))
    visited, closed, gval, parent = run(g, s, ORDER)
    reach = [c for c in g.free_cells() if dijkstra(g, s, c) < math.inf]
    missing = sorted(set(reach) - visited)
    print(grid_to_str(g, s, None, missing))
    print('reachable', len(reach), 'visited', len(visited), 'never visited:', missing)
    print('parent/arrival of each closed cell:')
    for n in ORDER:
        p = parent[n]
        print(f'  {n} g={gval[n]:.3f} parent={p}')
