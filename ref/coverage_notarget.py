"""Exhaustion test: canonical JPS with NO target, cell-closing, arbitrary (random) expansion
order. Conjecture C: the set of cells visited by scans (plus s) equals the connected component
of s, for every order.  Also records, per instance, the worst case over orders."""
import math, random, sys, time
from collections import deque
from jpswa import Grid, CanonicalJPS, grid_to_str, DIRS8


def component(grid, s):
    seen = {s}; dq = deque([s])
    while dq:
        x, y = dq.popleft()
        for dx, dy in DIRS8:
            if grid.legal(x, y, dx, dy):
                n = (x + dx, y + dy)
                if n not in seen:
                    seen.add(n); dq.append(n)
    return seen


def run_notarget(grid, s, rng):
    """Random-order canonical JPS to exhaustion with no target. Returns visited set."""
    J = CanonicalJPS(grid, s, (-99, -99), 1.0, 'hig')   # target unreachable/outside: never matched
    visited = {s}
    orig_jump = J.jump

    def jump_rec(x, y, dx, dy, gg):
        # replicate J.jump but record visited cells
        g = J.g
        while True:
            if not g.legal(x, y, dx, dy):
                return None
            x += dx; y += dy; gg += 1
            visited.add((x, y))
            if dx and dy:
                if jump_rec(x, y, dx, 0, gg) is not None or jump_rec(x, y, 0, dy, gg) is not None:
                    return (x, y, gg)
            else:
                if J.has_forced(x, y, dx, dy):
                    return (x, y, gg)
    closed = {}
    open_ = [(s, (0, 0))]
    while open_:
        i = rng.randrange(len(open_))
        x, d = open_.pop(i)
        if x in closed:
            continue
        closed[x] = d
        for e in J.successor_dirs(x[0], x[1], d[0], d[1]):
            r = jump_rec(x[0], x[1], e[0], e[1], 0)
            if r is None:
                continue
            y = (r[0], r[1])
            if y in closed:
                continue
            open_.append((y, e))
    return visited


def main(seed, n_grids, orders=20):
    rng = random.Random(seed); inst = bad = 0; t0 = time.time()
    for _ in range(n_grids):
        W = H = rng.choice((5, 6, 7, 8, 10, 12))
        p = rng.choice((0.2, 0.3, 0.4, 0.5, 0.6))
        grid = Grid(W, H, [(x, y) for y in range(H) for x in range(W) if rng.random() < p])
        cells = grid.free_cells()
        if not cells:
            continue
        for _ in range(3):
            s = rng.choice(cells)
            comp = component(grid, s)
            for k in range(orders):
                inst += 1
                V = run_notarget(grid, s, rng)
                if V != comp:
                    bad += 1
                    if bad <= 5:
                        print('COVERAGE GAP: missing', sorted(comp - V), 'extra', sorted(V - comp))
                        print(grid_to_str(grid, s, None, sorted(comp - V)))
    print(f'seed {seed}: runs {inst}, coverage gaps {bad}, {time.time()-t0:.0f}s')


if __name__ == '__main__':
    main(int(sys.argv[1]), int(sys.argv[2]))
