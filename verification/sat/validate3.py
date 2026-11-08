"""Validation on ORDER-DEPENDENT fixed instances only (the interesting ones): pinwheel 7x7 / 9x9 cores with random
extra obstacles and random starts, filtered by the any-order adversary (FAIL).  For each: wa=False must be SAT with a
faithful replay; wa=True must agree with wa_adversary for w in {1, 3/2, 2, 5}; slack test at w = 1 and 2 (exact
min_slack sigma: SAT at sigma with max violation == sigma, UNSAT at sigma - 1).  Also reports the number of lazy
iterations / added constraints, which shows the WA* machinery is exercised."""
import sys, time, random, math
sys.path.insert(0, '/path/to/jps-wa/verification/sat')
sys.path.insert(0, '/path/to/jps-wa/verification/round3')
sys.path.insert(0, '/path/to/jps-wa/ref')
from lazy import solve_lazy
from enc import check_model
from validate import any_adversary
from validate2 import to_pair, max_violation
from core import wa_adversary, min_slack, pinwheel1
from jpswa import Grid, dijkstra


def main(seed=5, n_inst=20):
    rng = random.Random(seed)
    insts = []
    tried = 0
    while len(insts) < n_inst:
        N = rng.choice([7, 7, 7, 8, 9])
        g, t = pinwheel1(N=N, centre=(N // 2 + rng.choice([-1, 0, 0, 1]) if N > 7 else N // 2, N // 2))
        bl = set(g.blocked)
        for _ in range(rng.randrange(0, 3)):
            bl.add((rng.randrange(N), rng.randrange(N)))
        bl.discard(t)
        s = (rng.randrange(N), rng.randrange(N))
        if s in bl or s == t: continue
        grid = Grid(N, N, bl)
        if math.isinf(dijkstra(grid, s, t)): continue
        tried += 1
        a, order = any_adversary(grid, s, t, limit=1_500_000)
        if a != 'FAIL': continue
        # does the failing order step on t (via a sub-jump) without pushing it?
        from core import Model
        M = Model(grid, s); od = {s: (0.0, None)}; cl = set(); tv = False
        for x in order:
            gx, px = od[x]; jps, vis = M.expand(x, M.dir_from(x, px), t); tv |= (t in vis); cl.add(x); del od[x]
            for (j, c) in jps:
                if j not in cl and gx + c < od.get(j, (math.inf,))[0] - 1e-12: od[j] = (gx + c, x)
        insts.append((N, bl, s, t, tv))
    print(f'{len(insts)} order-dependent instances out of {tried} tried; '
          f'{sum(1 for i in insts if i[4])} of them with a failing order that steps on t via a sub-jump without pushing it')
    agree = total = 0
    for i, (N, bl, s, t, tv) in enumerate(insts):
        grid = Grid(N, N, bl)
        o = solve_lazy(N, t, (1, 1), wa=False, fixed_grid=bl, fixed_s=s)
        ok = o['status'] == 'sat'
        if o['res'] is not None:
            faithful, _, log, _ = check_model(o['res'], 1.0); ok = ok and faithful
        print(f'[{i}] N={N} s={s} t={t} bl={sorted(bl)} t_visited_not_pushed={tv} ANY-ORDER sat={o["status"]} it={o["iters"]} '
              f'+{o["stats"]["eq_added"]}eq/{o["stats"]["min_added"]}min faithful={ok} ({o["build"]:.0f}+{o["solve"]:.1f}s) {"OK" if ok else "MISMATCH"}', flush=True)
        agree += ok; total += 1
        for w in [(1, 1), (3, 2), (2, 1), (5, 1)]:
            wv = w[0] / w[1]
            a2, _ = wa_adversary(grid, s, t, wv, limit=3_000_000)
            o2 = solve_lazy(N, t, w, wa=True, fixed_grid=bl, fixed_s=s)
            ok2 = (a2 == 'FAIL') == (o2['status'] == 'sat') and a2 != 'limit'
            extra = ''
            if o2['res'] is not None:
                faithful, wa_ok, log, rep = check_model(o2['res'], wv)
                extra = f' replay faithful={faithful} wa_ok={wa_ok} ref={rep}'; ok2 = ok2 and faithful and wa_ok
            print(f'      w={wv}: wa_adversary={a2} sat={o2["status"]} ({o2["solve"]:.1f}s, it={o2["iters"]}, '
                  f'+{o2["stats"]["wa_added"]}wa/{o2["stats"]["eq_added"]}eq/{o2["stats"]["min_added"]}min){extra} {"OK" if ok2 else "MISMATCH"}', flush=True)
            agree += ok2; total += 1
            if w in [(1, 1), (2, 1)]:
                st, val, _ = min_slack(grid, s, t, wv, cap=300_000)
                if st != 'FAIL':
                    print(f'      slack test skipped (min_slack {st} {val})'); continue
                pr = to_pair(val)
                if pr is None:
                    print(f'      slack test skipped ({val})'); continue
                o3 = solve_lazy(N, t, w, wa=True, fixed_grid=bl, fixed_s=s, slack=pr)
                o4 = solve_lazy(N, t, w, wa=True, fixed_grid=bl, fixed_s=s, slack=(pr[0] - 1, pr[1]))
                ok3 = o3['status'] == 'sat' and o4['status'] == 'unsat'
                extra = ''
                if o3['res'] is not None:
                    faithful, _, log, _ = check_model(o3['res'], wv); mv = max_violation(o3['res'], wv)
                    extra = f' faithful={faithful} max_violation={mv:.4f}'; ok3 = ok3 and faithful and abs(mv - val) < 1e-9
                print(f'      slack w={wv}: min_slack={val:.4f}={pr}: sat@sigma={o3["status"]} (it={o3["iters"]}) '
                      f'sat@sigma-1={o4["status"]} (it={o4["iters"]}){extra} {"OK" if ok3 else "MISMATCH"}', flush=True)
                agree += ok3; total += 1
    print(f'AGREE {agree}/{total}')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 5, int(sys.argv[2]) if len(sys.argv) > 2 else 20)
