"""TASK 2: dedicated generator for NON-CONVEX unvisited regions and longer dependency cycles.
Hole shapes R around t: L-tromino, U-pentomino, T-tetromino, S/Z-tetromino, two separate 1x1 holes, 1x3 bar,
plus 'ring' (3x3 minus centre) and 2x2 (control).  Obstacles are placed on the cells at Chebyshev distance 2
from R ("knight shell" of the hole) -- this is where the pinwheel blockers live -- plus optional far obstacles.
For every instance: (1) quick filter: can ANY expansion order leave t unvisited?  (min_slack with cap, w=1);
(2) if order-failable: min_slack at w in WS, report the minimal slack of a failing order (0 = WA* failure).
Usage: python3 gen_nonconvex.py SEED SECONDS"""
import sys, math, random, time
sys.path.insert(0, '/path/to/jps-wa/verification/round3'); sys.path.insert(0, '/path/to/jps-wa/ref')
from core import Model, min_slack, wa_adversary, reproduce, octile
from jpswa import Grid, grid_to_str

SHAPES = {
    'L3': [(0, 0), (1, 0), (0, 1)],
    'L4': [(0, 0), (1, 0), (2, 0), (0, 1)],
    'T4': [(0, 0), (1, 0), (2, 0), (1, 1)],
    'S4': [(0, 0), (1, 0), (1, 1), (2, 1)],
    'U5': [(0, 0), (0, 1), (1, 1), (2, 1), (2, 0)],
    'bar3': [(0, 0), (1, 0), (2, 0)],
    'two1': [(0, 0), (2, 0)],
    'two1d': [(0, 0), (2, 2)],
    'ring8': [(x, y) for x in range(3) for y in range(3) if (x, y) != (1, 1)],
    'sq2': [(0, 0), (1, 0), (0, 1), (1, 1)],
    'plus5': [(1, 0), (0, 1), (1, 1), (2, 1), (1, 2)],
}

def shell(R, dist=2):
    out = set()
    for (x, y) in R:
        for dx in range(-dist, dist + 1):
            for dy in range(-dist, dist + 1):
                if max(abs(dx), abs(dy)) == dist: out.add((x + dx, y + dy))
    return [c for c in out if all(max(abs(c[0] - r[0]), abs(c[1] - r[1])) >= dist for r in R)]

def instance(rnd, shape):
    N = rnd.choice([9, 10, 11])
    R0 = SHAPES[shape]
    ox, oy = rnd.randint(3, N - 6), rnd.randint(3, N - 6)
    R = [(x + ox, y + oy) for x, y in R0]
    sh = [c for c in shell(R) if 0 <= c[0] < N and 0 <= c[1] < N]
    k = rnd.randint(3, min(8, len(sh)))
    bl = set(rnd.sample(sh, k))
    # optional far obstacles
    for _ in range(rnd.randint(0, 4)):
        c = (rnd.randrange(N), rnd.randrange(N))
        if c not in R: bl.add(c)
    g = Grid(N, N, bl)
    free = [c for c in g.free_cells() if c not in R]
    s = rnd.choice(free); t = rnd.choice(R)
    return g, s, t, R

if __name__ == '__main__':
    seed = int(sys.argv[1]); secs = float(sys.argv[2])
    rnd = random.Random(seed); t0 = time.time()
    WS = [1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 1e6]
    n_inst = 0; n_failable = 0; best = {w: (math.inf, None) for w in WS}; shapes_fail = {}
    while time.time() - t0 < secs:
        shape = rnd.choice(list(SHAPES))
        g, s, t, R = instance(rnd, shape)
        M = Model(g, s)
        if t not in M.component(): continue
        n_inst += 1
        st, v, order = min_slack(g, s, t, 1.0, cap=40_000, M=M)
        if st == 'complete': continue
        n_failable += 1; shapes_fail[shape] = shapes_fail.get(shape, 0) + 1
        for w in WS:
            st, v, order = min_slack(g, s, t, w, cap=40_000, M=M)
            print(f'  [{time.time()-t0:6.0f}s] {shape} s={s} t={t} w={w:g}: {st} {v:.3f}', flush=True)
            if st == 'FAIL' and v < best[w][0]:
                best[w] = (v, (shape, s, t, sorted(g.blocked), g.W))
            if st == 'FAIL' and v < 1e-9:
                print('!!!!! WA* FAILURE', shape, s, t, sorted(g.blocked), 'w=', w, 'order', order, flush=True)
                print(reproduce(g, s, t, w, order), flush=True)
    print(f'seed {seed}: instances {n_inst}, order-failable {n_failable}, failable by shape {shapes_fail}')
    for w in WS:
        v, inst = best[w]
        print(f'  w={w:g}: best (minimal) slack of a failing order = {v:.3f}  slack/w={v / w:.3f}  at {inst}')
