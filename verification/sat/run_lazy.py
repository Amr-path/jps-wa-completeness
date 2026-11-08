"""Variable-grid runs with the lazy solver.
usage: python3 run_lazy.py N p q timeout_s wa(1|0) [t_x t_y]   -> logs/lazy_N{N}_w{p}_{q}[_noWA].log"""
import sys, time, json
sys.path.insert(0, '/path/to/jps-wa/verification/sat')
from lazy import solve_lazy
from enc import check_model
N, p, q, tmo, wa = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5] != '0'
reps = [(x, y) for y in range(N) for x in range(N) if 2 * x <= N - 1 and 2 * y <= N - 1]
tag = f'lazyv2_N{N}_w{p}_{q}' + ('' if wa else '_noWA')
if len(sys.argv) > 7:
    reps = [(int(sys.argv[6]), int(sys.argv[7]))]; tag += f'_t{reps[0][0]}{reps[0][1]}'
log = open(f'/path/to/jps-wa/verification/sat/logs/{tag}.log', 'a')
def out(*a):
    print(*a, flush=True); print(*a, file=log, flush=True)
out(f'=== N={N} w={p}/{q} wa={wa} lazy timeout={tmo}s per t  {time.ctime()}')
summary = {}
for t in reps:
    o = solve_lazy(N, t, (p, q), wa=wa, sym_s=True, timeout=tmo, verbose=True)
    out(f't={t}: {o["status"]}  build {o["build"]:.0f}s solve {o["solve"]:.0f}s iters {o["iters"]} {o["stats"]}')
    summary[str(t)] = (o['status'], round(o['solve']))
    if o['res'] is not None:
        res = o['res']
        out('!!!!! SAT model:', json.dumps({k: (sorted(v) if isinstance(v, set) else str(v)) for k, v in res.items()}))
        faithful, wa_ok, lg, rep = check_model(res, p / q)
        out(f'   replay: faithful={faithful} wa_consistent={wa_ok} log={lg[:5]}')
        out(f'   reference CanonicalJPS replays (cost, inf = failure): {rep}')
out('SUMMARY', json.dumps(summary))
