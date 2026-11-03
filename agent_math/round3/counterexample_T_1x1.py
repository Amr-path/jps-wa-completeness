"""NEW, SIMPLER COUNTEREXAMPLE TO (T): a single never-visited cell.
9x9 grid, 4 blocked cells at the knight offsets around t=(4,4): (2,3),(5,2),(6,5),(3,6); s=(8,8) (also s=(0,0),(1,1)).
An expansion order of canonical JPS with cell closing (reference loop; parent = best-g generator) empties Open
with t never stepped on.  Found by core.min_slack (bottleneck search, any slack), replayed with the REFERENCE
successor_dirs/jump (pinwheel_verify.replay) and checked against the reachable set."""
import sys, math
sys.path.insert(0, '/home/claude/jps-wa/agent_math/round3'); sys.path.insert(0, '/home/claude/jps-wa/agent_math')
from core import *
from pinwheel_verify import replay
g, t = pinwheel1(N=9)
for s in [(8, 8), (0, 0), (1, 1)]:
    st, v, order = min_slack(g, s, t, 1.0, cap=400_000)
    visited, closed, gval, parent = replay(g, s, order)
    comp = Model(g, s).component()
    print(f's={s}: {st}, order={order}')
    print(f'   reachable {len(comp)}, visited {len(visited)}, NEVER VISITED: {sorted(comp - visited)}')
    assert sorted(comp - visited) == [t]
print(grid_to_str(g, (8, 8), t))
