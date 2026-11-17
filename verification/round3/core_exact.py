"""Exact-arithmetic version of core.wa_adversary (review, 2026-11-17).

Every cost is a + b*sqrt(2) with integers a, b, stored as the tuple (a, b); comparisons are exact (sign of
A + B sqrt2 decided by comparing squares). The weight is a rational P/Q, and the WA* priority is stored as
Q g + P h. An entry may be popped iff its priority equals the minimum exactly; an arrival improves a g-value iff it
is strictly smaller. Everything else (scan rules, success = t receives an entry, adversarial choice among the
minimal entries, state = (closed set, open entries)) is as in core.py; the scan rules come from the reference
implementation (ref/jpswa.py).
"""
import sys
from fractions import Fraction
sys.path.insert(0, '/path/to/jps-wa/verification/round3')
sys.path.insert(0, '/path/to/jps-wa/ref')
from jpswa import CanonicalJPS  # scan rules of the reference implementation


def sgn(a, b):
    """sign of a + b sqrt2 for integers a, b"""
    if a >= 0 and b >= 0: return 1 if (a or b) else 0
    if a <= 0 and b <= 0: return -1
    s = a * a - 2 * b * b  # never 0 unless a = b = 0
    return (1 if s > 0 else -1) if a > 0 else (-1 if s > 0 else 1)


def lt(x, y): return sgn(x[0] - y[0], x[1] - y[1]) < 0


def octile_x(x0, y0, x1, y1):
    dx, dy = abs(x0 - x1), abs(y0 - y1)
    return (max(dx, dy) - min(dx, dy), min(dx, dy))


class ModelX:
    """Scan cache with exact costs: expand(x, d, t) -> tuple of (cell, (a, b))."""
    def __init__(self, grid, s):
        self.grid = grid; self.s = s
        self.J = CanonicalJPS(grid, s, (-99, -99), 1.0, 'hig')
        self.cache = {}

    def dir_from(self, x, p):
        if p is None: return (0, 0)
        return ((x[0] > p[0]) - (x[0] < p[0]), (x[1] > p[1]) - (x[1] < p[1]))

    def expand(self, x, d, t):
        key = (x, d, t)
        if key in self.cache: return self.cache[key]
        grid = self.grid; J = self.J; out = []

        def jr(x0, y0, dx, dy, a, b):
            while True:
                if not grid.legal(x0, y0, dx, dy): return None
                x0 += dx; y0 += dy
                if dx and dy: b += 1
                else: a += 1
                if (x0, y0) == t: return (x0, y0, a, b)
                if dx and dy:
                    if jr(x0, y0, dx, 0, a, b) is not None or jr(x0, y0, 0, dy, a, b) is not None: return (x0, y0, a, b)
                elif J.has_forced(x0, y0, dx, dy): return (x0, y0, a, b)
        for e in J.successor_dirs(x[0], x[1], d[0], d[1]):
            r = jr(x[0], x[1], e[0], e[1], 0, 0)
            if r is not None: out.append(((r[0], r[1]), (r[2], r[3])))
        self.cache[key] = tuple(out)
        return self.cache[key]


def wa_adversary_x(grid, s, t, w, limit, M=None, anyorder=False):
    """Exhaustive adversary over WA*-consistent pop orders, exact. Returns 'FAIL' / 'complete' / 'limit'.
    anyorder=True (test only): every open entry may be popped, as in core.min_slack."""
    M = M or ModelX(grid, s)
    q = Fraction(w).limit_denominator(1000); P, Q = q.numerator, q.denominator

    def pri(c, g):
        h = octile_x(c[0], c[1], t[0], t[1])
        return (Q * g[0] + P * h[0], Q * g[1] + P * h[1])
    start = (frozenset(), ((s, (0, 0), None),))
    seen = set(); stack = [start]; n = 0
    while stack:
        closed, open_ = stack.pop()
        key = (closed, open_)
        if key in seen: continue
        seen.add(key); n += 1
        if n > limit: return 'limit'
        if not open_: return 'FAIL'
        pr = [(pri(c, g), c, g, p) for c, g, p in open_]
        fmin = pr[0][0]
        for f, *_ in pr[1:]:
            if lt(f, fmin): fmin = f
        od = {c: (g, p) for c, g, p in open_}
        for f, x, gx, px in pr:
            if (f != fmin and not anyorder) or x == t: continue  # equal a + b sqrt2 <=> equal tuples
            nc = closed | {x}; no = dict(od); del no[x]
            for (j, c) in M.expand(x, M.dir_from(x, px), t):
                if j in nc: continue
                jg = (gx[0] + c[0], gx[1] + c[1])
                if j not in no or lt(jg, no[j][0]): no[j] = (jg, x)
            if t in no: continue
            stack.append((nc, tuple(sorted((c, g, p) for c, (g, p) in no.items()))))
    return 'complete'
