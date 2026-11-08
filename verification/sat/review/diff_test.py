"""Differential test of the lazy SAT encoding (fixed grid, fixed s) against the faithful search-based references.
   wa=True , eqg=True  (per w)  vs core.wa_adversary            (must agree exactly)
   wa=False, eqg=True           vs validate.any_adversary        (must agree exactly: same semantics, any pop order)
   wa=False, eqg=False          vs ref/adversary.Adversary.can_fail  (enc SAT => can_fail True; converse need not hold,
                                                                 can_fail ignores g altogether)
Sample biased towards order-dependent instances (any_adversary == FAIL).  Every SAT model is replayed with the
reference code (check_model) on the KNOWN grid.
usage: python3 diff_test.py seed n_inst [N ...]"""
import sys, time, random, math, json
sys.path.insert(0, '/path/to/jps-wa/verification/sat')
sys.path.insert(0, '/path/to/jps-wa/verification/round3')
sys.path.insert(0, '/path/to/jps-wa/ref')
from lazy import solve_lazy
from enc import check_model
from validate import any_adversary
from core import wa_adversary
from jpswa import Grid, dijkstra
from adversary import Adversary

WS = [(1, 1), (3, 2), (2, 1), (5, 1)]
TMO = 60


def main(seed, n_inst, Ns):
    rng = random.Random(seed)
    insts = []; tried = 0
    while len(insts) < n_inst:
        N = rng.choice(Ns)
        t = (N // 2, N // 2) if rng.random() < 0.7 else (rng.randrange(N), rng.randrange(N))
        if rng.random() < 0.6:   # pinwheel core around t (the known order-dependent family) + random extras
            from core import pinwheel1
            g0, _ = pinwheel1(N=N, centre=t)
            bl = set(g0.blocked)
            for _ in range(rng.randrange(0, 4)):
                bl.add((rng.randrange(N), rng.randrange(N)))
        else:
            dens = rng.choice([0.15, 0.25, 0.35])
            bl = {(x, y) for x in range(N) for y in range(N) if rng.random() < dens}
        bl.discard(t)
        s = (rng.randrange(N), rng.randrange(N))
        if s in bl or s == t: continue
        grid = Grid(N, N, bl)
        if math.isinf(dijkstra(grid, s, t)): continue
        tried += 1
        a, _ = any_adversary(grid, s, t, limit=1_000_000)
        if a == 'limit': continue
        # bias: keep every order-dependent instance, 1 in 6 of the others
        if a != 'FAIL' and rng.random() > 1 / 6: continue
        insts.append((N, bl, s, t, a))
    print(f'{len(insts)} instances ({sum(1 for i in insts if i[4] == "FAIL")} order-dependent) out of {tried} tried', flush=True)
    rows = []; disagreements = []
    for i, (N, bl, s, t, a) in enumerate(insts):
        grid = Grid(N, N, bl)
        row = dict(N=N, s=s, t=t, blocked=sorted(bl), anyorder=a)
        # no-WA, eqg
        o = solve_lazy(N, t, (1, 1), wa=False, eqg=True, fixed_grid=bl, fixed_s=s, timeout=TMO)
        row['noWA'] = o['status']
        exp = 'sat' if a == 'FAIL' else 'unsat'
        if o['status'] != exp: disagreements.append(('noWA', row, o['status'], exp))
        if o['res'] is not None:
            res = dict(o['res']); res['blocked'] = bl; res['s'] = s
            ok, wa_ok, lg, rep = check_model(res, 1.0)
            row['noWA_replay_faithful'] = ok
            if not ok: disagreements.append(('noWA replay', row, lg))
        # no-WA, no eqg vs unrestricted adversary
        o2 = solve_lazy(N, t, (1, 1), wa=False, eqg=False, fixed_grid=bl, fixed_s=s, timeout=TMO)
        cf, _ = Adversary(grid, s, t).can_fail(limit_states=1_000_000)
        row['noWA_noeqg'] = o2['status']; row['can_fail'] = cf
        if o2['status'] == 'sat' and cf is False: disagreements.append(('noeqg vs can_fail', row))
        # WA per w
        for (p, q) in WS:
            w = p / q
            ref, _ = wa_adversary(grid, s, t, w, limit=1_000_000)
            o3 = solve_lazy(N, t, (p, q), wa=True, eqg=True, fixed_grid=bl, fixed_s=s, timeout=TMO)
            st = o3['status']
            row[f'w{p}/{q}'] = (st, ref, o3['iters'])
            if ref == 'limit' or st == 'timeout':
                continue
            if (st == 'sat') != (ref == 'FAIL'):
                disagreements.append((f'WA w={p}/{q}', row, st, ref))
            if o3['res'] is not None:
                res = dict(o3['res']); res['blocked'] = bl; res['s'] = s
                ok, wa_ok, lg, rep = check_model(res, w)
                row[f'w{p}/{q}_replay'] = (ok, wa_ok, rep.get('replay'))
                if not (ok and wa_ok and math.isinf(rep['replay'])):
                    disagreements.append((f'WA replay w={p}/{q}', row, lg, rep))
        rows.append(row)
        print(f'[{i}] N={N} s={s} t={t} nb={len(bl)} any={a} noWA={row["noWA"]} noeqg={row["noWA_noeqg"]}/can_fail={cf} ' +
              ' '.join(f'w{p}/{q}:{row[f"w{p}/{q}"][0]}/{row[f"w{p}/{q}"][1]}' for p, q in WS), flush=True)
    print('DISAGREEMENTS', len(disagreements))
    for d in disagreements:
        print(json.dumps(d, default=str))
    json.dump(rows, open(f'/path/to/jps-wa/verification/sat/review/diff_{seed}.json', 'w'), default=str)


if __name__ == '__main__':
    seed = int(sys.argv[1]); n = int(sys.argv[2]); Ns = [int(x) for x in sys.argv[3:]] or [6, 7]
    main(seed, n, Ns)
