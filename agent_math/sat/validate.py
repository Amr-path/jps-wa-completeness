"""Validation (ii): on FIXED grids the SMT encoding must agree with the faithful Python adversaries of round3/core.py:
   wa=False  <->  any-order adversary (every live entry may be popped)      [order-dependence]
   wa=True   <->  wa_adversary(grid, s, t, w)                                [WA*-realisable failure]
Every SAT model is replayed (check_model) with the Model and with the reference CanonicalJPS (ReplayJPS)."""
import sys, time, random, math
sys.path.insert(0, '/home/claude/jps-wa/agent_math/sat')
sys.path.insert(0, '/home/claude/jps-wa/agent_math/round3')
sys.path.insert(0, '/home/claude/jps-wa/ref')
import z3
from enc import Encoding, check_model
from core import Model, wa_adversary, _succ_state, pinwheel1
from jpswa import Grid, octile


def any_adversary(grid, s, t, limit=3_000_000):
    """Faithful model, arbitrary pop order (any live entry).  'FAIL' iff some order empties Open without stepping on t."""
    M = Model(grid, s)
    start = (frozenset(), ((s, 0.0, None),))
    seen = set(); stack = [(start, [])]; n = 0
    while stack:
        (closed, open_), order = stack.pop()
        key = (closed, open_)
        if key in seen: continue
        seen.add(key); n += 1
        if n > limit: return 'limit', None
        if not open_: return 'FAIL', order
        od = {c: (g, p) for c, g, p in open_}
        for x, (gx, px) in od.items():
            if x == t: continue
            nc, no, vis = _succ_state(M, closed, od, x, gx, px, t)
            if t in no: continue
            stack.append(((nc, tuple(sorted((c, g, p) for c, (g, p) in no.items()))), order + [x]))
    return 'complete', None


from solve import solve
def solve_fixed(N, blocked, s, t, w, wa, timeout_ms=600_000):
    o = solve(N, t, w, wa=wa, fixed_grid=blocked, fixed_s=s, timeout=timeout_ms / 1000, engine=ENGINE)
    return o['status'], o['solve'] + o['build'], o['res']
ENGINE = 'cadical'


def main(seed=1, n_inst=36):
    rng = random.Random(seed)
    insts = []
    # pinwheel 7x7 + one extra obstacle + random start (order-dependent ones exist here)
    while len(insts) < n_inst // 2:
        g, t = pinwheel1(N=7)
        extra = (rng.randrange(7), rng.randrange(7))
        bl = set(g.blocked) | {extra}
        s = (rng.randrange(7), rng.randrange(7))
        if s in bl or s == t or t in bl: continue
        grid = Grid(7, 7, bl)
        if math.isinf(__import__('jpswa').dijkstra(grid, s, t)): continue
        insts.append((7, bl, s, t))
    # random 6x6 grids
    while len(insts) < n_inst:
        N = 6
        bl = {(x, y) for x in range(N) for y in range(N) if rng.random() < 0.25}
        s = (rng.randrange(N), rng.randrange(N)); t = (rng.randrange(N), rng.randrange(N))
        if s in bl or t in bl or s == t: continue
        grid = Grid(N, N, bl)
        if math.isinf(__import__('jpswa').dijkstra(grid, s, t)): continue
        insts.append((N, bl, s, t))
    agree = 0; total = 0; nfail_any = 0
    for i, (N, bl, s, t) in enumerate(insts):
        grid = Grid(N, N, bl)
        a, _ = any_adversary(grid, s, t)
        r, dt, res = solve_fixed(N, bl, s, t, (1, 1), wa=False)
        ok = (a == 'FAIL') == (r == 'sat')
        extra = ''
        if res is not None:
            faithful, wa_ok, log, rep = check_model(res, 1.0)
            extra = f' replay_faithful={faithful}'
            ok = ok and faithful
        print(f'[{i}] N={N} s={s} t={t} |bl|={len(bl)} ANY-ORDER: adversary={a} sat={r} ({dt:.1f}s){extra} {"OK" if ok else "MISMATCH"}', flush=True)
        agree += ok; total += 1; nfail_any += (a == 'FAIL')
        for w in [(1, 1), (2, 1), (5, 1)]:
            wv = w[0] / w[1]
            a2, _ = wa_adversary(grid, s, t, wv)
            r2, dt2, res2 = solve_fixed(N, bl, s, t, w, wa=True)
            ok2 = (a2 == 'FAIL') == (r2 == 'sat')
            extra = ''
            if res2 is not None:
                faithful, wa_ok, log, rep = check_model(res2, wv)
                extra = f' replay faithful={faithful} wa_ok={wa_ok} ref={rep}'
                ok2 = ok2 and faithful and wa_ok
            print(f'      w={wv}: wa_adversary={a2} sat={r2} ({dt2:.1f}s){extra} {"OK" if ok2 else "MISMATCH"}', flush=True)
            agree += ok2; total += 1
    print(f'AGREE {agree}/{total}; order-dependent instances: {nfail_any}/{len(insts)}')


if __name__ == '__main__':
    if len(sys.argv) > 3: ENGINE = sys.argv[3]
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1, int(sys.argv[2]) if len(sys.argv) > 2 else 36)
