"""Lemma tests with the REFERENCE implementation (instrumented subclass; same loop, same jump/successor_dirs).
L1  (w=1, any tie rule): a cell is never closed with a g larger than ANY arrival ever generated for it
    (dropped arrivals never improve).            Expected: holds for w=1, violated for w>1.
L1' (w=1): closing g equals the exact shortest-path distance dist(s,cell).   Expected: holds.
L2  (any w): an improving dropped arrival generated from x satisfies g_new >= g_closed - (w-1)*cost(x->cell)
    whenever x was in Open when the cell closed (we test the weaker: for all x popped after the cell closed).
L3  (structure of terminal failing configurations, from min_slack orders): every visited cell p with a legal
    straight move u into an unvisited reachable cell is CLOSED, has a straight arrival d perpendicular to u,
    p-d+u is free, and p is forced on side -u (p-d-u blocked, p-u free).
"""
import sys, math, random
sys.path.insert(0, '/path/to/jps-wa/verification/round3')
from core import *

class Instr(CanonicalJPS):
    def search(self):
        s, t, w = self.s, self.t, self.w
        gval = {s: 0.0}; parent = {s: None}; closed = {}
        self.arrivals = {s: [(0.0, None, 0)]}   # cell -> list of (g, generator, pop-index of generator)
        import heapq, itertools
        counter = itertools.count(); open_ = []
        def push(cell, gc):
            c = next(counter); f = gc + w * octile(cell[0], cell[1], t[0], t[1])
            key = {'hig': (f, -gc, c), 'log': (f, gc, c), 'fifo': (f, c), 'lifo': (f, -c),
                   'rand': (self.rng.random(), c), 'greedy': (octile(cell[0], cell[1], t[0], t[1]), -gc, c)}[self.tie]
            heapq.heappush(open_, (key, cell, gc))
        push(s, 0.0); k = 0
        while open_:
            key, n, gn = heapq.heappop(open_)
            if n in closed or gn > gval[n] + 1e-12: continue
            closed[n] = (gn, k); k += 1
            if n == t: break
            x, y = n; p = parent[n]
            dx = dy = 0
            if p is not None: dx = (x > p[0]) - (x < p[0]); dy = (y > p[1]) - (y < p[1])
            for ddx, ddy in self.successor_dirs(x, y, dx, dy):
                r = self.jump(x, y, ddx, ddy, gn)
                if r is None: continue
                j = (r[0], r[1]); jg = r[2]
                self.arrivals.setdefault(j, []).append((jg, n, k - 1))
                if j in closed: continue
                if jg < gval.get(j, math.inf) - 1e-12:
                    gval[j] = jg; parent[j] = n; push(j, jg)
        self.closed = closed; self.gval = gval
        return closed

def rand_grid(rng, N, p):
    bl = [(x, y) for x in range(N) for y in range(N) if rng.random() < p]
    return Grid(N, N, bl)

rng = random.Random(7)
viol = {'L1_w1': 0, 'L1p_w1': 0, 'L1_wgt1': 0, 'L2': 0}; tests = {'L1_w1': 0, 'L1p_w1': 0, 'L1_wgt1': 0, 'L2': 0}
for it in range(400):
    N = rng.choice((6, 8, 10)); g = rand_grid(rng, N, rng.choice((0.1, 0.2, 0.3)))
    free = g.free_cells()
    if len(free) < 4: continue
    s, t = rng.sample(free, 2)
    if dijkstra(g, s, t) == math.inf: continue
    for w in (1.0, 1.0, 1.5, 2.0, 5.0, 1e6):
        for tie in ('hig', 'log', 'fifo', 'lifo', 'rand', 'greedy'):
            if tie == 'rand': continue   # 'rand' is not a WA* ordering
            if w > 1 and tie == 'greedy': continue
            J = Instr(g, s, t, w, tie); closed = J.search()
            for c, (gc, kc) in closed.items():
                arr = J.arrivals.get(c, [])
                gmin = min(a[0] for a in arr)
                if w == 1.0:
                    tests['L1_w1'] += 1; tests['L1p_w1'] += 1
                    if gc > gmin + 1e-9: viol['L1_w1'] += 1
                    if abs(gc - dijkstra(g, s, c)) > 1e-9: viol['L1p_w1'] += 1
                else:
                    tests['L1_wgt1'] += 1
                    if gc > gmin + 1e-9: viol['L1_wgt1'] += 1
                    for (ga, gen, kgen) in arr:
                        if gen is not None and kgen > kc and ga < gc - 1e-9:   # improving arrival from x popped after c closed
                            tests['L2'] += 1
                            cost = ga - closed[gen][0]
                            if ga < gc - (w - 1) * cost - 1e-9: viol['L2'] += 1
print('tests', tests); print('violations', viol)

# L3 on failing orders of several instances
def check_L3(grid, s, t, order):
    M = Model(grid, s); comp = M.component()
    gval = {s: 0.0}; parent = {s: None}; closed = set(); open_ = {s: 0.0}; visited = {s}; arr = {}
    for x in order:
        gx = open_.pop(x); d = M.dir_from(x, parent[x]); closed.add(x); arr[x] = d
        jps, vis = M.expand(x, d); visited |= vis
        for (j, c) in jps:
            if j in closed: continue
            if gx + c < gval.get(j, math.inf) - 1e-12: gval[j] = gx + c; parent[j] = x; open_[j] = gx + c
    assert not open_
    U = comp - visited; bad = 0; pairs = 0
    for p in visited:
        for u in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            q = (p[0] + u[0], p[1] + u[1])
            if q in U:
                pairs += 1
                ok = p in closed and arr[p] != (0, 0) and arr[p][0] * u[0] + arr[p][1] * u[1] == 0 and (arr[p][0] == 0 or arr[p][1] == 0)
                if ok:
                    d = arr[p]
                    ok = grid.free(p[0] - d[0] + u[0], p[1] - d[1] + u[1]) and (not grid.free(p[0] - d[0] - u[0], p[1] - d[1] - u[1])) and grid.free(p[0] - u[0], p[1] - u[1])
                if not ok: bad += 1
    return len(U), pairs, bad

insts = [(Grid(8, 8, [(3, 1), (6, 3), (1, 4), (4, 6), (1, 6)]), (0, 2), (3, 3)),
         (pinwheel1(N=9)[0], (8, 8), (4, 4)), (pinwheel1(N=9)[0], (0, 0), (4, 4)), (pinwheel1(N=9)[0], (1, 1), (4, 4)),
         (Grid(8, 8, [(0, 4), (0, 6), (0, 7), (1, 1), (1, 4), (1, 6), (2, 1), (3, 1), (4, 6), (6, 3), (6, 7), (7, 1), (7, 7)]), (3, 0), (3, 4))]
for grid, s, t in insts:
    for w in (1.0, 3.0):
        st, v, order = min_slack(grid, s, t, w, cap=300_000)
        if order: print('L3', s, t, w, 'slack', round(v, 3), '(|U|, boundary pairs, violations) =', check_L3(grid, s, t, order))
