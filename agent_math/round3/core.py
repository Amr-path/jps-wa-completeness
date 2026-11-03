"""Round 3 core tooling.

Faithful model of ref/jpswa.py CanonicalJPS.search (cell closing, parent = best-g generator, stale entries
skipped, closed cells never re-expanded) in which the only freedom is WHICH non-stale open entry is popped.

 * wa_adversary(grid,s,t,w): DFS over all WA*-consistent pop orders (popped entry must have f_w within EPS of
   the minimum; ties adversarial).  'FAIL' = Open empties before t receives an entry.  (Corrected 2026-10-25:
   success is "t is RETURNED by a top-level scan", as in the reference algorithm; a sub-jump that steps on t
   makes the enclosing diagonal scan return the diagonal cell, not t, so stepping on t is not success.)
 * min_slack(grid,s,t,w,cap): bottleneck (minimax) search over pop orders: slack of an order = max over pops
   of f(popped)-fmin.  Returns the minimal slack of a failing order (0 => WA*-realisable failure), or a lower
   bound if the state cap is hit, or inf if every order reaches t.  Branches in which t receives an entry are
   pruned (t pushed = t eventually popped = success).
 * ReplayJPS: subclass of the reference CanonicalJPS whose tie-breaking follows a prescribed pop order
   (deterministic rule: among f-minimal entries pop the one earliest in the list).  Used to reproduce any
   failure found with the REFERENCE code.
"""
import sys, math, heapq, itertools
sys.path.insert(0, '/home/claude/jps-wa/ref')
from jpswa import Grid, CanonicalJPS, grid_to_str, octile, dijkstra, SQ2, DIRS8

EPS = 1e-9

class Model:
    """Scan cache: expand(x, parent) -> (list of (cell, cost-from-x), visited frozenset)."""
    def __init__(self, grid, s):
        self.grid = grid; self.s = s
        self.J = CanonicalJPS(grid, s, (-99, -99), 1.0, 'hig')
        self.cache = {}

    def dir_from(self, x, p):
        if p is None: return (0, 0)
        return ((x[0] > p[0]) - (x[0] < p[0]), (x[1] > p[1]) - (x[1] < p[1]))

    def expand(self, x, d, t=None):
        """t: target; a scan (top-level or sub-jump) stops when it steps on t, exactly as in the reference jump()."""
        key = (x, d, t)
        if key in self.cache: return self.cache[key]
        grid = self.grid; J = self.J
        out = []; vis = set()
        def jr(x0, y0, dx, dy, gg):
            while True:
                if not grid.legal(x0, y0, dx, dy): return None
                x0 += dx; y0 += dy; gg += SQ2 if (dx and dy) else 1.0; vis.add((x0, y0))
                if (x0, y0) == t: return (x0, y0, gg)
                if dx and dy:
                    if jr(x0, y0, dx, 0, gg) is not None or jr(x0, y0, 0, dy, gg) is not None: return (x0, y0, gg)
                elif J.has_forced(x0, y0, dx, dy): return (x0, y0, gg)
        for e in J.successor_dirs(x[0], x[1], d[0], d[1]):
            r = jr(x[0], x[1], e[0], e[1], 0.0)
            if r is not None: out.append(((r[0], r[1]), r[2]))
        self.cache[key] = (tuple(out), frozenset(vis))
        return self.cache[key]

    def component(self):
        from collections import deque
        seen = {self.s}; dq = deque([self.s]); g = self.grid
        while dq:
            x, y = dq.popleft()
            for dx, dy in DIRS8:
                if g.legal(x, y, dx, dy):
                    n = (x + dx, y + dy)
                    if n not in seen: seen.add(n); dq.append(n)
        return seen


def _succ_state(M, closed, od, x, gx, px, t=None):
    """apply expansion of x; returns (new closed, new open dict, visited). Success (t pushed) is checked by the caller."""
    d = M.dir_from(x, px)
    jps, vis = M.expand(x, d, t)
    nc = closed | {x}
    no = dict(od); del no[x]
    for (j, c) in jps:
        if j in nc: continue
        jg = gx + c
        if jg < no.get(j, (math.inf,))[0] - 1e-12: no[j] = (jg, x)
    return nc, no, vis


def wa_adversary(grid, s, t, w, limit=2_000_000, M=None):
    """Exhaustive adversary over WA*-consistent tie-breaking.  Returns ('FAIL', order) / ('complete', None) / ('limit', None)."""
    M = M or Model(grid, s)
    h = lambda c: octile(c[0], c[1], t[0], t[1])
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
        fmin = min(g + w * h(c) for c, (g, p) in od.items())
        for x, (gx, px) in od.items():
            if gx + w * h(x) > fmin + EPS: continue
            if x == t: continue
            nc, no, vis = _succ_state(M, closed, od, x, gx, px, t)
            if t in no: continue
            stack.append(((nc, tuple(sorted((c, g, p) for c, (g, p) in no.items()))), order + [x]))
    return 'complete', None


def min_slack(grid, s, t, w, cap=300_000, M=None):
    """Bottleneck search.  Returns (status, value, order): status 'FAIL' (value = minimal slack of a failing
    order; 0.0 means WA*-realisable), 'LB' (cap hit; value = lower bound on the minimal slack), 'complete'
    (value = inf: no order avoiding t exists at all)."""
    M = M or Model(grid, s)
    h = lambda c: octile(c[0], c[1], t[0], t[1])
    start = (frozenset(), ((s, 0.0, None),))
    best = {start: 0.0}
    pq = [(0.0, 0, start, [])]
    cnt = itertools.count(1)
    done = set(); n = 0
    while pq:
        b, _, st, order = heapq.heappop(pq)
        if st in done: continue
        done.add(st); n += 1
        closed, open_ = st
        if not open_: return 'FAIL', b, order
        if n > cap: return 'LB', b, None
        od = {c: (g, p) for c, g, p in open_}
        fmin = min(g + w * h(c) for c, (g, p) in od.items())
        for x, (gx, px) in od.items():
            if x == t: continue
            nc, no, vis = _succ_state(M, closed, od, x, gx, px, t)
            if t in no: continue
            nb = max(b, gx + w * h(x) - fmin)
            if nb < EPS: nb = 0.0
            nst = (nc, tuple(sorted((c, g, p) for c, (g, p) in no.items())))
            if nst in done: continue
            if nb < best.get(nst, math.inf) - 1e-12:
                best[nst] = nb
                heapq.heappush(pq, (nb, next(cnt), nst, order + [x]))
    return 'complete', math.inf, None


class ReplayJPS(CanonicalJPS):
    """Reference algorithm with the deterministic tie rule: among entries with minimal f_w (within EPS), pop the
    one whose cell comes first in `order`; cells not in `order` come last, then 'hig'."""
    def __init__(self, grid, s, t, w, order):
        super().__init__(grid, s, t, w, 'hig')
        self.rank = {c: i for i, c in enumerate(order)}

    def search(self):
        s, t, w = self.s, self.t, self.w
        gval = {s: 0.0}; parent = {s: None}; closed = set()
        open_ = []  # list of (f, cell, g)
        self.visited = {s}
        def push(cell, gc):
            open_.append((gc + w * octile(cell[0], cell[1], t[0], t[1]), cell, gc)); self.generated += 1
        push(s, 0.0)
        while open_:
            fmin = min(e[0] for e in open_)
            cands = [e for e in open_ if e[0] <= fmin + EPS]
            e = min(cands, key=lambda e: (self.rank.get(e[1], 10**9), -e[2]))
            open_.remove(e)
            f, n, gn = e
            if n in closed or gn > gval[n] + 1e-12: continue
            closed.add(n); self.expanded += 1; self.trace.append((n, gn))
            if n == t: return gn, self._path(parent, t)
            x, y = n; p = parent[n]
            if p is None: dx = dy = 0
            else: dx = (x > p[0]) - (x < p[0]); dy = (y > p[1]) - (y < p[1])
            for ddx, ddy in self.successor_dirs(x, y, dx, dy):
                r = self.jump(x, y, ddx, ddy, gn)
                if r is None: continue
                jx, jy, jg = r; j = (jx, jy)
                if j in closed: continue
                if jg < gval.get(j, math.inf) - 1e-12:
                    gval[j] = jg; parent[j] = n; push(j, jg)
        return math.inf, None

    def jump(self, x, y, dx, dy, gg):
        # identical to the reference, plus recording of stepped-on cells
        g = self.g
        while True:
            if not g.legal(x, y, dx, dy): return None
            x += dx; y += dy; gg += SQ2 if (dx and dy) else 1.0
            self.scanned += 1; self.visited.add((x, y))
            if (x, y) == self.t: return (x, y, gg)
            if dx and dy:
                if self.jump(x, y, dx, 0, gg) is not None or self.jump(x, y, 0, dy, gg) is not None:
                    return (x, y, gg)
            else:
                if self.has_forced(x, y, dx, dy): return (x, y, gg)


def reproduce(grid, s, t, w, order):
    """Run the REFERENCE algorithm (ReplayJPS: reference successor_dirs/jump, reference loop) with the tie rule
    given by `order`; also the 6 built-in tie rules.  Returns dict of results (cost or inf)."""
    res = {}
    R = ReplayJPS(grid, s, t, w, order); c, _ = R.search(); res['replay'] = c
    for tie in ('hig', 'log', 'fifo', 'lifo', 'rand', 'greedy'):
        c, _ = CanonicalJPS(grid, s, t, w, tie).search(); res[tie] = c
    return res


def pinwheel1(L=(3, 3, 3, 3), N=9, centre=None, extra=()):
    """1x1 pinwheel around t: blockers at the four knight offsets t-2d_{i-1}-d_i (d_0=E,d_1=S,d_2=W,d_3=N)."""
    c = centre or (N // 2, N // 2)
    D = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    bl = set()
    for i in range(4):
        dp, d = D[(i - 1) % 4], D[i]
        bl.add((c[0] - 2 * dp[0] - d[0], c[1] - 2 * dp[1] - d[1]))
    bl |= set(extra)
    return Grid(N, N, [b for b in bl if 0 <= b[0] < N and 0 <= b[1] < N]), c
