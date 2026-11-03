"""SAT/SMT encoding of a complete run of cell-closing canonical JPS (no corner cutting) under WA* ordering
f_w = g + w*h on a VARIABLE N x N grid, ending with Open empty and the target t never stepped on.

Order-free ("certificate") encoding: no explicit time steps.  Variables (all Boolean except A,B):
   blocked[c]     : grid
   isS[c]         : start (one-hot); t is a fixed parameter
   closed[x]      : x is expanded during the run
   bef[x,y]       : strict total order on cells (closing order; only closed cells' positions matter)
   par[z,x]       : the expansion of z generated the entry with which x is closed (x's parent)
   delta[x][e]    : arrival direction of x (direction of the ray from par to x); delta0[x] for the start
   A[x], B[x]     : g(x) = A + B*sqrt2 (bit-vectors: number of straight / diagonal steps on the parent chain)
The static part (rays, forced sides, returned cells, visited cells) is a Boolean function of blocked[].
Dynamic semantics (exactly those of ref/jpswa.py CanonicalJPS.search, equivalently round3/core.py Model):
   arc(z,y)  := closed[z] and e(z,y) in succ(z, delta(z)) and Jump(z, e(z,y)) returns y        (static given delta)
   (open empties)       arc(z,y) -> closed[y]
   (closing)            closed[y], y != s  ->  exactly one parent p with arc(p,y), p bef y
   (g = min)            arc(z,y), z bef y  ->  g(y) <= g(z) + c(z,y)
   (first at equal g)   par[p,y], arc(z,y), z bef p  ->  g(z) + c(z,y) > g(y)          [optional: eqg=True]
   (WA*)                closed[x], arc(z,y), z bef x bef y  ->  q g(x) + p h(x) <= q (g(z) + c(z,y)) + p h(y)
   (failure)            t is never returned by a top-level scan, i.e. no arc(z,t) (equivalently closed[t] is false).
                        Every ray, top-level or sub-jump, stops when it steps on t (as the reference jump()); a sub-jump
                        reaching t makes the enclosing diagonal return the diagonal cell, which is pushed, not t.
   (t reachable)        4-connected reachability of t from s through free cells (equivalent to 8-connected).
Arithmetic.  Numbers a + b*sqrt2 (a, b integers, |a|,|b| <= M) are compared through V = S*a + R*b where R/S is a
continued-fraction convergent of sqrt2 chosen with |R/S - sqrt2| < 1/(2.42 M^2).  This is EXACT: for D = da + db*sqrt2
with |da|,|db| <= M and D != 0, |D| = |da^2 - 2db^2| / |da - db*sqrt2| >= 1/(M(1+sqrt2)) while |D - (S da + R db)/S| =
|db| |sqrt2 - R/S| < 1/(2.42 M) <= |D|, so the signs agree; D = 0 forces da = db = 0 (sqrt2 irrational) and then the
approximation is 0 as well.  All comparisons are of the form  (linear form in V-values)  <=  constant, implemented with
shared bit-vector subtractors and comparisons against constants.
"""
import sys, math, itertools, time, functools
from fractions import Fraction
import z3
sys.path.insert(0, '/home/claude/jps-wa/ref')
sys.path.insert(0, '/home/claude/jps-wa/agent_math/round3')

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
STRAIGHT = DIRS[:4]
DIAG = DIRS[4:]
CONVERGENTS = [(1393, 985), (3363, 2378), (8119, 5741), (19601, 13860), (47321, 33461), (114243, 80782),
               (275807, 195025), (665857, 470832)]  # (R, S) with R/S -> sqrt2


def oct_pair(a, b):
    """octile distance as (p, q) meaning p + q*sqrt2  (oct = max + (sqrt2-1) min)."""
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    mn, mx = min(dx, dy), max(dx, dy)
    return (mx - mn, mn)


def sgn(v):
    return (v > 0) - (v < 0)


def choose_convergent(M):
    """smallest convergent R/S with |R/S - sqrt2| < 1/(2.42 M^2), checked with exact rational arithmetic:
       |R/S - sqrt2| < eps  <=>  (R/S - eps)^2 < 2 < (R/S + eps)^2 (all terms positive)."""
    eps = Fraction(1, int(2.42 * M * M) + 1)
    for R, S in CONVERGENTS:
        r = Fraction(R, S)
        if (r - eps) ** 2 < 2 < (r + eps) ** 2:
            return R, S
    raise ValueError('no convergent precise enough')


class Encoding:
    def __init__(self, N, t, w=(1, 1), wa=True, eqg=True, fixed_grid=None, fixed_s=None, sym_s=False, solver=None,
                 max_blocked=None, lazy=False, slack=(0, 0)):
        """N: grid side; t: fixed target cell; w = (p, q) weight p/q; wa: include the WA* ordering constraint;
        eqg: include the 'first arrival kept at equal g' rule (False = adversary may pick any minimal-g arrival);
        fixed_grid: optional set of blocked cells; fixed_s: optional start cell; sym_s: symmetry breaking on s;
        solver: object with .add (z3.Solver or z3.Goal);
        lazy: do not assert the WA* and eqg constraints; instead expose the bits of the differences D(x,z) = F(x) - q V(z)
        and E(z,y) = V(z) - V(y) as named Booleans so that the lazy driver (lazy.py) can add violated constraints as
        comparator circuits over them."""
        self.lazy = lazy
        self.slack = slack   # (a, b): the WA* constraint is relaxed to f(x) <= f_arrival + a + b*sqrt2 (validation only)
        self.N, self.t, self.wp, self.wq = N, t, w[0], w[1]
        self.sol = solver if solver is not None else z3.Solver()
        s = self.sol
        cells = [(x, y) for y in range(N) for x in range(N)]
        self.cells = cells
        B = z3.Bool
        TRUE, FALSE = z3.BoolVal(True), z3.BoolVal(False)
        self.names = {}  # name -> z3 Bool (for CNF model recovery)

        def NB(name):
            v = B(name); self.names[name] = v; return v

        # ---------------- grid
        blocked = {c: NB(f'bl_{c[0]}_{c[1]}') for c in cells}
        self.blocked = blocked

        def inb(c):
            return 0 <= c[0] < N and 0 <= c[1] < N

        def free(c):
            return z3.Not(blocked[c]) if inb(c) else FALSE

        def isblocked(c):
            return blocked[c] if inb(c) else TRUE

        if fixed_grid is not None:
            for c in cells:
                s.add(blocked[c] if c in fixed_grid else z3.Not(blocked[c]))
        if max_blocked is not None:
            s.add(z3.PbLe([(blocked[c], 1) for c in cells], max_blocked))
        s.add(z3.Not(blocked[t]))

        isS = {c: NB(f'isS_{c[0]}_{c[1]}') for c in cells}
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
            while inb(c):
                out.append(c)
                c = (c[0] + e[0], c[1] + e[1])
            return out
        self.ray = ray

        def perp(e):
            return [(0, 1), (0, -1)] if e[0] else [(1, 0), (-1, 0)]

        forced = {}
        fside = {}  # fside[(y, e, eps)]: y has forced side eps (perpendicular unit vector) w.r.t. straight e
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

        pas = {}; sret = {}; sretany = {}
        for z in cells:
            for e in STRAIGHT:
                prev = None; rets = []
                for y in ray(z, e):
                    v = B(f'pass_{z[0]}_{z[1]}_{e[0]}{e[1]}_{y[0]}_{y[1]}')
                    # a straight ray (top-level or sub-jump) stops at y if y has a forced side OR y == t (reference jump())
                    if prev is None:
                        s.add(v == free(y))
                    else:
                        s.add(v == z3.And(pas[(z, e, prev)], z3.Not(forced[(prev, e)]), prev != t, free(y)))
                    pas[(z, e, y)] = v
                    r = B(f'sret_{z[0]}_{z[1]}_{e[0]}{e[1]}_{y[0]}_{y[1]}')
                    s.add(r == (z3.And(v, forced[(y, e)]) if y != t else v))
                    sret[(z, e, y)] = r
                    rets.append(r)
                    prev = y
                a = B(f'sretany_{z[0]}_{z[1]}_{e[0]}{e[1]}')
                s.add(a == (z3.Or(rets) if rets else FALSE))
                sretany[(z, e)] = a
        dpass = {}; dret = {}; dstop = {}
        for y in cells:
            for e in DIAG:
                v = B(f'dstop_{y[0]}_{y[1]}_{e[0]}{e[1]}')
                # a diagonal scan stops at y if y == t or one of the two sub-jumps returns a cell (t included)
                s.add(v == (TRUE if y == t else z3.Or(sretany[(y, (e[0], 0))], sretany[(y, (0, e[1]))])))
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
        ret = {}; ret.update(sret); ret.update(dret)
        self.ret = ret

        # failure condition: t is never RETURNED by a top-level scan (t pushed <=> returned; a sub-jump reaching t only
        # makes the enclosing diagonal scan return its current cell).  Since arc(z,t) -> closed[t], it suffices to forbid
        # closed[t]; this is asserted in the dynamic part.

        # ---------------- dynamic part
        closed = {c: NB(f'cl_{c[0]}_{c[1]}') for c in cells}
        bef = {}
        for i, x in enumerate(cells):
            for j, y in enumerate(cells):
                if i < j:
                    bef[(x, y)] = NB(f'bef_{x[0]}_{x[1]}_{y[0]}_{y[1]}')
                elif i > j:
                    bef[(x, y)] = z3.Not(bef[(y, x)])
        for x in cells:
            for y in cells:
                if x == y: continue
                for zc in cells:
                    if zc == x or zc == y: continue
                    s.add(z3.Or(z3.Not(bef[(x, y)]), z3.Not(bef[(y, zc)]), bef[(x, zc)]))
        self.bef = bef
        # order symmetry breaking (sound: the order of unclosed cells is immaterial): every closed cell precedes every
        # unclosed cell, and unclosed cells are ordered by index.
        for i, x in enumerate(cells):
            for j, y in enumerate(cells):
                if i < j:
                    s.add(z3.Implies(z3.And(z3.Not(closed[x]), z3.Not(closed[y])), bef[(x, y)]))
                if x != y:
                    s.add(z3.Implies(z3.And(closed[x], z3.Not(closed[y])), bef[(x, y)]))

        AMAX = N * N * (N - 1)       # a parent chain has < N*N arcs of cost <= N-1 each
        GB = self.GB = max(1, AMAX).bit_length()
        wp, wq = self.wp, self.wq
        M = wq * (2 * AMAX + N + abs(slack[0]) + abs(slack[1])) + wp * N   # bound on |da|, |db| in every compared difference
        R_FP, S_FP = choose_convergent(M)
        self.R_FP, self.S_FP = R_FP, S_FP
        VMAX = (S_FP + R_FP) * (wq * (AMAX + abs(slack[0]) + abs(slack[1])) + wp * N)   # bound on every q*V + p*H term
        VB = self.VB = (2 * VMAX).bit_length() + 2    # signed differences fit
        A = {c: z3.BitVec(f'A_{c[0]}_{c[1]}', GB) for c in cells}
        Bc = {c: z3.BitVec(f'B_{c[0]}_{c[1]}', GB) for c in cells}
        delta = {c: {e: NB(f'dl_{c[0]}_{c[1]}_{e[0]}{e[1]}') for e in DIRS} for c in cells}
        delta0 = {c: NB(f'dl0_{c[0]}_{c[1]}') for c in cells}
        self.closed, self.A, self.Bc, self.delta, self.delta0 = closed, A, Bc, delta, delta0
        for c in cells:
            s.add(z3.ULE(A[c], AMAX), z3.ULE(Bc[c], AMAX))
            s.add(z3.Implies(isS[c], z3.And(closed[c], A[c] == 0, Bc[c] == 0, delta0[c])))
            s.add(z3.Implies(z3.Not(isS[c]), z3.Not(delta0[c])))
            s.add(z3.Implies(closed[c], z3.Not(blocked[c])))
            s.add(z3.Implies(z3.Not(closed[c]), z3.And(A[c] == 0, Bc[c] == 0)))  # normalise
            s.add(z3.Implies(z3.And(closed[c], z3.Not(isS[c])), z3.PbEq([(delta[c][e], 1) for e in DIRS], 1)))
            s.add(z3.Implies(z3.Not(z3.And(closed[c], z3.Not(isS[c]))), z3.And([z3.Not(delta[c][e]) for e in DIRS])))
            for d in cells:
                if d != c:
                    s.add(z3.Implies(isS[c], bef[(c, d)]))   # the start is closed first

        inS = {}
        for z in cells:
            for e in DIRS:
                terms = [delta0[z], delta[z][e]]
                if e in STRAIGHT:
                    for d in DIAG:   # (a,0) natural successor of (a,b)
                        if (e[0] and d[0] == e[0]) or (e[1] and d[1] == e[1]):
                            terms.append(delta[z][d])
                    for d in STRAIGHT:   # (0,eps) forced successor of (a,0) with forced side eps
                        if (d[0] != 0) != (e[0] != 0):
                            terms.append(z3.And(delta[z][d], fside[(z, d, e)]))
                else:
                    for d in STRAIGHT:   # (a,eps) forced successor of (a,0) with forced side (0,eps), and symmetric
                        if d[0] and d[0] == e[0]:
                            terms.append(z3.And(delta[z][d], fside[(z, d, (0, e[1]))]))
                        if d[1] and d[1] == e[1]:
                            terms.append(z3.And(delta[z][d], fside[(z, d, (e[0], 0))]))
                v = B(f'inS_{z[0]}_{z[1]}_{e[0]}{e[1]}')
                s.add(v == z3.And(closed[z], z3.Or(terms)))
                inS[(z, e)] = v
        self.inS = inS

        arcs = []; arc = {}
        for z in cells:
            for e in DIRS:
                for k, y in enumerate(ray(z, e), start=1):
                    v = NB(f'arc_{z[0]}_{z[1]}_{y[0]}_{y[1]}')
                    s.add(v == z3.And(inS[(z, e)], ret[(z, e, y)]))
                    cost = (0, k) if (e[0] and e[1]) else (k, 0)
                    arc[(z, y)] = (v, e, cost)
                    arcs.append((z, y, e, cost))
        self.arc = arc; self.arcs = arcs

        # fixed-point values.  mulc: multiplication by a constant as shift-and-add (small circuits)
        def mulc(x, k):
            terms = [x << i for i in range(k.bit_length()) if (k >> i) & 1]
            out = terms[0]
            for tm in terms[1:]:
                out = out + tm
            return out

        def ext(v):
            return z3.ZeroExt(VB - GB, v)

        Vv = {c: mulc(ext(A[c]), S_FP) + mulc(ext(Bc[c]), R_FP) for c in cells}

        def const(p, q):
            return z3.BitVecVal(p * S_FP + q * R_FP, VB)

        def sconst(val):
            return z3.BitVecVal(val % (1 << VB), VB)

        H = {c: oct_pair(c, t) for c in cells}
        self.H = H
        # F(x) = q V(x) + p Hs(x)
        Fv = {c: mulc(Vv[c], wq) + const(wp * H[c][0], wp * H[c][1]) for c in cells}
        qV = {c: mulc(Vv[c], wq) for c in cells}

        par = {}
        for (z, y, e, cost) in arcs:
            par[(z, y)] = NB(f'par_{z[0]}_{z[1]}_{y[0]}_{y[1]}')
        self.par = par
        in_arcs = {c: [] for c in cells}
        for (z, y, e, cost) in arcs:
            in_arcs[y].append((z, e, cost))
        # E(y,z) = V(z) - V(y) (signed), one per arc
        Ediff = {}
        for (z, y, e, cost) in arcs:
            Ediff[(z, y)] = Vv[z] - Vv[y]
        for y in cells:
            for (z, e, cost) in in_arcs[y]:
                av = arc[(z, y)][0]
                s.add(z3.Implies(av, closed[y]))                      # Open empties
                p = par[(z, y)]
                s.add(z3.Implies(p, z3.And(av, bef[(z, y)], delta[y][e],
                                           A[y] == A[z] + cost[0], Bc[y] == Bc[z] + cost[1])))
                # g = min:  V(y) <= V(z) + c  <=>  V(z) - V(y) >= -c      (lazy mode: added by lazy.py on violation)
                if not lazy:
                    s.add(z3.Implies(z3.And(av, bef[(z, y)]), Ediff[(z, y)] >= sconst(-(cost[0] * S_FP + cost[1] * R_FP))))
            s.add(z3.Implies(z3.And(closed[y], z3.Not(isS[y])), z3.PbEq([(par[(z, y)], 1) for (z, e, c) in in_arcs[y]], 1)))
            s.add(z3.Implies(z3.Not(z3.And(closed[y], z3.Not(isS[y]))), z3.And([z3.Not(par[(z, y)]) for (z, e, c) in in_arcs[y]])))
            if eqg and not lazy:
                for (z, e, cost) in in_arcs[y]:
                    for (z2, e2, cost2) in in_arcs[y]:
                        if z2 == z: continue
                        # earliest among the minimal arrivals:  V(z2) + c2 > V(y)  <=>  V(z2) - V(y) > -c2
                        s.add(z3.Implies(z3.And(par[(z, y)], arc[(z2, y)][0], bef[(z2, z)]),
                                         Ediff[(z2, y)] > sconst(-(cost2[0] * S_FP + cost2[1] * R_FP))))

        # WA*:  closed x, arc (z,y), z bef x bef y  ->  F(x) <= q V(z) + q c + p Hs(y)   <=>  F(x) - qV(z) <= const
        self.n_wa = 0
        self.wa_on, self.eqg_on = wa, eqg
        if lazy:
            # expose the bits of A[c], B[c] as named Booleans; the lazy driver builds V, F, D, E and the comparators
            # itself (lazy.py) and adds violated WA* / eqg constraints incrementally.
            for c in cells:
                for i in range(GB):
                    v = NB(f'abit_{c[0]}_{c[1]}_{i}'); s.add(v == (z3.Extract(i, i, A[c]) == 1))
                    v = NB(f'bbit_{c[0]}_{c[1]}_{i}'); s.add(v == (z3.Extract(i, i, Bc[c]) == 1))
            self.Kwa = {}   # (z,y) -> K such that the WA constraint reads D(x,z) = F(x) - q V(z) <= K
            self.Keq = {}   # (z,y) -> K2 such that the eqg constraint reads E(z,y) = V(z) - V(y) > K2
            for (z, y, e, cost) in arcs:
                self.Kwa[(z, y)] = (wq * (cost[0] * S_FP + cost[1] * R_FP) + wp * (H[y][0] * S_FP + H[y][1] * R_FP)
                                    + wq * (slack[0] * S_FP + slack[1] * R_FP))
                self.Keq[(z, y)] = -(cost[0] * S_FP + cost[1] * R_FP)
            self.Hs = {c: H[c][0] * S_FP + H[c][1] * R_FP for c in cells}
        if wa and not lazy:
            D = {}
            for x in cells:
                for z in cells:
                    if z != x:
                        D[(x, z)] = Fv[x] - qV[z]
            for (z, y, e, cost) in arcs:
                av = arc[(z, y)][0]
                K = (wq * (cost[0] * S_FP + cost[1] * R_FP) + wp * (H[y][0] * S_FP + H[y][1] * R_FP)
                     + wq * (slack[0] * S_FP + slack[1] * R_FP))
                for x in cells:
                    if x == y or x == z: continue
                    s.add(z3.Implies(z3.And(closed[x], av, bef[(z, x)], bef[(x, y)]), D[(x, z)] <= sconst(K)))
                    self.n_wa += 1

        # failure: t is never returned by a top-level scan (arc(z,t) -> closed[t] is asserted above)
        s.add(z3.Not(closed[t]))
        # t reachable from s (4-connected): layered reachability
        L = N * N
        rl = {(c, k): B(f'rl_{c[0]}_{c[1]}_{k}') for c in cells for k in range(L)}
        for c in cells:
            s.add(rl[(c, 0)] == isS[c])
            for k in range(1, L):
                nb = [rl[(c, k - 1)]]
                for e in STRAIGHT:
                    n = (c[0] + e[0], c[1] + e[1])
                    if inb(n):
                        nb.append(rl[(n, k - 1)])
                s.add(rl[(c, k)] == z3.And(z3.Not(blocked[c]), z3.Or(nb)))
        s.add(rl[(t, L - 1)])

    # ------------------------------------------------------------------ model extraction
    def extract_from_bools(self, val):
        """val: name -> bool for the named Booleans.  g-values are recomputed from the parent chains."""
        N = self.N
        g = lambda name: bool(val.get(name, False))
        blocked = {c for c in self.cells if g(f'bl_{c[0]}_{c[1]}')}
        sc = [c for c in self.cells if g(f'isS_{c[0]}_{c[1]}')][0]
        closed = [c for c in self.cells if g(f'cl_{c[0]}_{c[1]}')]
        idx = {c: i for i, c in enumerate(self.cells)}

        def before(a, b):
            if idx[a] < idx[b]:
                return g(f'bef_{a[0]}_{a[1]}_{b[0]}_{b[1]}')
            return not g(f'bef_{b[0]}_{b[1]}_{a[0]}_{a[1]}')
        order = sorted(closed, key=functools.cmp_to_key(lambda a, b: 0 if a == b else (-1 if before(a, b) else 1)))
        par = {}
        for (z, y) in self.par:
            if g(f'par_{z[0]}_{z[1]}_{y[0]}_{y[1]}'):
                par[y] = z
        gval = {sc: (0, 0)}
        for c in order:
            if c == sc: continue
            p = par[c]; cost = self.arc[(p, c)][2]
            gval[c] = (gval[p][0] + cost[0], gval[p][1] + cost[1])
        return dict(N=N, blocked=blocked, s=sc, t=self.t, order=order, g=gval, parent=par)

    def extract(self, m):
        val = {name: z3.is_true(m.eval(v, model_completion=True)) for name, v in self.names.items()}
        return self.extract_from_bools(val)


# ---------------------------------------------------------------------- CNF / CaDiCaL path
def to_cnf(goal):
    """bit-blast a z3 Goal to CNF; returns (clauses, nvars, name->var map)."""
    tac = z3.Then('simplify', 'propagate-values', 'card2bv', 'bit-blast', 'tseitin-cnf')
    sub = tac(goal)
    assert len(sub) == 1
    d = sub[0].dimacs()
    clauses = []; names = {}
    nv = 0
    for line in d.split('\n'):
        if not line: continue
        if line[0] == 'p':
            nv = int(line.split()[2])
        elif line[0] == 'c':
            parts = line.split()
            if len(parts) == 3:
                names[parts[2]] = int(parts[1])
        else:
            lits = [int(x) for x in line.split()]
            if lits and lits[-1] == 0: lits.pop()
            clauses.append(lits)
    return clauses, nv, names


def solve_cnf(clauses, names, timeout=None):
    """CaDiCaL via pysat.  Returns (status, val) with status in {'sat','unsat','timeout'}; val: name -> bool.
    Named variables eliminated by the preprocessing tactics are absent from `names`; extract_from_bools treats them
    as False, so every model is re-checked by replay (always done by the drivers)."""
    from pysat.solvers import Cadical153
    import threading
    sol = Cadical153(bootstrap_with=clauses)
    if timeout:
        timer = threading.Timer(timeout, lambda: sol.interrupt())
        timer.start()
        r = sol.solve_limited(expect_interrupt=True)
        timer.cancel()
    else:
        r = sol.solve()
    if r is None:
        sol.delete(); return 'timeout', None
    if not r:
        sol.delete(); return 'unsat', None
    model = set(l for l in sol.get_model() if l > 0)
    val = {n: (v in model) for n, v in names.items() if not n.startswith('k!')}
    sol.delete()
    return 'sat', val


def check_model(res, w):
    """Faithful replay of the extracted pop order with round3/core.py's Model (reference successor_dirs/jump) and
    with the reference CanonicalJPS via ReplayJPS.  Returns (faithful, wa_consistent, log, reference replay results)."""
    from jpswa import Grid, octile
    from core import Model, reproduce, EPS
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
        jps, vis = M.expand(x, d, t)
        closed.add(x); del od[x]
        for (j, c) in jps:
            if j in closed:
                continue
            jg = gx + c
            if jg < od.get(j, (math.inf,))[0] - 1e-12:
                od[j] = (jg, x)
        if t in od:
            log.append(f'expansion of {x} pushes t'); ok = False
    if od:
        log.append(f'Open not empty at end: {od}'); ok = False
    rep = reproduce(grid, s, t, w, order)
    return ok, wa_ok, log, rep
