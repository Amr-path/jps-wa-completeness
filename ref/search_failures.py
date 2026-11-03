"""Randomised search for failures of canonical JPS + WA* (no re-expansion).

A *failure* on a solvable instance is: no path returned, or cost > w * C* (+tol).
Also sanity-checks canonical JPS at w = 1 against Dijkstra (must be exact)."""
import math
import random
import sys
import time

from jpswa import Grid, CanonicalJPS, dijkstra, wastar, grid_to_str

TOL = 1e-9


def random_grid(rng, W, H, p):
    blocked = [(x, y) for y in range(H) for x in range(W) if rng.random() < p]
    return Grid(W, H, blocked)


def main(seed=1, n_grids=3000, sizes=(4, 5, 6, 8), dens=(0.2, 0.35, 0.5), weights=(1.0, 1.2, 1.5, 2.0, 3.0, 10.0),
         ties=('hig', 'log', 'fifo', 'lifo'), pairs_per_grid=12):
    rng = random.Random(seed)
    t0 = time.time()
    stats = dict(instances=0, jps_opt_mismatch=0, failures=0, wa_failures=0)
    failures = []
    for gi in range(n_grids):
        W = H = rng.choice(sizes)
        grid = random_grid(rng, W, H, rng.choice(dens))
        cells = grid.free_cells()
        if len(cells) < 2:
            continue
        for _ in range(pairs_per_grid):
            s, t = rng.sample(cells, 2)
            opt = dijkstra(grid, s, t)
            if math.isinf(opt):
                continue
            # sanity: canonical JPS optimal at w=1 (any tie rule)
            c1, _ = CanonicalJPS(grid, s, t, 1.0, rng.choice(ties)).search()
            if abs(c1 - opt) > 1e-6:
                stats['jps_opt_mismatch'] += 1
                failures.append(('JPS_W1_MISMATCH', grid, s, t, 1.0, '-', c1, opt))
            for w in weights:
                for tie in ties:
                    stats['instances'] += 1
                    c, path = CanonicalJPS(grid, s, t, w, tie).search()
                    if math.isinf(c) or c > w * opt + TOL:
                        stats['failures'] += 1
                        failures.append(('JPSWA_FAIL', grid, s, t, w, tie, c, opt))
                # control: plain WA* without re-expansion must never fail
                cw = wastar(grid, s, t, w)
                if math.isinf(cw) or cw > w * opt + TOL:
                    stats['wa_failures'] += 1
                    failures.append(('WA_FAIL', grid, s, t, w, '-', cw, opt))
    print(f"done in {time.time()-t0:.1f}s  {stats}")
    for kind, grid, s, t, w, tie, c, opt in failures[:20]:
        print(f"\n--- {kind}  w={w} tie={tie} cost={c:.4f} opt={opt:.4f} ratio={c/opt if opt else 0:.4f}")
        print(grid_to_str(grid, s, t))
    return failures


if __name__ == '__main__':
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
    main(seed=seed, n_grids=n)
