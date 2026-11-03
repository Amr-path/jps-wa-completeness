"""Adversarial-order analysis of canonical JPS with cell-closing.

Abstraction: a search state is (closed: cell -> arrival direction used at expansion,
open: set of (cell, arrival_dir) pending entries).  The adversary may expand ANY pending
entry (any best-first order with any tie rule is a special case; the adversary is even
stronger because it may also choose which pending direction a cell is expanded with).
Jump points returned into an already-closed cell are ignored (no re-expansion).

Question answered per instance: does there exist an expansion order under which Open
empties without t ever being touched by a scan?  (If a scan touches t the jump returns t,
t is pushed and must eventually be expanded, so the search succeeds.)

This gives a SOUND over-approximation of failure: if the adversary cannot fail, canonical
JPS + any WA* ordering cannot fail on that instance.  If the adversary CAN fail, the found
order must still be checked for realisability by an actual WA* run.
"""
import math
import sys
import random
from functools import lru_cache

from jpswa import Grid, CanonicalJPS, dijkstra, grid_to_str, DIRS8


class Adversary:
    def __init__(self, grid, s, t):
        self.g = grid
        self.s, self.t = s, t
        self.J = CanonicalJPS(grid, s, t, 1.0, 'hig')
        self.jump_cache = {}
        self.succ_cache = {}

    def succ(self, x, d):
        key = (x, d)
        if key not in self.succ_cache:
            out = []
            for e in self.J.successor_dirs(x[0], x[1], d[0], d[1]):
                jk = (x, e)
                if jk not in self.jump_cache:
                    r = self.J.jump(x[0], x[1], e[0], e[1], 0.0)
                    self.jump_cache[jk] = None if r is None else (r[0], r[1])
                y = self.jump_cache[jk]
                if y is not None:
                    out.append((y, e))
            self.succ_cache[key] = tuple(out)
        return self.succ_cache[key]

    def can_fail(self, limit_states=2_000_000):
        """Returns (True, order) if some expansion order ends with Open empty and t unclosed."""
        t = self.t
        start = (frozenset(), frozenset({(self.s, (0, 0))}))
        seen = set()
        stack = [(start, [])]
        n = 0
        while stack:
            (closed, open_), order = stack.pop()
            if (closed, open_) in seen:
                continue
            seen.add((closed, open_))
            n += 1
            if n > limit_states:
                return None, order  # undecided
            closed_cells = {c for c, _ in closed}
            pend = [(x, d) for (x, d) in open_ if x not in closed_cells]
            if not pend:
                if t not in closed_cells:
                    return True, order
                continue
            for (x, d) in pend:
                if x == t:
                    continue  # expanding t = success; adversary avoids it (but if t is pending and
                              # it is the only pending entry, the loop above leaves nothing else)
                new_closed = closed | {(x, d)}
                new_open = set(e for e in open_ if e[0] != x)
                for (y, e) in self.succ(x, d):
                    if y not in closed_cells:
                        new_open.add((y, e))
                stack.append(((new_closed, frozenset(new_open)), order + [(x, d)]))
            # if the only pending entries are t itself, this branch succeeds (no push)
        return False, None


def random_grid(rng, W, H, p):
    return Grid(W, H, [(x, y) for y in range(H) for x in range(W) if rng.random() < p])


def main(seed, n_grids, sizes=(4, 5, 6), dens=(0.3, 0.45, 0.55)):
    rng = random.Random(seed)
    inst = fails = undecided = 0
    for gi in range(n_grids):
        W = H = rng.choice(sizes)
        grid = random_grid(rng, W, H, rng.choice(dens))
        cells = grid.free_cells()
        if len(cells) < 2:
            continue
        for _ in range(6):
            s, t = rng.sample(cells, 2)
            if math.isinf(dijkstra(grid, s, t)):
                continue
            inst += 1
            ok, order = Adversary(grid, s, t).can_fail()
            if ok is None:
                undecided += 1
            elif ok:
                fails += 1
                print('ADVERSARIAL FAILURE')
                print(grid_to_str(grid, s, t))
                print('order:', order)
                sys.stdout.flush()
    print(f'seed {seed}: instances {inst}, adversarial failures {fails}, undecided {undecided}')


if __name__ == '__main__':
    main(int(sys.argv[1]), int(sys.argv[2]))
