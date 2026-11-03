"""Independent cell-closing canonical JPS order model (auditor's own code; no import of core/_succ_state/decide).

State: closed bitmask + live entries {cell: (g, arrival_dir)}.  Popping a live entry x closes x, runs the
successor scans of (x, dir); each returned cell y not closed gets entry (g_x + c, e) if g strictly improves
(tolerance 1e-12).  A scan stops when it steps on t (returns t).  Success = t receives an entry.
Failure = Open empty and t never received an entry.
"""
import math, sys, heapq, itertools
SQ2 = math.sqrt(2.0)
D8 = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def octile(a, b):
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    return max(dx, dy) + (SQ2 - 1) * min(dx, dy)


class Inst:
    def __init__(self, N, blocked, s, t):
        self.N = N; self.B = set(map(tuple, blocked)); self.s = tuple(s); self.t = tuple(t)
        self.cache = {}

    def free(self, x, y):
        return 0 <= x < self.N and 0 <= y < self.N and (x, y) not in self.B

    def legal(self, x, y, dx, dy):
        if not self.free(x + dx, y + dy): return False
        if dx and dy: return self.free(x + dx, y) and self.free(x, y + dy)
        return True

    def forced_sides(self, x, y, dx, dy):
        """straight (dx,dy): list of perpendicular unit vectors p with x-d+p blocked and x+p free."""
        out = []
        perps = [(0, 1), (0, -1)] if dx else [(1, 0), (-1, 0)]
        for px, py in perps:
            if not self.free(x - dx + px, y - dy + py) and self.free(x + px, y + py):
                out.append((px, py))
        return out

    def succ_dirs(self, x, y, d):
        if d == (0, 0): return list(D8)
        dx, dy = d
        if dx and dy: return [(dx, dy), (dx, 0), (0, dy)]
        out = [d]
        for px, py in self.forced_sides(x, y, dx, dy):
            out.append((px, py)); out.append((dx + px, dy + py))
        return out

    def jump(self, x, y, dx, dy, vis):
        c = 0.0
        while True:
            if not self.legal(x, y, dx, dy): return None
            x += dx; y += dy; c += SQ2 if (dx and dy) else 1.0
            vis.add((x, y))
            if (x, y) == self.t: return (x, y), c
            if dx and dy:
                if self.jump(x, y, dx, 0, vis) is not None or self.jump(x, y, 0, dy, vis) is not None:
                    return (x, y), c
            elif self.forced_sides(x, y, dx, dy):
                return (x, y), c

    def expand(self, x, d):
        k = (x, d)
        if k not in self.cache:
            vis = set(); out = []
            for e in self.succ_dirs(x[0], x[1], d):
                r = self.jump(x[0], x[1], e[0], e[1], vis)
                if r is not None: out.append((r[0], r[1], e))
            self.cache[k] = (tuple(out), frozenset(vis))
        return self.cache[k]

    def idx(self, c): return c[1] * self.N + c[0]

    def step(self, mask, od, x):
        """returns (newmask, new od, success_flag)"""
        g, d = od[x]
        jps, _ = self.expand(x, d)
        nm = mask | (1 << self.idx(x))
        no = dict(od); del no[x]
        for y, c, e in jps:
            if (nm >> self.idx(y)) & 1: continue
            ng = g + c
            if y not in no or ng < no[y][0] - 1e-12:
                no[y] = (ng, e)
        return nm, no, (self.t in no)

    def key(self, mask, od):
        return (mask, tuple(sorted((self.idx(c), round(g * 1e6), d) for c, (g, d) in od.items())))

    def f(self, w, c, g): return g + w * octile(c, self.t)


def exhaustive(I, limit=10**8):
    """any pop order. returns ('FAIL', order) or ('complete', nstates)."""
    od0 = {I.s: (0.0, (0, 0))}
    seen = {I.key(0, od0)}
    stack = [(0, od0, [])]
    while stack:
        mask, od, order = stack.pop()
        for x in list(od):
            nm, no, succ = I.step(mask, od, x)
            if succ: continue
            if not no: return 'FAIL', order + [x]
            k = I.key(nm, no)
            if k in seen: continue
            seen.add(k)
            if len(seen) > limit: return 'limit', len(seen)
            stack.append((nm, no, order + [x]))
    return 'complete', len(seen)


def bottleneck(I, w, cap=5_000_000, EPS=1e-9):
    """minimax search: minimal over failing orders of max_k (f(popped_k) - fmin_k)."""
    od0 = {I.s: (0.0, (0, 0))}
    k0 = I.key(0, od0)
    best = {k0: 0.0}; done = set()
    cnt = itertools.count()
    pq = [(0.0, next(cnt), 0, od0, ())]
    while pq:
        b, _, mask, od, order = heapq.heappop(pq)
        if mask == -1: return 'FAIL', b, list(order)
        k = I.key(mask, od)
        if k in done: continue
        done.add(k)
        if len(done) > cap: return 'cap', b, None
        fmin = min(I.f(w, c, g) for c, (g, d) in od.items())
        for x, (g, d) in list(od.items()):
            nm, no, succ = I.step(mask, od, x)
            if succ: continue
            v = I.f(w, x, g) - fmin
            if v < EPS: v = 0.0
            nb = max(b, v)
            if not no:
                # terminal failing; push as a final state so we pop it in order
                heapq.heappush(pq, (nb, next(cnt), -1, None, order + (x,)))
                continue
            nk = I.key(nm, no)
            if nk in done: continue
            if nb < best.get(nk, math.inf) - 1e-12:
                best[nk] = nb
                heapq.heappush(pq, (nb, next(cnt), nm, no, order + (x,)))
    return 'complete', math.inf, None


def replay(I, w, order):
    od = {I.s: (0.0, (0, 0))}; mask = 0; b = 0.0; vis = {I.s}
    for x in order:
        assert x in od, ('not live', x)
        fmin = min(I.f(w, c, g) for c, (g, d) in od.items())
        g, d = od[x]
        b = max(b, I.f(w, x, g) - fmin)
        vis |= I.expand(x, d)[1]
        mask, od, succ = I.step(mask, od, x)
        assert not succ, 't got entry'
    assert not od, 'open not empty'
    return b, (I.t in vis)
