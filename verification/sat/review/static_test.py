"""Check the STATIC layer of enc.py (forced sides, straight/diagonal ray returns `ret`, t-visibility `tvis`, and the
successor-direction logic `inS`) against the reference jpswa.CanonicalJPS on random fixed grids.
Method: record the constraints Encoding() adds, keep the prefix that precedes the first dynamic constraint
(variables cl_/bef_/par_/A_/B_/dl_), fix the grid, get a z3 model, and compare, for every cell z and direction e:
   ret[(z,e,y)]  <->  reference jump(z,e) returns y (with t far away, i.e. ignoring the stop at t)
   tvis[(z,e)]   <->  reference jump(z,e) (with the real t) steps on t
and the successor sets for every arrival direction (via the inS terms evaluated under a forced delta)."""
import sys, random, itertools
sys.path.insert(0, '/path/to/jps-wa/verification/sat')
sys.path.insert(0, '/path/to/jps-wa/verification/round3')
sys.path.insert(0, '/path/to/jps-wa/ref')
import z3
from enc import Encoding, DIRS, STRAIGHT, DIAG
from jpswa import Grid, CanonicalJPS
from core import ReplayJPS


class Rec:
    def __init__(self): self.cs = []
    def add(self, *a): self.cs.extend(a)


DYN = ('cl_', 'bef_', 'par_', 'A_', 'B_', 'dl_', 'dl0_', 'inS_', 'arc_', 'rl_')


def is_static(c):
    s = str(c)
    return not any(tok in s for tok in DYN)


def main(seed=11, n=10):
    rng = random.Random(seed)
    bad = 0; checked = 0
    for it in range(n):
        N = rng.choice([5, 5, 6])
        dens = rng.choice([0.1, 0.25, 0.4])
        bl = {(x, y) for x in range(N) for y in range(N) if rng.random() < dens}
        t = (rng.randrange(N), rng.randrange(N)); bl.discard(t)
        rec = Rec()
        E = Encoding(N, t, (1, 1), wa=False, eqg=False, fixed_grid=bl, solver=rec, lazy=True)
        sol = z3.Solver()
        for c in rec.cs:
            if is_static(c): sol.add(c)
        assert sol.check() == z3.sat
        m = sol.model()
        ev = lambda v: z3.is_true(m.eval(v, model_completion=True))
        grid = Grid(N, N, bl)
        Jfar = CanonicalJPS(grid, (0, 0), (-99, -99), 1.0, 'hig')      # ignores t
        Jt = ReplayJPS(grid, (0, 0), t, 1.0, [])                        # real t, records visited
        for z in E.cells:
            if z in bl: continue
            for e in DIRS:
                r = Jfar.jump(z[0], z[1], e[0], e[1], 0.0)
                rc = None if r is None else (r[0], r[1])
                for y in E.ray(z, e):
                    checked += 1
                    if ev(E.ret[(z, e, y)]) != (rc == y):
                        bad += 1; print('ret mismatch', N, sorted(bl), t, z, e, y, rc)
                Jt.visited = set()
                Jt.jump(z[0], z[1], e[0], e[1], 0.0)
                if ev(E.tvis[(z, e)]) != (t in Jt.visited):
                    bad += 1; print('tvis mismatch', N, sorted(bl), t, z, e, ev(E.tvis[(z, e)]), t in Jt.visited)
            # successor sets: evaluate the inS terms under each arrival direction (static part of inS)
            for d in [(0, 0)] + DIRS:
                refs = set(Jfar.successor_dirs(z[0], z[1], d[0], d[1]))
                for e in DIRS:
                    # rebuild the condition of inS[(z,e)] as in enc.py, with delta fixed to d
                    cond = False
                    if d == (0, 0): cond = True
                    elif d == e: cond = True
                    elif e in STRAIGHT:
                        if d in DIAG and ((e[0] and d[0] == e[0]) or (e[1] and d[1] == e[1])): cond = True
                        if d in STRAIGHT and (d[0] != 0) != (e[0] != 0):
                            cond = ev(E.forced[(z, d)]) and ev(z3.Bool(f'fs_{z[0]}_{z[1]}_{d[0]}{d[1]}_{e[0]}{e[1]}'))
                    else:
                        if d in STRAIGHT and d[0] and d[0] == e[0]:
                            cond = ev(z3.Bool(f'fs_{z[0]}_{z[1]}_{d[0]}{d[1]}_0{e[1]}'))
                        if d in STRAIGHT and d[1] and d[1] == e[1]:
                            cond = ev(z3.Bool(f'fs_{z[0]}_{z[1]}_{d[0]}{d[1]}_{e[0]}0'))
                    checked += 1
                    if bool(cond) != (e in refs):
                        bad += 1; print('succ mismatch', N, sorted(bl), t, z, d, e, cond, e in refs)
    print(f'static checks: {checked} comparisons, {bad} mismatches')


if __name__ == '__main__':
    main()
