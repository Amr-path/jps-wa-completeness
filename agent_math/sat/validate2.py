"""Validation (ii) of the lazy encoding on FIXED grids against the faithful Python adversaries (round3/core.py):
   (a) wa=False  <->  any-order adversary (every live entry may be popped)        [order-dependence]
   (b) wa=True   <->  wa_adversary(grid, s, t, w) for w in {1, 2, 5}              [WA*-realisable failure]
   (c) slack test: on order-dependent instances with exact min_slack sigma (a + b sqrt2) at w: the encoding with the
       WA* constraint relaxed by sigma must be SAT (and the model's max violation <= sigma), relaxed by sigma - 1 UNSAT.
Every SAT model is replayed with the faithful Model (check_model) and, for (b), with the reference CanonicalJPS."""
import sys, time, random, math
sys.path.insert(0, '/home/claude/jps-wa/agent_math/sat')
sys.path.insert(0, '/home/claude/jps-wa/agent_math/round3')
sys.path.insert(0, '/home/claude/jps-wa/ref')
from lazy import solve_lazy, exact_sign
from enc import check_model
from validate import any_adversary
from core import wa_adversary, min_slack, pinwheel1, Model
from jpswa import Grid, octile, dijkstra

SQ2 = math.sqrt(2)


def to_pair(v):
    for b in range(-60, 61):
        a = round(v - b * SQ2)
        if abs(a + b * SQ2 - v) < 1e-7 and abs(a) <= 200:
            return (a, b)
    return None


def max_violation(res, w):
    """max over pops of f(popped) - fmin in the faithful replay"""
    grid = Grid(res['N'], res['N'], res['blocked']); s, t = res['s'], res['t']
    M = Model(grid, s); h = lambda c: octile(c[0], c[1], t[0], t[1])
    od = {s: (0.0, None)}; closed = set(); worst = 0.0
    for x in res['order']:
        gx, px = od[x]
        fmin = min(g + w * h(c) for c, (g, p) in od.items())
        worst = max(worst, gx + w * h(x) - fmin)
        jps, vis = M.expand(x, M.dir_from(x, px), t)
        closed.add(x); del od[x]
        for (j, c) in jps:
            if j in closed: continue
            if gx + c < od.get(j, (math.inf,))[0] - 1e-12: od[j] = (gx + c, x)
    return worst


def main(seed=1, n_inst=36, N7=7, N6=6):
    rng = random.Random(seed)
    insts = []
    while len(insts) < n_inst // 2:
        g, t = pinwheel1(N=N7)
        extra = (rng.randrange(N7), rng.randrange(N7))
        bl = set(g.blocked) | {extra}
        s = (rng.randrange(N7), rng.randrange(N7))
        if s in bl or s == t or t in bl: continue
        if math.isinf(dijkstra(Grid(N7, N7, bl), s, t)): continue
        insts.append((N7, bl, s, t))
    while len(insts) < n_inst:
        N = N6
        bl = {(x, y) for x in range(N) for y in range(N) if rng.random() < 0.25}
        s = (rng.randrange(N), rng.randrange(N)); t = (rng.randrange(N), rng.randrange(N))
        if s in bl or t in bl or s == t: continue
        if math.isinf(dijkstra(Grid(N, N, bl), s, t)): continue
        insts.append((N, bl, s, t))
    agree = total = nfail_any = nslack = 0
    for i, (N, bl, s, t) in enumerate(insts):
        grid = Grid(N, N, bl)
        a, _ = any_adversary(grid, s, t)
        o = solve_lazy(N, t, (1, 1), wa=False, fixed_grid=bl, fixed_s=s)
        ok = (a == 'FAIL') == (o['status'] == 'sat')
        extra = ''
        if o['res'] is not None:
            faithful, wa_ok, log, rep = check_model(o['res'], 1.0)
            extra = f' replay_faithful={faithful}'; ok = ok and faithful
        print(f'[{i}] N={N} s={s} t={t} bl={sorted(bl)} ANY-ORDER: adversary={a} sat={o["status"]} '
              f'({o["build"]:.0f}+{o["solve"]:.1f}s, it={o["iters"]}){extra} {"OK" if ok else "MISMATCH"}', flush=True)
        agree += ok; total += 1; nfail_any += (a == 'FAIL')
        for w in [(1, 1), (2, 1), (5, 1)]:
            wv = w[0] / w[1]
            a2, _ = wa_adversary(grid, s, t, wv)
            o2 = solve_lazy(N, t, w, wa=True, fixed_grid=bl, fixed_s=s)
            ok2 = (a2 == 'FAIL') == (o2['status'] == 'sat')
            extra = ''
            if o2['res'] is not None:
                faithful, wa_ok, log, rep = check_model(o2['res'], wv)
                extra = f' replay faithful={faithful} wa_ok={wa_ok} ref={rep}'
                ok2 = ok2 and faithful and wa_ok
            print(f'      w={wv}: wa_adversary={a2} sat={o2["status"]} ({o2["solve"]:.1f}s, it={o2["iters"]}, '
                  f'+{o2["stats"]["wa_added"]}/{o2["stats"]["eq_added"]}){extra} {"OK" if ok2 else "MISMATCH"}', flush=True)
            agree += ok2; total += 1
            if a == 'FAIL' and w[1] == 1 and w[0] in (1, 2):
                st, val, _ = min_slack(grid, s, t, wv, cap=400_000)
                if st != 'FAIL':
                    print(f'      slack test skipped (min_slack {st} {val})'); continue
                pr = to_pair(val)
                if pr is None:
                    print(f'      slack test skipped (slack {val} not recognised as a+b sqrt2)'); continue
                o3 = solve_lazy(N, t, w, wa=True, fixed_grid=bl, fixed_s=s, slack=pr)
                o4 = solve_lazy(N, t, w, wa=True, fixed_grid=bl, fixed_s=s, slack=(pr[0] - 1, pr[1]))
                ok3 = o3['status'] == 'sat' and o4['status'] == 'unsat'
                extra = ''
                if o3['res'] is not None:
                    faithful, _, log, _ = check_model(o3['res'], wv)
                    mv = max_violation(o3['res'], wv)
                    extra = f' model faithful={faithful} max_violation={mv:.4f}'
                    ok3 = ok3 and faithful and mv <= val + 1e-9
                print(f'      slack w={wv}: min_slack={val:.4f}={pr}: sat@sigma={o3["status"]} (it={o3["iters"]}) '
                      f'sat@sigma-1={o4["status"]} (it={o4["iters"]}){extra} {"OK" if ok3 else "MISMATCH"}', flush=True)
                agree += ok3; total += 1; nslack += 1
    print(f'AGREE {agree}/{total}; order-dependent instances: {nfail_any}/{len(insts)}; slack tests: {nslack}')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1, int(sys.argv[2]) if len(sys.argv) > 2 else 36)
