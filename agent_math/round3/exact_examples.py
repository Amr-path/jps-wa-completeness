"""Exact slacks (slack_threshold.exact_min) for: the pinwheel at all ten weights of Section 6, and two
intermediate hill-climb instances (climb_1.log ev=4, climb_2.log ev=483), whose logged values were FAIL (exact
in min_slack) -- recomputed here with the threshold method."""
import sys, time, math
sys.path.insert(0, '/home/claude/jps-wa/agent_math/round3')
from core import Grid
from slack_threshold import decide, exact_min
out = open('/home/claude/jps-wa/agent_math/round3/logs_v2/exact_examples.log', 'a')
def log(*a):
    print(*a, flush=True); print(*a, file=out, flush=True)
pin = [(2, 3), (5, 2), (6, 5), (3, 6)]
C = [('pinwheel', w, 9, (1, 1), (4, 4), pin) for w in [1.0, 1.1, 1.2, 1.5, 2.0, 3.0, 5.0, 10.0, 100.0, 1e6]]
C += [('climb1_ev4', 1.0, 9, (8, 8), (4, 4), [(1, 4), (2, 3), (3, 6), (5, 2), (6, 5), (6, 6)]),
      ('climb2_ev483', 2.0, 9, (2, 8), (4, 4), [(0, 0), (0, 2), (0, 6), (0, 8), (1, 0), (2, 0), (2, 1), (2, 3), (2, 6), (3, 1), (3, 6), (3, 7), (4, 7), (5, 0), (5, 2), (6, 5), (6, 6), (6, 8), (7, 2), (7, 3), (8, 1), (8, 7)])]
log(f'=== exact examples {time.ctime()}')
for nm, w, N, s, t, bl in C:
    g = Grid(N, N, bl)
    log(f'{nm} w={w} N={N} s={s} t={t} blocked={bl}')
    st, _, n = decide(g, s, t, w, 0.0, 20_000_000); log(f'   WA* adversary: {st} states {n}')
    # any-order first, then tighten downward (as in resume_slacks2.py)
    st, order, n = decide(g, s, t, w, 1e9, 20_000_000); log(f'   any order: {st} states {n}')
    if st != 'FAIL': log(f'   RESULT {nm} w={w}: {st}'); continue
    from slack_threshold import replay
    while True:
        v = replay(g, s, t, w, order)
        st, o2, n = decide(g, s, t, w, v - 1e-6, 20_000_000)
        log(f'   bottleneck {v:.6f}; decide(v-1e-6) -> {st} states {n}')
        if st != 'FAIL': break
        order = o2
    log(f"   RESULT {nm} w={w}: {'exact' if st == 'complete' else 'upper'} {v!r}  slack/w={v/w:.6f}")
log('EXACT_EXAMPLES_DONE')
