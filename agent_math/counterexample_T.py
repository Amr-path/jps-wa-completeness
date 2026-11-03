"""THE COUNTEREXAMPLE TO (T)  (round 2).

8x8 grid, 4 blocked cells (a 'pinwheel' around the central 2x2 block), start s=(0,2):
    ........
    ...#....
    S.......
    ...**.#.      * = the four cells (3,3),(4,3),(3,4),(4,4) that are reachable but never visited
    .#.**...
    ........
    ....#...
    ........
Some expansion order of canonical JPS with cell-closing (exactly ref/jpswa.py's loop, parent = best-g
generator, stale entries skipped, closed cells never re-expanded) empties Open while the central 2x2 block
is never stepped on.  This script (1) finds such an order by a DFS over pop orders that prunes any branch
visiting the block (faithful model with g-values), (2) replays it with the REFERENCE jump/successor code
and an instrumented Grid.legal to record every stepped-on cell, (3) prints the trace, (4) checks WA*
realisability (target in the block, several w, adversarial ties) -> not realisable for this grid."""
import sys, math
sys.path.insert(0, '/home/claude/jps-wa/ref')
from jpswa import Grid, CanonicalJPS, grid_to_str, dijkstra, octile
from pinwheel_verify import faithful_dfs
from pinwheel_verify2 import RecGrid, run
from pinwheel_wastar import wastar_adversary
from common import Model

BLOCKED = [(3, 1), (6, 3), (1, 4), (4, 6), (1, 6)]
S = (0, 2)
HOLE = [(3, 3), (4, 3), (3, 4), (4, 4)]
D = {(1, 0): 'E', (-1, 0): 'W', (0, 1): 'S', (0, -1): 'N', (1, 1): 'SE', (1, -1): 'NE', (-1, 1): 'SW', (-1, -1): 'NW', (0, 0): '0'}

if __name__ == '__main__':
    g = Grid(8, 8, BLOCKED)
    print(grid_to_str(g, S, None, HOLE))
    res, order, closed = faithful_dfs(g, S, HOLE)
    print('faithful DFS:', res)
    cells = [o[0] for o in order]
    rg = RecGrid(8, 8, BLOCKED)
    visited, cl, gval, parent = run(rg, S, cells)
    reach = [c for c in g.free_cells() if dijkstra(g, S, c) < math.inf]
    missing = sorted(set(reach) - visited)
    print('reachable', len(reach), 'visited', len(visited), 'NEVER VISITED:', missing)
    assert set(missing) == set(HOLE)
    # trace
    M = Model(g, S)
    print('\npop#  cell   arrival  g      succ-dirs        jump points returned (dir)  [dropped = already closed]')
    cs = set()
    for i, n in enumerate(cells):
        p = parent[n]
        d = (0, 0) if p is None else ((n[0] > p[0]) - (n[0] < p[0]), (n[1] > p[1]) - (n[1] < p[1]))
        jps, vis = M.scan(n, d); cs.add(n)
        rets = [f'{y}<-{D[e]}' + (' dropped' if y in cs else '') for (y, e) in jps]
        print(f'{i:3d}  {n}  {D[d]:2s}  {gval[n]:6.3f}  {[D[e] for e in M.succ_dirs(n, d)]}  {rets}')
    print('\nORDER =', cells)
    # WA* realisability on this grid
    print('\nWA* (target in the block, adversarial ties):')
    for t in HOLE:
        out = []
        for w in (1.0, 1.1, 1.25, 1.5, 2.0, 3.0, 5.0, 10.0, 100.0, 1e6):
            r, o = wastar_adversary(g, S, t, w, limit=500_000)
            out.append(f'{w}:{r}')
        print(' t=', t, ' '.join(out))
