"""Static-layer check (v2 semantics): for random fixed grids and targets, ret[(z,e,y)] must equal
'reference CanonicalJPS.jump(z,e) with the REAL target t returns y' for every cell z, direction e, ray cell y
(this covers: straight rays stopping at t, sub-jumps stopping at t and thereby stopping the diagonal, diagonal stepping on t)."""
import sys, random
sys.path.insert(0, '/home/claude/jps-wa/agent_math/sat'); sys.path.insert(0, '/home/claude/jps-wa/ref')
import z3
from enc import Encoding, DIRS
from jpswa import Grid, CanonicalJPS

class Rec:
    def __init__(self): self.cs = []
    def add(self, *a): self.cs.extend(a)

DYN = ('cl_', 'bef_', 'par_', 'A_', 'B_', 'dl_', 'dl0_', 'inS_', 'arc_', 'rl_', 'abit', 'bbit')

def main(seed=1, n=40):
    rng = random.Random(seed); bad = checked = n_ret_t = n_diag_t = 0
    for it in range(n):
        N = rng.choice([5, 6, 7]); dens = rng.choice([0.05, 0.15, 0.3])
        bl = {(x, y) for x in range(N) for y in range(N) if rng.random() < dens}
        t = (rng.randrange(N), rng.randrange(N)); bl.discard(t)
        rec = Rec(); E = Encoding(N, t, (1, 1), wa=False, eqg=False, fixed_grid=bl, solver=rec, lazy=True)
        sol = z3.Solver()
        for c in rec.cs:
            if not any(tok in str(c) for tok in DYN): sol.add(c)
        assert sol.check() == z3.sat
        m = sol.model(); ev = lambda v: z3.is_true(m.eval(v, model_completion=True))
        J = CanonicalJPS(Grid(N, N, bl), (0, 0), t, 1.0, 'hig')
        Jfar = CanonicalJPS(Grid(N, N, bl), (0, 0), (-99, -99), 1.0, 'hig')
        for z in E.cells:
            if z in bl: continue
            for e in DIRS:
                r = J.jump(z[0], z[1], e[0], e[1], 0.0); rc = None if r is None else (r[0], r[1])
                rf = Jfar.jump(z[0], z[1], e[0], e[1], 0.0); rfc = None if rf is None else (rf[0], rf[1])
                if rc == t: n_ret_t += 1
                if rc != rfc and rc != t: n_diag_t += 1   # diagonal stopped early because a sub-jump hit t
                for y in E.ray(z, e):
                    checked += 1
                    if ev(E.ret[(z, e, y)]) != (rc == y):
                        bad += 1; print('ret mismatch', N, sorted(bl), t, z, e, y, 'ref', rc)
    print(f'checked {checked} (z,e,y) triples on {n} grids: {bad} mismatches; scans returning t: {n_ret_t}; '
          f'diagonals stopped by a sub-jump hitting t: {n_diag_t}')

if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1, int(sys.argv[2]) if len(sys.argv) > 2 else 40)
