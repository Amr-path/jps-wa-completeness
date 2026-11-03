"""SMT encoding (z3) of a complete run of cell-closing canonical JPS (no corner cutting) under WA* ordering
f_w = g + w*h on a VARIABLE N x N grid, ending with Open empty and the target t never stepped on.

Order-free ("certificate") encoding: no explicit time steps.  Each cell x has
   closed[x]      : x is expanded during the run
   T[x]  (bef[x,y]       : strict total order on cells (closing order; only closed cells' positions matter)
   par[z,x]       : the expansion of z generated the entry with which x is closed (x's parent)
   delta[x][e]    : arrival direction of x (direction of the ray from par to x); delta0[x] for the start
   A[x], B[x]     : g(x) = A + B*sqrt2 (number of straight / diagonal steps on the parent chain)
The static part (rays, forced sides, returned cells, visited cells) is a Boolean function of blocked[].
The dynamic semantics (exactly those of ref/jpswa.py CanonicalJPS.search, equivalently round3/core.py):
   arc(z,y)  := closed[z] and e(z,y) in succ(z, delta(z)) and Jump(z, e(z,y)) returns y        (static given delta)
   (open empties)       arc(z,y) -> closed[y]
   (closing)            closed[y], y != s  ->  exactly one parent p with arc(p,y), T[p] < T[y]
   (g = min)            arc(z,y), T[z] < T[y]  ->  g(y) <= g(z) + c(z,y)
   (first at equal g)   par[p,y], arc(z,y), T[z] < T[p]  ->  g(z) + c(z,y) > g(y)
   (WA*)                closed[x], arc(z,y), T[z] < T[x] < T[y]  ->  g(x) + w h(x) <= g(z) + c(z,y) + w h(y)
   (failure)            for every closed z and e in succ(z,delta(z)): the scan Jump(z,e) does not step on t
   (t reachable)        4-connected reachability of t from s through free cells (equivalent to 8-connected).
Numbers a + b*sqrt2 are compared through the fixed-point value V = a*S + b*R, S = 2^28, R = round(sqrt2*S), as 56-bit
bit-vectors.  This is EXACT for the magnitudes occurring here: a comparison of two such numbers is the sign of
D = da + db*sqrt2 with |da|,|db| <= M; if D != 0 then |D| = |da^2 - 2 db^2| / |da - db sqrt2| >= 1/(M(1+sqrt2)), while the
rounding error is |db| * |R/S - sqrt2| <= M * 2^-(FB+1); the encoding asserts M * 2^-(FB+1) < 1/(2.42 M).  If D = 0 then
da = db = 0 (sqrt2 irrational) and the fixed-point values coincide exactly.
w = p/q rational.
"""
import sys, math, itertools, time
import z3
sys.path.insert(0, '/home/claude/jps-wa/ref')
sys.path.insert(0, '/home/claude/jps-wa/agent_math/round3')

S_SCALE = 10 ** 15
R_SCALE = 1414213562373095  # round(sqrt(2) * 1e15)
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
STRAIGHT = DIRS[:4]
DIAG = DIRS[4:]


def oct_pair(a, b):
    """octile distance as (p, q) meaning p + q*sqrt2  (oct = max + (sqrt2-1) min)."""
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    mn, mx = min(dx, dy), max(dx, dy)
    return (mx - mn, mn)


def scaled(p, q):
    return p * S_SCALE + q * R_SCALE


def sgn(v):
    return (v > 0) - (v < 0)


class Encoding:
    def __init__(self, N, t, w=(1, 1), wa=True, fixed_grid=None, fixed_s=None, sym_s=False, solver=None):
        """N: grid side; t: fixed target cell; w = (p, q) weight p/q; wa: include the WA* ordering constraint;
        fixed_grid: optional set of blocked cells (grid fixed); fixed_s: optional start cell;
        sym_s: break the symmetries fixing t (only when fixed_grid is None)."""
        self.N, self.t, self.wp, self.wq = N, t, w[0], w[1]
        self.sol = solver or z3.Solver()
        s = self.sol
        cells = [(x, y) for y in range(N) for x in range(N)]
        self.cells = cells
        idx = {c: i for i, c in enumerate(cells)}
        self.idx = idx
        B = z3.Bool
        TRUE, FALSE = z3.BoolVal(True), z3.BoolVal(False)

        # ---------------- grid
        blocked = {c: B(f'bl_{c[0]}_{c[1]}') for c in cells}
        self.blocked = blocked

        def free(c):
            if not (0 <= c[0] < N and 0 <= c[1] < N):
                return FALSE
            return z3.Not(blocked[c])

        def isblocked(c):
            if not (0 <= c[0] < N and 0 <= c[1] < N):
                return TRUE
            return blocked[c]

        if fixed_grid is not None:
            for c in cells:
                s.add(blocked[c] if c in fixed_grid else z3.Not(blocked[c]))
        s.add(z3.Not(blocked[t]))

        isS = {c: B(f'isS_{c[0]}_{c[1]}') for c in cells}
        self.isS = isS
        s.add(z3.PbEq([(isS[c], 1) for c in cells], 1))
        s.add(z3.Not(isS[t]))
        for c in cells:
            s.add(z3.Implies(isS[c], z3.Not(blocked[c])))
        if fixed_s is not None:
            s.add(isS[fixed_s])
        if sym_s and fixed_grid is None:
            # EXACT symmetries of the algorithm: reflections in the vertical / horizontal axis (and their product).
            # (Diagonal reflections / 90-degree rotations are NOT used: the horizontal sub-jump is executed before the
            # vertical one with short-circuit, so the visited set is not invariant under x<->y.)
            # If such a reflection fixes t, restrict s to the half-grid on one side of the axis.
            cx = cy = (N - 1) / 2
            for c in cells:
                if (t[0] * 2 == N - 1 and c[0] > cx) or (t[1] * 2 == N - 1 and c[1] > cy):
                    s.add(z3.Not(isS[c]))

        # ---------------- static ray structure
        def ray(z, e):
            out = []
            c = (z[0] + e[0], z[1] + e[1])
            while 0 <= c[0] < N and 0 <= c[1] < N:
                out.append(c)
                c = (c[0] + e[0], c[1] + e[1])
            return out
        self.ray = ray

        def perp(e):
            return [(0, 1), (0, -1)] if e[0] else [(1, 0), (-1, 0)]

        # forced[y][e]: y has a forced side w.r.t. straight direction e
        forced = {}
        fside = {}  # fside[y][e][eps]
        for y in cells:
            for e in STRAIGHT:
                terms = []
                for ep in perp(e):
                    v = B(f'fs_{y[0]}_{y[1]}_{e[0]}{e[1]}_{ep[0]}{ep[1]}')
                    s.add(v == z3.And(isblocked((y[0] - e[0] + ep[0], y[1] - e[1] + ep[1])), free((y[0] + ep[0], y[1] + ep[1]))))
                    fside[(y, e, ep)] = v
                    terms.append(v)
                v = B(f'forced_{y[0]}_{y[1]}_{e[0]}{e[1]}')
                s.add(v == z3.Or(terms))
                forced[(y, e)] = v
        self.forced = forced

        def legal(x, e):
            if e[0] and e[1]:
                return z3.And(free((x[0] + e[0], x[1] + e[1])), free((x[0] + e[0], x[1])), free((x[0], x[1] + e[1])))
            return free((x[0] + e[0], x[1] + e[1]))

        # straight rays: pass[z,e,y] (ray from z in direction e steps onto y), sret[z,e,y] (returns y)
        pas = {}; sret = {}; sretany = {}
        for z in cells:
            for e in STRAIGHT:
                prev = None
                rets = []
                for y in ray(z, e):
                    v = B(f'pass_{z[0]}_{z[1]}_{e[0]}{e[1]}_{y[0]}_{y[1]}')
                    if prev is None:
                        s.add(v == free(y))
                    else:
                        s.add(v == z3.And(pas[(z, e, prev)], z3.Not(forced[(prev, e)]), free(y)))
                    pas[(z, e, y)] = v
                    r = B(f'sret_{z[0]}_{z[1]}_{e[0]}{e[1]}_{y[0]}_{y[1]}')
                    s.add(r == z3.And(v, forced[(y, e)]))
                    sret[(z, e, y)] = r
                    rets.append(r)
                    prev = y
                a = B(f'sretany_{z[0]}_{z[1]}_{e[0]}{e[1]}')
                s.add(a == z3.Or(rets) if rets else a == FALSE)
                sretany[(z, e)] = a
        # diagonal rays
        dpass = {}; dret = {}; dstop = {}
        for y in cells:
            for e in DIAG:
                v = B(f'dstop_{y[0]}_{y[1]}_{e[0]}{e[1]}')
                s.add(v == z3.Or(sretany[(y, (e[0], 0))], sretany[(y, (0, e[1]))]))
                dstop[(y, e)] = v
        for z in cells:
            for e in DIAG:
                prev = None
                for y in ray(z, e):
                    v = B(f'dpass_{z[0]}_{z[1]}_{e[0]}{e[1]}_{y[0]}_{y[1]}')
                    if prev is None:
                        s.add(v == legal(z, e))
                    else:
                        s.add(v == z3.And(dpass[(z, e, prev)], z3.Not(dstop[(prev, e)]), legal(prev, e)))
                    dpass[(z, e, y)] = v
                    r = B(f'dret_{z[0]}_{z[1]}_{e[0]}{e[1]}_{y[0]}_{y[1]}')
                    s.add(r == z3.And(v, dstop[(y, e)]))
                    dret[(z, e, y)] = r
                    prev = y
        ret = {}
        ret.update(sret); ret.update(dret)
        self.ret = ret

        # tvis[z,e]: the scan Jump(z,e) steps on t  (t fixed)
        def on_ray(z, e, c):
            d = (c[0] - z[0], c[1] - z[1])
            if e[0] == 0:
                return d[0] == 0 and sgn(d[1]) == e[1]
            if e[1] == 0:
                return d[1] == 0 and sgn(d[0]) == e[0]
            return abs(d[0]) == abs(d[1]) and d[0] != 0 and sgn(d[0]) == e[0] and sgn(d[1]) == e[1]
        tvis = {}
        for z in cells:
            for e in DIRS:
                if e in STRAIGHT:
                    tvis[(z, e)] = pas[(z, e, t)] if on_ray(z, e, t) else FALSE
                else:
                    terms = []
                    ea, eb = (e[0], 0), (0, e[1])
                    for y in ray(z, e):
                        if y == t:
                            terms.append(dpass[(z, e, y)])
                        elif on_ray(y, ea, t):
                            terms.append(z3.And(dpass[(z, e, y)], pas[(y, ea, t)]))
                        elif on_ray(y, eb, t):
                            terms.append(z3.And(dpass[(z, e, y)], z3.Not(sretany[(y, ea)]), pas[(y, eb, t)]))
                    tvis[(z, e)] = z3.Or(terms) if terms else FALSE
        self.tvis = tvis

        # ---------------- dynamic part (SAT-friendly)
        # strict total order on cells: bef[x][y]  (x closed before y).  Only closed cells' positions matter.
        closed = {c: B(f'cl_{c[0]}_{c[1]}') for c in cells}
        bef = {}
        for i, x in enumerate(cells):
            for j, y in enumerate(cells):
                if i < j:
                    bef[(x, y)] = B(f'bef_{x[0]}_{x[1]}_{y[0]}_{y[1]}')
                elif i > j:
                    bef[(x, y)] = z3.Not(bef[(y, x)])
        for x in cells:
            for y in cells:
                if x == y: continue
                for zc in cells:
                    if zc == x or zc == y: continue
                    s.add(z3.Or(z3.Not(bef[(x, y)]), z3.Not(bef[(y, zc)]), bef[(x, zc)]))
        self.bef = bef
        # g(x) = A + B sqrt2 as bit-vectors; fixed-point value V = A*S + B*R  (S = 2^FB, R = round(sqrt2 * S))
        GB = self.GB = 10            # A, B < 1024
        FB = self.FB = 28
        S_FP = 1 << FB
        R_FP = round(math.sqrt(2) * S_FP)
        self.S_FP, self.R_FP = S_FP, R_FP
        VB = self.VB = 56
        A = {c: z3.BitVec(f'A_{c[0]}_{c[1]}', GB) for c in cells}
        Bc = {c: z3.BitVec(f'B_{c[0]}_{c[1]}', GB) for c in cells}
        delta = {c: {e: B(f'dl_{c[0]}_{c[1]}_{e[0]}{e[1]}') for e in DIRS} for c in cells}
        delta0 = {c: B(f'dl0_{c[0]}_{c[1]}') for c in cells}
        self.closed, self.A, self.Bc, self.delta, self.delta0 = closed, A, Bc, delta, delta0
        AMAX = N * N * (N - 1)       # a parent chain has < N*N arcs of cost <= N-1 each
        assert AMAX < (1 << GB)
        for c in cells:
            s.add(z3.ULE(A[c], AMAX), z3.ULE(Bc[c], AMAX))
            s.add(z3.Implies(isS[c], z3.And(closed[c], A[c] == 0, Bc[c] == 0, delta0[c])))
            s.add(z3.Implies(z3.Not(isS[c]), z3.Not(delta0[c])))
            s.add(z3.Implies(closed[c], z3.Not(blocked[c])))
            s.add(z3.Implies(z3.Not(closed[c]), z3.And(A[c] == 0, Bc[c] == 0)))  # normalise
            s.add(z3.Implies(z3.And(closed[c], z3.Not(isS[c])), z3.PbEq([(delta[c][e], 1) for e in DIRS], 1)))
            s.add(z3.Implies(z3.Not(z3.And(closed[c], z3.Not(isS[c]))), z3.And([z3.Not(delta[c][e]) for e in DIRS])))
            # the start is closed first
            for d in cells:
                if d != c:
                    s.add(z3.Implies(isS[c], bef[(c, d)]))

        # inS[z][e]: e in succ(z, delta(z)) and z closed
        inS = {}
        for z in cells:
            for e in DIRS:
                terms = [delta0[z], delta[z][e]]
                if e in STRAIGHT:
                    for d in DIAG:
                        if (e[0] and d[0] == e[0]) or (e[1] and d[1] == e[1]):
                            terms.append(delta[z][d])
                    for d in STRAIGHT:
                        if (d[0] != 0) != (e[0] != 0):   # perpendicular
                            terms.append(z3.And(delta[z][d], fside[(z, d, e)]))
                else:
                    for d in STRAIGHT:
                        if d[0] and d[0] == e[0]:
                            terms.append(z3.And(delta[z][d], fside[(z, d, (0, e[1]))]))
                        if d[1] and d[1] == e[1]:
                            terms.append(z3.And(delta[z][d], fside[(z, d, (e[0], 0))]))
                v = B(f'inS_{z[0]}_{z[1]}_{e[0]}{e[1]}')
                s.add(v == z3.And(closed[z], z3.Or(terms)))
                inS[(z, e)] = v
        self.inS = inS

        arcs = []
        arc = {}
        for z in cells:
            for e in DIRS:
                for k, y in enumerate(ray(z, e), start=1):
                    v = B(f'arc_{z[0]}_{z[1]}_{y[0]}_{y[1]}')
                    s.add(v == z3.And(inS[(z, e)], ret[(z, e, y)]))
                    cost = (0, k) if (e[0] and e[1]) else (k, 0)
                    arc[(z, y)] = (v, e, cost)
                    arcs.append((z, y, e, cost))
        self.arc = arc
        self.arcs = arcs

        def V(c):
            return z3.ZeroExt(VB - GB, A[c]) * S_FP + z3.ZeroExt(VB - GB, Bc[c]) * R_FP

        def const(p, q):
            return z3.BitVecVal(p * S_FP + q * R_FP, VB)

        def Varr(z, cost):
            return V(z) + const(*cost)

        par = {}
        for (z, y, e, cost) in arcs:
            par[(z, y)] = B(f'par_{z[0]}_{z[1]}_{y[0]}_{y[1]}')
        self.par = par
        in_arcs = {c: [] for c in cells}
        for (z, y, e, cost) in arcs:
            in_arcs[y].append((z, e, cost))
        for y in cells:
            for (z, e, cost) in in_arcs[y]:
                av = arc[(z, y)][0]
                s.add(z3.Implies(av, closed[y]))                      # Open empties
                p = par[(z, y)]
                s.add(z3.Implies(p, z3.And(av, bef[(z, y)], delta[y][e],
                                           A[y] == A[z] + cost[0], Bc[y] == Bc[z] + cost[1])))
                s.add(z3.Implies(z3.And(av, bef[(z, y)]), z3.ULE(V(y), Varr(z, cost))))   # g = min
            s.add(z3.Implies(z3.And(closed[y], z3.Not(isS[y])), z3.PbEq([(par[(z, y)], 1) for (z, e, c) in in_arcs[y]], 1)))
            s.add(z3.Implies(z3.Not(z3.And(closed[y], z3.Not(isS[y]))), z3.And([z3.Not(par[(z, y)]) for (z, e, c) in in_arcs[y]])))
            for (z, e, cost) in in_arcs[y]:
                for (z2, e2, cost2) in in_arcs[y]:
                    if z2 == z: continue
                    # earliest among the minimal arrivals
                    s.add(z3.Implies(z3.And(par[(z, y)], arc[(z2, y)][0], bef[(z2, z)]), z3.UGT(Varr(z2, cost2), V(y))))

        # WA* ordering:  closed x, arc (z,y), z before x before y  ->  q g(x) + p h(x) <= q (g(z)+c) + p h(y)
        H = {c: oct_pair(c, t) for c in cells}
        self.H = H
        wp, wq = self.wp, self.wq
        # exactness of the fixed-point comparison (see module docstring): coefficients bounded by
        #   |a|,|b| <= q*(2*AMAX + N) + p*N  =: M ;  need  M * 2^-(FB+1) < 1/(2.42 M)
        M = wq * (2 * AMAX + N) + wp * N
        assert M * 2.0 ** -(FB + 1) < 1.0 / (2.42 * M), 'fixed-point precision insufficient'
        assert wq * (AMAX * (S_FP + R_FP) + N * S_FP) + wp * N * (S_FP + R_FP) < (1 << VB), 'bit-width insufficient'
        if wa:
            for x in cells:
                Fx = wq * V(x) + const(wp * H[x][0], wp * H[x][1])
                for (z, y, e, cost) in arcs:
                    if y == x or z == x: continue
                    Fa = wq * Varr(z, cost) + const(wp * H[y][0], wp * H[y][1])
                    s.add(z3.Implies(z3.And(closed[x], arc[(z, y)][0], bef[(z, x)], bef[(x, y)]), z3.ULE(Fx, Fa)))

        # failure: no executed scan steps on t
        for z in cells:
            for e in DIRS:
                s.add(z3.Implies(inS[(z, e)], z3.Not(tvis[(z, e)])))
        # t reachable from s (4-connected): layered reachability with Boolean layers
        L = N * N
        rl = {(c, k): B(f'rl_{c[0]}_{c[1]}_{k}') for c in cells for k in range(L)}
        for c in cells:
            s.add(rl[(c, 0)] == isS[c])
            for k in range(1, L):
                nb = [rl[(c, k - 1)]]
                for e in STRAIGHT:
                    n = (c[0] + e[0], c[1] + e[1])
                    if 0 <= n[0] < N and 0 <= n[1] < N:
                        nb.append(rl[(n, k - 1)])
                s.add(rl[(c, k)] == z3.And(z3.Not(blocked[c]), z3.Or(nb)))
        s.add(rl[(t, L - 1)])

    # ------------------------------------------------------------------ model extraction
    def extract(self, m):
        N = self.N
        ev = lambda v: z3.is_true(m.eval(v, model_completion=True))
        blocked = {c for c in self.cells if ev(self.blocked[c])}
        sc = [c for c in self.cells if ev(self.isS[c])][0]
        closed = [c for c in self.cells if ev(self.closed[c])]
        def before(a, b):
            v = m.eval(self.bef[(a, b)], model_completion=True)
            return z3.is_true(v)
        import functools
        order = sorted(closed, key=functools.cmp_to_key(lambda a, b: 0 if a == b else (-1 if before(a, b) else 1)))
        gval = {c: (m.eval(self.A[c], model_completion=True).as_long(), m.eval(self.Bc[c], model_completion=True).as_long()) for c in closed}
        par = {}
        for (z, y), v in self.par.items():
            if z3.is_true(m.eval(v, model_completion=True)):
                par[y] = z
        return dict(N=N, blocked=blocked, s=sc, t=self.t, order=order, g=gval, parent=par)


def check_model(res, w):
    """Faithful replay of the extracted pop order with round3/core.py's Model (reference successor_dirs/jump) and
    with the reference CanonicalJPS via ReplayJPS.  Returns (faithful, wa_consistent, log, reference replay results)."""
    from jpswa import Grid, octile
    from core import Model, reproduce, EPS
    import math
    grid = Grid(res['N'], res['N'], res['blocked'])
    s, t, order = res['s'], res['t'], res['order']
    M = Model(grid, s)
    h = lambda c: octile(c[0], c[1], t[0], t[1])
    od = {s: (0.0, None)}
    closed = set()
    ok = True; wa_ok = True
    log = []
    for x in order:
        if x not in od:
            log.append(f'{x} popped but not in Open'); ok = False; break
        gx, px = od[x]
        fmin = min(g + w * h(c) for c, (g, p) in od.items())
        if gx + w * h(x) > fmin + EPS:
            log.append(f'{x} popped with f={gx + w * h(x):.4f} > fmin={fmin:.4f}'); wa_ok = False
        d = M.dir_from(x, px)
        jps, vis = M.expand(x, d)
        if t in vis:
            log.append(f'expansion of {x} steps on t'); ok = False
        closed.add(x); del od[x]
        for (j, c) in jps:
            if j in closed:
                continue
            jg = gx + c
            if jg < od.get(j, (math.inf,))[0] - 1e-12:
                od[j] = (jg, x)
    if od:
        log.append(f'Open not empty at end: {od}'); ok = False
    rep = reproduce(grid, s, t, w, order)
    return ok, wa_ok, log, rep
