"""Search for a WA*-realisable pinwheel failure: variations of the pinwheel grid (different start cells,
random toggles of a few cells, larger windows), target in the hole, exhaustive adversary restricted to
WA* order (ties adversarial) for several weights.  Prints any failure found."""
import sys, math, random, time
sys.path.insert(0, '/home/claude/jps-wa/ref')
from jpswa import Grid, CanonicalJPS, grid_to_str, octile, dijkstra
from pinwheel import build
from pinwheel_wastar import wastar_adversary

def main(seed, n):
    rng = random.Random(seed)
    g0, s0, hole, sh = build()
    ws = [1.0, 1.5, 2.0, 3.0, 10.0, 1000.0]
    fails = 0; tried = 0; t0 = time.time()
    for it in range(n):
        blocked = set(g0.blocked)
        # random toggles of up to 3 cells, never hole cells
        for _ in range(rng.randint(0, 3)):
            c = (rng.randrange(8), rng.randrange(8))
            if c in hole: continue
            if c in blocked: blocked.discard(c)
            else: blocked.add(c)
        g = Grid(8, 8, list(blocked))
        free = [c for c in g.free_cells() if c not in hole]
        if not free: continue
        s = rng.choice(free)
        t = rng.choice(hole)
        if dijkstra(g, s, t) == math.inf: continue
        for w in ws:
            tried += 1
            res, order = wastar_adversary(g, s, t, w, limit=300_000)
            if res == 'FAIL':
                fails += 1
                print('WA* FAILURE w=', w, 's=', s, 't=', t); print(grid_to_str(g, s, t)); print('order', order); sys.stdout.flush()
                break
        if (it + 1) % 50 == 0:
            print(f'{it+1} grids, {tried} runs, {fails} failures, {time.time()-t0:.0f}s'); sys.stdout.flush()
    print('done', fails)

if __name__ == '__main__':
    main(int(sys.argv[1]), int(sys.argv[2]))
