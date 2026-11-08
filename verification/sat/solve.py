"""Common solve routine: build Encoding into a z3 Goal, bit-blast to CNF, solve with CaDiCaL; on SAT recover the full
model with z3 (assumptions = the named Booleans) and return the extracted run.  Also offers the plain z3 path."""
import sys, time
sys.path.insert(0, '/path/to/jps-wa/verification/sat')
import z3
from enc import Encoding, to_cnf, solve_cnf, check_model


def solve(N, t, w, wa=True, eqg=True, fixed_grid=None, fixed_s=None, sym_s=False, timeout=None, max_blocked=None,
          engine='cadical', verbose=False):
    """returns dict(status, build, solve, res, stats)"""
    t0 = time.time()
    g = z3.Goal()
    E = Encoding(N, t, w=w, wa=wa, eqg=eqg, fixed_grid=fixed_grid, fixed_s=fixed_s, sym_s=sym_s, solver=g,
                 max_blocked=max_blocked)
    tb = time.time() - t0
    out = dict(N=N, t=t, w=w, build=tb, res=None, stats={})
    if engine == 'z3':
        sol = z3.Solver()
        if timeout: sol.set('timeout', int(timeout * 1000))
        sol.add(g)
        t1 = time.time(); r = sol.check(); out['solve'] = time.time() - t1
        out['status'] = 'sat' if r == z3.sat else ('unsat' if r == z3.unsat else 'timeout')
        if r == z3.sat:
            out['res'] = E.extract(sol.model())
        return out
    t1 = time.time()
    clauses, nv, names = to_cnf(g)
    tc = time.time() - t1
    out['stats'] = dict(vars=nv, clauses=len(clauses), named=len(names), cnf_time=round(tc, 1), n_wa=E.n_wa)
    if verbose:
        print('cnf', out['stats'], flush=True)
    t1 = time.time()
    status, val = solve_cnf(clauses, names, timeout=timeout)
    out['solve'] = time.time() - t1
    out['status'] = status
    if status == 'sat':
        # recover the complete model with z3 under the CaDiCaL assignment of the named Booleans
        sol = z3.Solver(); sol.add(g)
        assumptions = [E.names[n] if v else z3.Not(E.names[n]) for n, v in val.items() if n in E.names]
        r = sol.check(*assumptions)
        if r != z3.sat:
            out['status'] = 'sat-but-z3-recovery-failed'
        else:
            out['res'] = E.extract(sol.model())
    return out
