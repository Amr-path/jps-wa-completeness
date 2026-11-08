"""Main driver: variable N x N grid, variable start, target t ranging over the representatives of the exact
symmetry group {id, flip_x, flip_y, rot180} (t.x <= (N-1)/2, t.y <= (N-1)/2), weight w = p/q.
usage: python3 run_var.py N p q [timeout_s] [wa=1|0] [eqg=1|0] [engine] [t_x t_y]
Writes logs/var_N{N}_w{p}_{q}[_noWA][_noeqg].log ; any SAT model is replayed (Model + reference ReplayJPS)."""
import sys, time, json
sys.path.insert(0, '/path/to/jps-wa/verification/sat')
from solve import solve
from enc import check_model


def main():
    N, p, q = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    tmo = int(sys.argv[4]) if len(sys.argv) > 4 else 3600
    wa = (sys.argv[5] != '0') if len(sys.argv) > 5 else True
    eqg = (sys.argv[6] != '0') if len(sys.argv) > 6 else True
    engine = sys.argv[7] if len(sys.argv) > 7 else 'cadical'
    tag = f'var_N{N}_w{p}_{q}' + ('' if wa else '_noWA') + ('' if eqg else '_noeqg')
    reps = [(x, y) for y in range(N) for x in range(N) if 2 * x <= N - 1 and 2 * y <= N - 1]
    if len(sys.argv) > 9:
        reps = [(int(sys.argv[8]), int(sys.argv[9]))]
        tag += f'_t{reps[0][0]}{reps[0][1]}'
    log = open(f'/path/to/jps-wa/verification/sat/logs/{tag}.log', 'a')

    def out(*a):
        print(*a, flush=True); print(*a, file=log, flush=True)
    out(f'=== N={N} w={p}/{q} wa={wa} eqg={eqg} engine={engine} timeout={tmo}s  {time.ctime()}')
    summary = {}
    tot = 0.0
    for t in reps:
        o = solve(N, t, (p, q), wa=wa, eqg=eqg, sym_s=True, timeout=tmo, engine=engine)
        tot += o['solve']
        out(f't={t}: {o["status"]}  build {o["build"]:.1f}s  solve {o["solve"]:.1f}s  {o["stats"]}')
        summary[str(t)] = (o['status'], round(o['solve'], 1))
        if o['res'] is not None:
            res = o['res']
            out('!!!!! SAT model:', json.dumps({k: (sorted(v) if isinstance(v, set) else str(v)) for k, v in res.items()}))
            faithful, wa_ok, lg, rep = check_model(res, p / q)
            out(f'   replay: faithful={faithful} wa_consistent={wa_ok} log={lg[:5]}')
            out(f'   reference CanonicalJPS replays (cost, inf = failure): {rep}')
    out('SUMMARY', json.dumps(summary), f'total solve {tot:.1f}s')


if __name__ == '__main__':
    main()
