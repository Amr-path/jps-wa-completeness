"""Exhaustive adversary over expansion orders, no target: does some order leave a reachable cell unvisited?

State = (closed: frozenset of (cell, dir)), open: frozenset of (cell, dir)).  Visited cells are a function
of the closed set (union of the cells stepped on by the scans of the closed entries), so they are not
stored.  Terminal: no pending entry whose cell is unclosed.  Failure: visited != Reach(s).
Also runs on structured 'layered corridor' grids that maximise the strip/opening dependency chains.
"""
import sys, random, math, time
from jpswa import Grid, CanonicalJPS, grid_to_str, DIRS8
from coverage_notarget import component


class CoverAdversary:
    def __init__(self, grid, s):
        self.g = grid; self.s = s
        self.J = CanonicalJPS(grid, s, (-99, -99), 1.0, 'hig')
        self.scan_cache = {}   # (x, e) -> (jump point or None, frozenset visited)
        self.succ_cache = {}

    def scan(self, x, e):
        key = (x, e)
        if key in self.scan_cache: return self.scan_cache[key]
        vis = set(); g = self.g
        def jr(x, y, dx, dy):
            while True:
                if not g.legal(x, y, dx, dy): return None
                x += dx; y += dy; vis.add((x, y))
                if dx and dy:
                    if jr(x, y, dx, 0) is not None or jr(x, y, 0, dy) is not None: return (x, y)
                elif self.J.has_forced(x, y, dx, dy): return (x, y)
        r = jr(x[0], x[1], e[0], e[1])
        self.scan_cache[key] = (r, frozenset(vis)); return self.scan_cache[key]

    def succ(self, x, d):
        key = (x, d)
        if key not in self.succ_cache:
            out = []; vis = set()
            for e in self.J.successor_dirs(x[0], x[1], d[0], d[1]):
                r, v = self.scan(x, e); vis |= v
                if r is not None: out.append((r, e))
            self.succ_cache[key] = (tuple(out), frozenset(vis))
        return self.succ_cache[key]

    def can_fail(self, limit_states=2_000_000):
        reach = component(self.g, self.s)
        start = (frozenset(), frozenset({(self.s, (0, 0))}))
        seen = set(); stack = [(start, [])]; n = 0
        while stack:
            (closed, open_), order = stack.pop()
            if (closed, open_) in seen: continue
            seen.add((closed, open_)); n += 1
            if n > limit_states: return None, order, n
            closed_cells = {c for c, _ in closed}
            pend = [(x, d) for (x, d) in open_ if x not in closed_cells]
            if not pend:
                vis = {self.s}
                for (x, d) in closed: vis |= self.succ(x, d)[1]
                if vis != reach: return True, order, n
                continue
            for (x, d) in pend:
                new_closed = closed | {(x, d)}
                new_open = set(e for e in open_ if e[0] != x)
                for (y, e) in self.succ(x, d)[0]:
                    if y not in closed_cells: new_open.add((y, e))
                stack.append(((new_closed, frozenset(new_open)), order + [(x, d)]))
        return False, None, n


def layered_grid(rng, W, H):
    """Horizontal corridors separated by walls with random openings, plus sparse random blocks."""
    blocked = set()
    for y in range(H):
        if y % 2 == 1:
            for x in range(W):
                if rng.random() > rng.choice((0.15, 0.3, 0.5)): blocked.add((x, y))
        else:
            for x in range(W):
                if rng.random() < 0.1: blocked.add((x, y))
    return Grid(W, H, list(blocked))


def main(seed, n, kind):
    rng = random.Random(seed); fails = und = inst = 0; t0 = time.time(); maxn = 0
    for i in range(n):
        if kind == 'layered':
            W = rng.choice((8, 10, 12, 16)); H = rng.choice((5, 7, 9)); grid = layered_grid(rng, W, H)
        else:
            W = H = rng.choice((5, 6, 7, 8)); p = rng.choice((0.2, 0.3, 0.4))
            grid = Grid(W, H, [(x, y) for y in range(H) for x in range(W) if rng.random() < p])
        cells = grid.free_cells()
        if len(cells) < 3: continue
        for s in rng.sample(cells, min(2, len(cells))):
            inst += 1
            ok, order, nst = CoverAdversary(grid, s).can_fail(limit_states=400_000); maxn = max(maxn, nst)
            if ok is None: und += 1
            elif ok:
                fails += 1; print('COVERAGE FAILURE'); print(grid_to_str(grid, s, None)); print('order', order); sys.stdout.flush()
        if (i + 1) % 25 == 0:
            print(f'progress {i+1} grids, {inst} instances, {fails} failures, {und} undecided, max states {maxn}, {time.time()-t0:.0f}s'); sys.stdout.flush()
    print(f'seed {seed} {kind}: instances {inst}, failures {fails}, undecided {und}')


if __name__ == '__main__':
    main(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else 'random')
