"""Lazy (CEGAR-style) driver.  Base CNF = Encoding(lazy=True) bit-blasted by z3 (Boolean structure, order, parents,
g = min, A/B adders).  The WA* constraints and the equal-g rule are added incrementally to CaDiCaL as exact comparator
circuits over the bits of V(c) = S*A[c] + R*B[c] (circuits built here, in CNF, with sharing), whenever the current model
violates one of them.  The loop ends with UNSAT (no run satisfies all constraints: every lazily added clause is one of
the constraints of the eager encoding, so this is the same UNSAT) or with a model violating nothing (then replayed).

Arithmetic in two's complement with VB bits (no overflow by the bounds in enc.py).  Comparisons are exact (see enc.py).
"""
import sys, time, math, functools, itertools
sys.path.insert(0, '/home/claude/jps-wa/agent_math/sat')
import z3
from pysat.solvers import Cadical153
from enc import Encoding, to_cnf, check_model, DIRS


class Circuits:
    """Tseitin circuits over pysat literals.  Numbers = lists of 'bits' LSB first; a bit is an int literal or a bool."""

    def __init__(self, nv, add_clause):
        self.nv = nv
        self.emit = add_clause
        self.ncl = 0

    def new(self):
        self.nv += 1
        return self.nv

    def clause(self, lits):
        # drop clauses with a True constant; remove False constants
        out = []
        for l in lits:
            if l is True: return
            if l is False: continue
            out.append(l)
        self.emit(out); self.ncl += 1

    @staticmethod
    def neg(b):
        return (not b) if isinstance(b, bool) else -b

    def AND(self, a, b):
        if a is False or b is False: return False
        if a is True: return b
        if b is True: return a
        v = self.new()
        self.clause([-v, a]); self.clause([-v, b]); self.clause([v, -a, -b])
        return v

    def OR(self, a, b):
        return self.neg(self.AND(self.neg(a), self.neg(b)))

    def XOR(self, a, b):
        if a is False: return b
        if b is False: return a
        if a is True: return self.neg(b)
        if b is True: return self.neg(a)
        v = self.new()
        self.clause([-v, a, b]); self.clause([-v, -a, -b]); self.clause([v, -a, b]); self.clause([v, a, -b])
        return v

    def full_add(self, a, b, c):
        s1 = self.XOR(a, b)
        s = self.XOR(s1, c)
        carry = self.OR(self.AND(a, b), self.AND(s1, c))
        return s, carry

    def add(self, x, y, width):
        """x + y mod 2^width"""
        x = x + [False] * (width - len(x)); y = y + [False] * (width - len(y))
        out = []; c = False
        for i in range(width):
            s, c = self.full_add(x[i], y[i], c)
            out.append(s)
        return out

    def const(self, k, width):
        k %= (1 << width)
        return [bool((k >> i) & 1) for i in range(width)]

    def mulc(self, x, k, width):
        """x * k mod 2^width for a constant k >= 0 (shift-and-add)"""
        acc = None
        for i in range(k.bit_length()):
            if (k >> i) & 1:
                term = ([False] * i + x)[:width]
                acc = term if acc is None else self.add(acc, term, width)
        return acc if acc is not None else self.const(0, width)

    def sub(self, x, y, width):
        """x - y mod 2^width = x + ~y + 1"""
        x = x + [False] * (width - len(x)); y = y + [False] * (width - len(y))
        ny = [self.neg(b) for b in y]
        out = []; c = True
        for i in range(width):
            s, c = self.full_add(x[i], ny[i], c)
            out.append(s)
        return out

    def le_const_signed(self, d, K, width):
        """literal/bool for  d <= K  (two's complement, width bits)"""
        K %= (1 << width)
        # flip the sign bit of both: unsigned order then equals signed order
        dd = list(d); dd[width - 1] = self.neg(dd[width - 1])
        KK = K ^ (1 << (width - 1))
        # unsigned dd <= KK:  scan from MSB; eq = prefix equality
        eq = True
        terms = []
        for i in range(width - 1, -1, -1):
            kb = (KK >> i) & 1
            if kb == 1:
                terms.append(self.AND(eq, self.neg(dd[i])))     # d has 0 where K has 1, prefix equal -> less
                eq = self.AND(eq, dd[i])
            else:
                eq = self.AND(eq, self.neg(dd[i]))
        terms.append(eq)   # equal
        res = False
        for tm in terms:
            res = self.OR(res, tm)
        return res


def exact_sign(a, b):
    """sign of a + b*sqrt2 for integers a, b"""
    if a >= 0 and b >= 0:
        return 0 if a == 0 and b == 0 else 1
    if a <= 0 and b <= 0:
        return -1
    if a > 0:   # b < 0
        return 1 if a * a > 2 * b * b else -1
    return 1 if 2 * b * b > a * a else -1    # a < 0 < b


class Meta:
    """metadata of an Encoding (no z3 objects): cells, arcs with direction and cost, constants, model extraction."""
    def __init__(self, d):
        self.__dict__.update(d)
        self.par = self.arc   # same key set (z, y)

    def extract_from_bools(self, val):
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
        for (z, y) in self.arc:
            if g(f'par_{z[0]}_{z[1]}_{y[0]}_{y[1]}'):
                par[y] = z
        gval = {sc: (0, 0)}
        for c in order:
            if c == sc: continue
            p = par[c]; cost = self.arc[(p, c)][1]
            gval[c] = (gval[p][0] + cost[0], gval[p][1] + cost[1])
        return dict(N=self.N, blocked=blocked, s=sc, t=self.t, order=order, g=gval, parent=par)


class LazySolver:
    def __init__(self, N, t, w=(1, 1), wa=True, eqg=True, fixed_grid=None, fixed_s=None, sym_s=False, max_blocked=None,
                 verbose=False, slack=(0, 0)):
        self.N, self.t, self.w, self.wa, self.eqg, self.slack = N, t, w, wa, eqg, slack
        self.verbose = verbose
        t0 = time.time()
        # build the CNF in a child process (z3 is isolated; its memory is released; a z3 crash is retried)
        import pickle, subprocess, tempfile, os
        args = dict(N=N, t=t, w=w, wa=wa, eqg=eqg, fixed_grid=fixed_grid, fixed_s=fixed_s, sym_s=sym_s,
                    max_blocked=max_blocked, slack=slack)
        tmp = tempfile.mkdtemp(prefix='jpscnf_', dir='/tmp')
        pa, pc, pm = os.path.join(tmp, 'args.pkl'), os.path.join(tmp, 'f.cnf'), os.path.join(tmp, 'meta.pkl')
        pickle.dump(args, open(pa, 'wb'))
        # optional: CNF prebuilt elsewhere with the same z3 (used when running on a machine with another z3)
        pre = os.environ.get('JPS_PREBUILT')
        if pre:
            b = os.path.join(pre, 'N%d_w%d_%d_%s_t%d%d' % (N, w[0], w[1], 'wa' if wa else 'noWA', t[0], t[1]))
            assert pickle.load(open(b + '.args.pkl', 'rb')) == args, 'prebuilt CNF built with different arguments'
            import shutil
            shutil.copy(b + '.cnf', pc); shutil.copy(b + '.meta.pkl', pm)
            print('using prebuilt CNF', b, flush=True)
        for attempt in range(0 if pre else 3):
            r = subprocess.run([sys.executable, '/home/claude/jps-wa/agent_math/sat/cnf_build.py', pa, pc, pm],
                               capture_output=True, text=True)
            if r.returncode == 0: break
            print('cnf_build failed (attempt %d): %s' % (attempt, r.stderr[-500:]), flush=True)
        else:
            if not pre: raise RuntimeError('cnf_build failed repeatedly')
        meta = pickle.load(open(pm, 'rb'))
        self.E = E = Meta(meta)
        self.names = meta['names']
        from pysat.formula import CNF
        cnf = CNF(from_file=pc)
        nv = cnf.nv
        self.build_time = time.time() - t0
        self.base_clauses = len(cnf.clauses)
        self.sol = Cadical153(bootstrap_with=cnf.clauses)
        del cnf
        for f in (pa, pc, pm): os.remove(f)
        os.rmdir(tmp)
        import gc; gc.collect()
        self.C = Circuits(nv, self.sol.add_clause)
        self.cells = E.cells
        self.idx = {c: i for i, c in enumerate(self.cells)}
        self.VB, self.GB = E.VB, E.GB
        self.S, self.R = E.S_FP, E.R_FP
        self.wp, self.wq = w[0], w[1]
        self.Vbits = {}     # cell -> bits of V(c)
        self.Fbits = {}     # cell -> bits of F(c) = q V(c) + p Hs(c)
        self.qVbits = {}
        self.Dbits = {}     # (x,z) -> bits of F(x) - q V(z)
        self.Ebits = {}     # (z,y) -> bits of V(z) - V(y)
        self.cmp_cache = {}
        self.n_wa_added = 0; self.n_eq_added = 0; self.n_min_added = 0
        self.fresh_names = {}

    # ---- literals for named variables (fresh unconstrained variable if the name was eliminated as irrelevant)
    def lit(self, name):
        if name in self.names: return self.names[name]
        if name not in self.fresh_names:
            self.fresh_names[name] = self.C.new()
        return self.fresh_names[name]

    def bef_lit(self, a, b):
        if self.idx[a] < self.idx[b]:
            return self.lit(f'bef_{a[0]}_{a[1]}_{b[0]}_{b[1]}')
        return -self.lit(f'bef_{b[0]}_{b[1]}_{a[0]}_{a[1]}')

    def Abits(self, c):
        return [self.lit(f'abit_{c[0]}_{c[1]}_{i}') for i in range(self.GB)]

    def Bbits(self, c):
        return [self.lit(f'bbit_{c[0]}_{c[1]}_{i}') for i in range(self.GB)]

    def V(self, c):
        if c not in self.Vbits:
            C = self.C; VB = self.VB
            self.Vbits[c] = C.add(C.mulc(self.Abits(c), self.S, VB), C.mulc(self.Bbits(c), self.R, VB), VB)
        return self.Vbits[c]

    def qV(self, c):
        if c not in self.qVbits:
            self.qVbits[c] = self.C.mulc(self.V(c), self.wq, self.VB) if self.wq != 1 else self.V(c)
        return self.qVbits[c]

    def F(self, c):
        if c not in self.Fbits:
            self.Fbits[c] = self.C.add(self.qV(c), self.C.const(self.wp * self.E.Hs[c], self.VB), self.VB)
        return self.Fbits[c]

    def D(self, x, z):
        if (x, z) not in self.Dbits:
            self.Dbits[(x, z)] = self.C.sub(self.F(x), self.qV(z), self.VB)
        return self.Dbits[(x, z)]

    def Ed(self, z, y):
        if (z, y) not in self.Ebits:
            self.Ebits[(z, y)] = self.C.sub(self.V(z), self.V(y), self.VB)
        return self.Ebits[(z, y)]

    def le(self, key, bits, K):
        if (key, K) not in self.cmp_cache:
            self.cmp_cache[(key, K)] = self.C.le_const_signed(bits, K, self.VB)
        return self.cmp_cache[(key, K)]

    def add_wa(self, x, z, y):
        """closed x, arc(z,y), z bef x bef y -> D(x,z) <= Kwa(z,y)"""
        le = self.le(('D', x, z), self.D(x, z), self.E.Kwa[(z, y)])
        self.C.clause([-self.lit(f'cl_{x[0]}_{x[1]}'), -self.lit(f'arc_{z[0]}_{z[1]}_{y[0]}_{y[1]}'),
                       -self.bef_lit(z, x), -self.bef_lit(x, y), le])
        self.n_wa_added += 1

    def add_min(self, z, y):
        """arc(z,y), z bef y -> V(y) <= V(z) + c  i.e.  not (E(z,y) <= -c-1)"""
        le = self.le(('E', z, y), self.Ed(z, y), self.E.Keq[(z, y)] - 1)
        self.C.clause([-self.lit(f'arc_{z[0]}_{z[1]}_{y[0]}_{y[1]}'), -self.bef_lit(z, y), Circuits.neg(le)])
        self.n_min_added += 1

    def add_eq(self, p, z2, y):
        """par(p,y), arc(z2,y), z2 bef p -> E(z2,y) > Keq(z2,y)  i.e.  not (E <= Keq)"""
        le = self.le(('E', z2, y), self.Ed(z2, y), self.E.Keq[(z2, y)])
        self.C.clause([-self.lit(f'par_{p[0]}_{p[1]}_{y[0]}_{y[1]}'), -self.lit(f'arc_{z2[0]}_{z2[1]}_{y[0]}_{y[1]}'),
                       -self.bef_lit(z2, p), Circuits.neg(le)])
        self.n_eq_added += 1

    # ---- model reading and checking
    def read_model(self):
        model = set(l for l in self.sol.get_model() if l > 0)
        val = {n: (v in model) for n, v in self.names.items() if not n.startswith('k!')}
        return val

    def violations(self, val):
        """exact check of the WA* and eqg constraints on the model; returns (list of wa triples, list of eq triples, res)"""
        E = self.E
        res = E.extract_from_bools(val)
        order = res['order']; pos = {c: i for i, c in enumerate(order)}
        g = res['g']
        # g-values from the bits must agree with the chain recomputation (sanity)
        for c in order:
            a = sum((1 << i) for i in range(self.GB) if val.get(f'abit_{c[0]}_{c[1]}_{i}', False))
            b = sum((1 << i) for i in range(self.GB) if val.get(f'bbit_{c[0]}_{c[1]}_{i}', False))
            assert (a, b) == g[c], ('bit/g mismatch', c, (a, b), g[c])
        arcs_on = [(z, y) for (z, y) in E.arc if val.get(f'arc_{z[0]}_{z[1]}_{y[0]}_{y[1]}', False)]
        wa_v = []; eq_v = []; min_v = []
        wp, wq = self.wp, self.wq
        H = E.H
        for (z, y) in arcs_on:   # g = min
            if pos[z] < pos[y]:
                cost = E.arc[(z, y)][1]
                if exact_sign(g[z][0] + cost[0] - g[y][0], g[z][1] + cost[1] - g[y][1]) < 0:
                    min_v.append((z, y))
        if self.wa:
            for (z, y) in arcs_on:
                cost = E.arc[(z, y)][1]
                gz = g[z]
                fa = (wq * (gz[0] + cost[0] + self.slack[0]) + wp * H[y][0], wq * (gz[1] + cost[1] + self.slack[1]) + wp * H[y][1])
                for x in order:
                    if x == z or x == y: continue
                    if not (pos[z] < pos[x] < pos[y]): continue
                    fx = (wq * g[x][0] + wp * H[x][0], wq * g[x][1] + wp * H[x][1])
                    if exact_sign(fx[0] - fa[0], fx[1] - fa[1]) > 0:   # F(x) > Fa : violation
                        wa_v.append((x, z, y))
        if self.eqg:
            par = res['parent']
            for y, p in par.items():
                for (z2, yy) in arcs_on:
                    if yy != y or z2 == p: continue
                    if pos[z2] < pos[p]:
                        cost2 = E.arc[(z2, y)][1]
                        va = (g[z2][0] + cost2[0] - g[y][0], g[z2][1] + cost2[1] - g[y][1])
                        if exact_sign(*va) <= 0:   # g(z2)+c2 <= g(y): earlier arrival at least as good -> violation
                            eq_v.append((p, z2, y))
        return wa_v, eq_v, min_v, res

    def run(self, timeout=None, max_iter=10 ** 6):
        """returns dict(status, iters, solve_time, res, ...)"""
        import threading
        t_start = time.time()
        it = 0
        while it < max_iter:
            it += 1
            remaining = None if timeout is None else timeout - (time.time() - t_start)
            if remaining is not None and remaining <= 0:
                return self.result('timeout', it, t_start)
            if remaining is not None:
                timer = threading.Timer(remaining, lambda: self.sol.interrupt()); timer.start()
                r = self.sol.solve_limited(expect_interrupt=True)
                timer.cancel()
                if r is None:
                    return self.result('timeout', it, t_start)
            else:
                r = self.sol.solve()
            if not r:
                return self.result('unsat', it, t_start)
            val = self.read_model()
            wa_v, eq_v, min_v, res = self.violations(val)
            if not wa_v and not eq_v and not min_v:
                out = self.result('sat', it, t_start); out['res'] = res
                return out
            for (x, z, y) in wa_v: self.add_wa(x, z, y)
            for (p, z2, y) in eq_v: self.add_eq(p, z2, y)
            for (z, y) in min_v: self.add_min(z, y)
            if self.verbose and (it % 20 == 0 or it < 5):
                print(f'   iter {it}: +{len(wa_v)} wa +{len(eq_v)} eq +{len(min_v)} min (total {self.n_wa_added}/{self.n_eq_added}/{self.n_min_added}, '
                      f'clauses {self.base_clauses + self.C.ncl}, {time.time() - t_start:.0f}s)', flush=True)
        return self.result('iter-limit', it, t_start)

    def result(self, status, it, t_start):
        return dict(status=status, iters=it, solve=time.time() - t_start, build=self.build_time, res=None,
                    stats=dict(base_clauses=self.base_clauses, added_clauses=self.C.ncl, wa_added=self.n_wa_added,
                               eq_added=self.n_eq_added, min_added=self.n_min_added, vars=self.C.nv))


def solve_lazy(N, t, w, wa=True, eqg=True, fixed_grid=None, fixed_s=None, sym_s=False, timeout=None, max_blocked=None,
               verbose=False, slack=(0, 0)):
    L = LazySolver(N, t, w, wa, eqg, fixed_grid, fixed_s, sym_s, max_blocked, verbose, slack)
    out = L.run(timeout=timeout)
    out['N'], out['t'], out['w'] = N, t, w
    L.sol.delete()
    return out


if __name__ == '__main__':
    # quick self-test on the pinwheel (fixed grid): wa=False -> sat (order failure), wa=True -> unsat
    bl = {(2, 3), (5, 2), (6, 5), (3, 6)}
    for wa in [False, True]:
        o = solve_lazy(9, (4, 4), (1, 1), wa=wa, fixed_grid=bl, fixed_s=(1, 1), verbose=True)
        print('wa', wa, o['status'], 'iters', o['iters'], 'build %.1f solve %.1f' % (o['build'], o['solve']), o['stats'])
        if o['res']:
            print(' order', o['res']['order'])
            print(' replay', check_model(o['res'], 1.0))
