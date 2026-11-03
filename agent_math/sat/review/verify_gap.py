"""Replay a visited-but-not-pushed run with the REFERENCE CanonicalJPS.jump / successor_dirs (jpswa.py), popping in the
given order regardless of f.  Confirms: Open empties, t never pushed/popped, although t was stepped on."""
import sys, math
sys.path.insert(0, '/home/claude/jps-wa/ref'); sys.path.insert(0, '/home/claude/jps-wa/agent_math/round3')
from jpswa import Grid, CanonicalJPS
from core import ReplayJPS
N, bl, s, t = 7, [(1, 2), (2, 5), (4, 1), (5, 4)], (6, 4), (3, 3)
order = [(6, 4), (6, 5), (5, 6), (1, 6), (0, 5), (0, 1), (2, 1), (2, 3), (1, 4), (3, 4), (4, 5), (4, 3), (6, 3), (5, 2), (5, 0), (3, 6), (3, 2), (3, 0), (1, 0), (0, 3)]
grid = Grid(N, N, bl)
J = ReplayJPS(grid, s, t, 1.0, order)   # reference jump (records visited), reference successor_dirs
gval = {s: 0.0}; parent = {s: None}; closed = set(); open_ = {s}
stepped = []
for x in order:
    assert x in open_ and x not in closed, x
    open_.discard(x); closed.add(x)
    p = parent[x]; d = (0, 0) if p is None else ((x[0] > p[0]) - (x[0] < p[0]), (x[1] > p[1]) - (x[1] < p[1]))
    for e in J.successor_dirs(x[0], x[1], d[0], d[1]):
        J.visited = set()
        r = J.jump(x[0], x[1], e[0], e[1], gval[x])
        if t in J.visited: stepped.append((x, d, e, None if r is None else (r[0], r[1])))
        if r is None: continue
        j = (r[0], r[1])
        if j in closed: continue
        if r[2] < gval.get(j, math.inf) - 1e-12:
            gval[j] = r[2]; parent[j] = x; open_.add(j)
print('open at end:', open_, ' t pushed:', t in gval, ' t closed:', t in closed)
print('scans that stepped on t (cell, arrival dir, scan dir, returned):', stepped)
for sc in stepped:
    y = sc[3]; print('  returned cell', y, 'closed with arrival', (lambda p: None if p is None else ((y[0]>p[0])-(y[0]<p[0]), (y[1]>p[1])-(y[1]<p[1])))(parent.get(y)), 'position in order', order.index(y) if y in order else None, 'scan from', sc[0], 'at position', order.index(sc[0]))
print(grid.blocked)
for y in range(N):
    print(''.join('#' if (x, y) in grid.blocked else ('s' if (x, y) == s else ('t' if (x, y) == t else ('.' if (x, y) in closed else 'o'))) for x in range(N)))
