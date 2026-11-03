"""
Reference implementation (Python, deliberately simple) of

  canonical Jump Point Search (no corner cutting; Harabor & Grastien 2014 variant,
  as specified in Sec. 5.1 of Elshahed & Majahar Ali, "Certified corridor search")

combined with a Weighted A* open-list ordering  f_w = g + w*h  and a strict
closed-list policy (a cell, once expanded, is never re-expanded, and improvements
to its g are ignored) -- i.e. the combination whose completeness Carlson, Harabor
& Stuckey (SoCS 2024) conjecture but leave open.

Also: canonical JPS (w = 1), plain A*/WA* on the grid, and a Dijkstra oracle.

Grid model
----------
  cells (x, y), 0 <= x < W, 0 <= y < H;  out of bounds counts as blocked.
  moves to the 8 neighbours; a diagonal move (dx,dy) from (x,y) is legal iff
  (x+dx,y+dy), (x+dx,y) and (x,y+dy) are all free (no corner cutting).
  costs: 1 straight, sqrt(2) diagonal. Heuristic: octile distance to target.
"""
import heapq
import itertools
import math
from collections import deque

SQ2 = math.sqrt(2.0)
DIRS8 = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def octile(ax, ay, bx, by):
    dx, dy = abs(ax - bx), abs(ay - by)
    return (dx + (SQ2 - 1) * dy) if dx > dy else (dy + (SQ2 - 1) * dx)


class Grid:
    def __init__(self, W, H, blocked):
        self.W, self.H = W, H
        self.blocked = set(blocked)

    def free(self, x, y):
        return 0 <= x < self.W and 0 <= y < self.H and (x, y) not in self.blocked

    def legal(self, x, y, dx, dy):
        if not self.free(x + dx, y + dy):
            return False
        if dx and dy:
            return self.free(x + dx, y) and self.free(x, y + dy)
        return True

    def free_cells(self):
        return [(x, y) for y in range(self.H) for x in range(self.W) if self.free(x, y)]


# ---------------------------------------------------------------- oracle
def dijkstra(grid, s, t):
    """Exact shortest-path cost on the 8-connected no-corner-cutting graph; inf if none."""
    dist = {s: 0.0}
    pq = [(0.0, s)]
    while pq:
        d, (x, y) = heapq.heappop(pq)
        if (x, y) == t:
            return d
        if d > dist[(x, y)] + 1e-12:
            continue
        for dx, dy in DIRS8:
            if grid.legal(x, y, dx, dy):
                n = (x + dx, y + dy)
                nd = d + (SQ2 if dx and dy else 1.0)
                if nd < dist.get(n, math.inf) - 1e-12:
                    dist[n] = nd
                    heapq.heappush(pq, (nd, n))
    return math.inf


# ---------------------------------------------------------------- canonical JPS
class CanonicalJPS:
    """
    tie: tie-breaking among equal f_w in Open:
         'hig'  -> larger g first (standard)
         'log'  -> smaller g first
         'fifo' -> earlier insertion first
         'lifo' -> later insertion first
    """

    def __init__(self, grid, s, t, w=1.0, tie='hig'):
        self.g = grid
        self.s, self.t = s, t
        self.w = w
        self.tie = tie
        self.expanded = 0
        self.generated = 0
        self.scanned = 0
        self.trace = []
        import random as _r
        self.rng = _r.Random(hash((s, t, w, tie)) & 0xffffffff)

    # forced-direction test for straight arrival d at cell x: some perpendicular e with
    # x-d+e blocked and x+e free  (Sec. 5.1 of CCS; identical to ccs.cpp has_forced/dirs)
    def successor_dirs(self, x, y, dx, dy):
        g = self.g
        if dx == 0 and dy == 0:            # start cell
            return list(DIRS8)
        if dx and dy:                       # diagonal arrival: natural successors only
            return [(dx, dy), (dx, 0), (0, dy)]
        out = [(dx, dy)]
        if dx:
            for e in (1, -1):
                if not g.free(x - dx, y + e) and g.free(x, y + e):
                    out.append((0, e))
                    out.append((dx, e))
        else:
            for e in (1, -1):
                if not g.free(x + e, y - dy) and g.free(x + e, y):
                    out.append((e, 0))
                    out.append((e, dy))
        return out

    def has_forced(self, x, y, dx, dy):
        g = self.g
        if dx:
            return any(not g.free(x - dx, y + e) and g.free(x, y + e) for e in (1, -1))
        return any(not g.free(x + e, y - dy) and g.free(x + e, y) for e in (1, -1))

    def jump(self, x, y, dx, dy, gg):
        """Returns (jx, jy, jg) or None. Visits every stepped-on cell."""
        g = self.g
        while True:
            if not g.legal(x, y, dx, dy):
                return None
            x += dx
            y += dy
            gg += SQ2 if (dx and dy) else 1.0
            self.scanned += 1
            if (x, y) == self.t:
                return (x, y, gg)
            if dx and dy:
                # sub-jumps at every cell stepped onto, straight first (dx,0) then (0,dy), short-circuit
                if self.jump(x, y, dx, 0, gg) is not None or self.jump(x, y, 0, dy, gg) is not None:
                    return (x, y, gg)
            else:
                if self.has_forced(x, y, dx, dy):
                    return (x, y, gg)

    def search(self):
        s, t, w = self.s, self.t, self.w
        gval = {s: 0.0}
        parent = {s: None}
        closed = set()
        counter = itertools.count()
        open_ = []

        def push(cell, gc):
            c = next(counter)
            f = gc + w * octile(cell[0], cell[1], t[0], t[1])
            if self.tie == 'hig':
                key = (f, -gc, c)
            elif self.tie == 'log':
                key = (f, gc, c)
            elif self.tie == 'fifo':
                key = (f, c)
            elif self.tie == 'lifo':
                key = (f, -c)
            elif self.tie == 'rand':      # adversarial: arbitrary expansion order
                key = (self.rng.random(), c)
            elif self.tie == 'greedy':    # pure greedy best-first on h (limit w -> inf)
                key = (octile(cell[0], cell[1], t[0], t[1]), -gc, c)
            else:
                raise ValueError(self.tie)
            heapq.heappush(open_, (key, cell, gc))
            self.generated += 1

        push(s, 0.0)
        while open_:
            key, n, gn = heapq.heappop(open_)
            if n in closed or gn > gval[n] + 1e-12:
                continue
            closed.add(n)
            self.expanded += 1
            self.trace.append((n, gn))
            if n == t:
                return gn, self._path(parent, t)
            x, y = n
            p = parent[n]
            if p is None:
                dx = dy = 0
            else:
                dx = (x > p[0]) - (x < p[0])
                dy = (y > p[1]) - (y < p[1])
            for ddx, ddy in self.successor_dirs(x, y, dx, dy):
                r = self.jump(x, y, ddx, ddy, gn)
                if r is None:
                    continue
                jx, jy, jg = r
                j = (jx, jy)
                if j in closed:
                    continue  # WA* without re-expansion: improvements to closed cells are ignored
                if jg < gval.get(j, math.inf) - 1e-12:
                    gval[j] = jg
                    parent[j] = n
                    push(j, jg)
        return math.inf, None

    @staticmethod
    def _path(parent, t):
        out = [t]
        while parent[out[-1]] is not None:
            out.append(parent[out[-1]])
        return out[::-1]


# ---------------------------------------------------------------- plain WA* on the grid (control)
def wastar(grid, s, t, w=1.0):
    gval = {s: 0.0}
    closed = set()
    counter = itertools.count()
    pq = [((w * octile(*s, *t), 0.0, next(counter)), s, 0.0)]
    while pq:
        _, n, gn = heapq.heappop(pq)
        if n in closed or gn > gval[n] + 1e-12:
            continue
        closed.add(n)
        if n == t:
            return gn
        x, y = n
        for dx, dy in DIRS8:
            if grid.legal(x, y, dx, dy):
                m = (x + dx, y + dy)
                if m in closed:
                    continue
                ng = gn + (SQ2 if dx and dy else 1.0)
                if ng < gval.get(m, math.inf) - 1e-12:
                    gval[m] = ng
                    heapq.heappush(pq, ((ng + w * octile(*m, *t), -ng, next(counter)), m, ng))
    return math.inf


def grid_to_str(grid, s=None, t=None, path=None):
    pset = set(path or [])
    rows = []
    for y in range(grid.H):
        row = ''
        for x in range(grid.W):
            if (x, y) == s:
                row += 'S'
            elif (x, y) == t:
                row += 'T'
            elif not grid.free(x, y):
                row += '#'
            elif (x, y) in pset:
                row += '*'
            else:
                row += '.'
        rows.append(row)
    return '\n'.join(rows)
