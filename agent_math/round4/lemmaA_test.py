"""Test of LEMMA A (cell-closing WA*, any w, any tie rule):
  Let pi = (x_0,e_0),...,(x_i,e_i) be a J-path from (s,0) such that for every j < i the cell x_j is closed (at some
  time) with arrival direction delta(x_j) = e_j.  Then x_i is closed, and its closing g satisfies g(x_i) <= w * P_i(pi),
  P_i = cost of pi.
Operationally: build the executed-scan graph G (arc y->x whenever the expansion of y ran a scan that RETURNED x,
whether or not the arrival was accepted), keep only arcs y->x whose scan direction equals delta(x) (direction from
parent(x) to x) -- except that the LAST arc into the cell under test is unrestricted -- and compute the cheapest
such path from s to every closed x.  Check g(x) <= w*P_min(x) + 1e-9.
Also tested (expected to FAIL for w>1, i.e. the direction restriction is essential): same with all arcs."""
import sys, math, random, heapq
sys.path.insert(0, '/home/claude/jps-wa/ref')
from jpswa import Grid, CanonicalJPS, octile, SQ2, DIRS8

class InstrJPS(CanonicalJPS):
    def search(self):
        s, t, w = self.s, self.t, self.w
        gval = {s: 0.0}; parent = {s: None}; closed = set(); import itertools
        counter = itertools.count(); open_ = []
        self.arcs = []   # (y, x, dir, cost)
        self.closing = {}  # x -> (g, parent)
        def push(cell, gc):
            c = next(counter); f = gc + w * octile(cell[0], cell[1], t[0], t[1])
            key = {'hig': (f, -gc, c), 'log': (f, gc, c), 'fifo': (f, c), 'lifo': (f, -c),
                   'rand': (self.rng.random(), c), 'greedy': (octile(cell[0], cell[1], t[0], t[1]), -gc, c)}[self.tie]
            heapq.heappush(open_, (key, cell, gc))
        push(s, 0.0)
        while open_:
            key, n, gn = heapq.heappop(open_)
            if n in closed or gn > gval[n] + 1e-12: continue
            closed.add(n); self.closing[n] = (gn, parent[n])
            if n == t: return gn
            x, y = n; p = parent[n]
            dx = dy = 0
            if p is not None: dx = (x > p[0]) - (x < p[0]); dy = (y > p[1]) - (y < p[1])
            for ddx, ddy in self.successor_dirs(x, y, dx, dy):
                r = self.jump(x, y, ddx, ddy, gn)
                if r is None: continue
                jx, jy, jg = r; j = (jx, jy)
                self.arcs.append((n, j, (ddx, ddy), jg - gn))
                if j in closed: continue
                if jg < gval.get(j, math.inf) - 1e-12:
                    gval[j] = jg; parent[j] = n; push(j, jg)
        return math.inf

def dirof(x, p):
    return ((x[0] > p[0]) - (x[0] < p[0]), (x[1] > p[1]) - (x[1] < p[1]))

def check(J, w, restrict=True):
    """returns number of violations of g(x) <= w*Pmin(x)."""
    closing = J.closing
    # Dijkstra over arcs; a node is (cell).  Restricted: an arc y->x may be used as an INTERIOR arc only if
    # dir == delta(x); as the final arc always.  Do two-layer: dist_int[x] = cheapest path to x using only
    # direction-consistent arcs (so that x can be continued); final bound for x = min over arcs y->x of dist_int[y]+c.
    s = J.s
    adj = {}
    for y, x, d, c in J.arcs:
        adj.setdefault(y, []).append((x, d, c))
    dist_int = {s: 0.0}; pq = [(0.0, s)]
    while pq:
        dd, y = heapq.heappop(pq)
        if dd > dist_int.get(y, math.inf) + 1e-12: continue
        for x, d, c in adj.get(y, []):
            if x not in closing or x == s: continue
            if restrict and dirof(x, closing[x][1]) != d: continue
            nd = dd + c
            if nd < dist_int.get(x, math.inf) - 1e-12:
                dist_int[x] = nd; heapq.heappush(pq, (nd, x))
    bound = {}
    for y, x, d, c in J.arcs:
        if y in dist_int and x in closing:
            bound[x] = min(bound.get(x, math.inf), dist_int[y] + c)
    viol = 0; worst = 0.0
    for x, (g, p) in closing.items():
        if x == s: continue
        if x not in bound: viol += 1; continue   # closed cell with no executed arc?? impossible
        if g > w * bound[x] + 1e-9: viol += 1; worst = max(worst, g - w * bound[x])
    return viol, worst

if __name__ == '__main__':
    rnd = random.Random(4)
    from collections import defaultdict
    tot = defaultdict(lambda: [0, 0, 0.0])
    for it in range(1500):
        N = rnd.randint(5, 14); dens = rnd.choice([0.1, 0.2, 0.3, 0.4])
        cells = [(x, y) for x in range(N) for y in range(N)]
        bl = [c for c in cells if rnd.random() < dens]
        g = Grid(N, N, bl); fr = [c for c in cells if g.free(c[0], c[1])]
        if len(fr) < 2: continue
        s, t = rnd.sample(fr, 2)
        for w in (1.0, 1.5, 2.0, 5.0, 1e6):
            for tie in ('hig', 'log', 'fifo', 'lifo', 'rand', 'greedy'):
                J = InstrJPS(g, s, t, w, tie); J.search()
                for restrict in (True, False):
                    v, worst = check(J, w, restrict)
                    k = (restrict, w, tie); tot[k][0] += len(J.closing) - 1; tot[k][1] += v; tot[k][2] = max(tot[k][2], worst)
    for k in sorted(tot, key=str):
        print(('LEMMA A (dir-consistent)' if k[0] else 'unrestricted (all arcs)'), 'w=%g tie=%-6s' % k[1:], 'closings %d violations %d worst %.3f' % tuple(tot[k]))
