"""Second resume (2026-10-31). For each remaining climb endpoint: WA* adversary (theta=0), then an unrestricted
any-order test (theta=1e9). 'complete' there means no failing order exists at all. On FAIL, tighten downward:
replay the order to get its bottleneck v (independent replay), test v-1e-6, repeat until 'complete' (=> exact v).
climb7: decide was complete for all theta <= 10.5 earlier in this log, so its WA* test is skipped."""
import sys, json, time
sys.path.insert(0, '/home/claude/jps-wa/agent_math/round3')
from core import Grid
from slack_threshold import decide, replay
lim = int(sys.argv[1])
out = open('/home/claude/jps-wa/agent_math/round3/logs_v2/exact_slacks3.log', 'a')
def log(*a):
    print(*a, flush=True); print(*a, file=out, flush=True)
eps = json.load(open('/home/claude/jps-wa/agent_math/round3/logs_v2/climb_endpoints.json'))
log(f'=== RESUME 2 (any-order first, then tighten down), limit {lim}, {time.ctime()}')
for nm in ['climb7', 'climb2', 'climb4', 'climb3', 'climb6']:
    c = [e for e in eps if e['name'] == nm][0]
    g = Grid(c['N'], c['N'], [tuple(b) for b in c['bl']]); s, t, w = tuple(c['s']), tuple(c['t']), c['w']
    log(f"{nm} w={w} N={c['N']} s={s} t={t} |blocked|={len(c['bl'])}")
    if nm != 'climb7':
        t0 = time.time(); st, _, n = decide(g, s, t, w, 0.0, lim)
        log(f'   WA* adversary (theta=0): {st}  states {n}  {time.time()-t0:.0f}s')
    t0 = time.time(); st, order, n = decide(g, s, t, w, 1e9, lim)
    log(f'   decide(theta=1e9, any order) -> {st}  states {n}  {time.time()-t0:.0f}s')
    if st != 'FAIL':
        log(f"   RESULT {nm} w={w}: {'no_failing_order_at_all' if st == 'complete' else 'limit_anyorder'}"); continue
    res = None
    while res is None:
        v = replay(g, s, t, w, order)
        log(f'   failing order of bottleneck {v:.6f} (replayed), length {len(order)}')
        t0 = time.time(); st, o2, n = decide(g, s, t, w, v - 1e-6, lim)
        log(f'   decide(theta={v - 1e-6:.6f}) -> {st}  states {n}  {time.time()-t0:.0f}s')
        if st == 'complete': res = ('exact', v)
        elif st == 'limit': res = ('upper', v)
        else: order = o2
    log(f"   RESULT {nm} w={w}: {res[0]} {res[1]!r}")
log('EXACT_SLACKS3_DONE')
