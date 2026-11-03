"""Exhaustive WA*-adversary enumeration of a complete family:
  N x N grid (N = 7, 8, 9), t = centre, the four 1x1-pinwheel blockers, plus 0 or 1 extra blocked cell (every
  position), EVERY start cell s, every w in WS, adversarial ties.  Reports #instances, #order-failable, #WA* fails."""
import sys, time, math
sys.path.insert(0, '/home/claude/jps-wa/agent_math/round3')
from core import *
WS = [1.0, 1.1, 1.5, 2.0, 3.0, 5.0, 10.0, 100.0, 1e6]
N = int(sys.argv[1]); extras = int(sys.argv[2])   # extras: 0 or 1
t0 = time.time(); inst = runs = fails = orderfail = 0
core = sys.argv[3] if len(sys.argv) > 3 else 'pin1'
if core == 'pin1':
    base, t = pinwheel1(N=N); holes = [t]
else:   # round-2 2x2 pinwheel core, N must be 8
    base = Grid(8, 8, [(3, 1), (6, 3), (1, 4), (4, 6), (1, 6)]); holes = [(3, 3), (4, 3), (3, 4), (4, 4)]
cells = [c for c in Grid(N, N, []).free_cells() if c not in base.blocked and c not in holes]
extra_sets = [()] if extras == 0 else [(c,) for c in cells]
for ex in extra_sets:
    g = Grid(N, N, sorted(base.blocked | set(ex)))
    for s in g.free_cells():
      if s in holes: continue
      for t in holes:
        if dijkstra(g, s, t) == math.inf: continue
        inst += 1; M = Model(g, s)
        st, v, _ = min_slack(g, s, t, 1.0, cap=5_000, M=M)
        if st != 'complete': orderfail += 1
        for w in WS:
            r, order = wa_adversary(g, s, t, w, limit=200_000, M=M); runs += 1
            if r == 'FAIL':
                fails += 1; print('!!!!! WA* FAILURE', N, ex, s, t, w, order, flush=True)
                print(reproduce(g, s, t, w, order), flush=True)
            elif r == 'limit': print('limit', N, ex, s, w, flush=True)
    print(f'{time.time()-t0:.0f}s extra={ex} instances={inst} runs={runs} order-failable(cap5k)={orderfail} WA*fails={fails}', flush=True)
print('DONE', N, extras, inst, runs, orderfail, fails)
