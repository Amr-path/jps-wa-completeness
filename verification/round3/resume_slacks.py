"""Resume of slack_threshold.py after a container restart (2026-10-31).
climb1: decide(theta) was 'complete' for every theta up to 12.5 in logs_v2/exact_slacks3.log (decide is monotone
in theta: the allowed pop set only grows), so 12.5 is a valid lower bound; resume at 13.0.
Then the remaining climbs exactly as in slack_threshold.__main__."""
import sys, json, time
sys.path.insert(0, '/path/to/jps-wa/verification/round3')
from core import Grid
from slack_threshold import decide, exact_min
lim = int(sys.argv[1])
out = open('/path/to/jps-wa/verification/round3/logs_v2/exact_slacks3.log', 'a')
def log(*a):
    print(*a, flush=True); print(*a, file=out, flush=True)
eps = json.load(open('/path/to/jps-wa/verification/round3/logs_v2/climb_endpoints.json'))
log(f'=== RESUME after container restart, limit {lim}, {time.ctime()}')
for nm, th0 in [('climb1', 16.0), ('climb7', None), ('climb2', None), ('climb4', None), ('climb3', None), ('climb6', None)]:
    c = [e for e in eps if e['name'] == nm][0]
    g = Grid(c['N'], c['N'], [tuple(b) for b in c['bl']]); s, t, w = tuple(c['s']), tuple(c['t']), c['w']
    log(f"{nm} w={w} N={c['N']} s={s} t={t} |blocked|={len(c['bl'])}" + (f'  (resumed at theta={th0})' if th0 else ''))
    if th0 is None:
        t0 = time.time(); st, _, n = decide(g, s, t, w, 0.0, lim)
        log(f'   WA* adversary (theta=0): {st}  states {n}  {time.time()-t0:.0f}s')
        th0 = c['reported']
    step = 0.5 if w < 100 else 0.5 * w
    if nm == 'climb1':
        # decide was complete for every theta <= 15.5 (log above) and state counts plateaued near 18.7M, so test
        # the unrestricted case (theta = 1e9: any order of live entries) first, then tighten downward.
        t0 = time.time(); st, order, n = decide(g, s, t, w, 1e9, lim)
        log(f'   decide(theta=1e9, any order) -> {st}  states {n}  {time.time()-t0:.0f}s')
        if st != 'FAIL':
            log(f"   RESULT {nm} w={w}: {'no_failing_order_at_all' if st == 'complete' else 'limit'} 15.5"); continue
        th0 = 1e9
    r = exact_min(g, s, t, w, th0, step, lim, log)
    log(f"   RESULT {nm} w={w}: {r[0]} {r[1]!r}")
log('EXACT_SLACKS3_DONE')
