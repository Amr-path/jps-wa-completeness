"""Check the slack numbers of Section 6 (13.41 at w=1, 13.07 at w=2, 35.1 at w=10) with round3/core.py,
the per-step slack of the Table 2 order, and the sentence about (2,3)/(1,3)."""
import sys, math
sys.path.insert(0, '/home/claude/jps-wa/agent_math/round3')
from core import *
from core import _succ_state

g, t = pinwheel1(N=9)
s = (1, 1)
assert sorted(g.blocked) == sorted([(2,3),(5,2),(6,5),(3,6)])
M = Model(g, s)
for w in ():
    st, v, order = min_slack(g, s, t, w, cap=600_000, M=M)
    print(f'w={w}: min_slack status {st} value {v:.3f}', 'order', order)
for w in ():
    print('wa_adversary w=%g:' % w, wa_adversary(g, s, t, w, M=M)[0])

# per-step slack of the paper's order at w=1 and w=2
order = [(1,1),(2,2),(1,4),(2,5),(2,7),(4,7),(5,6),(4,5),(7,6),
         (7,4),(6,3),(5,4),(6,1),(7,2),(4,3),(3,2),(3,4),(4,1)]
h = lambda c: octile(c[0], c[1], t[0], t[1])
for w in (1.0, 2.0):
    closed = frozenset(); od = {s: (0.0, None)}; worst = (0, None)
    for x in order:
        gx, px = od[x]
        fmin = min(gg + w*h(c) for c, (gg, p) in od.items())
        argmin = min(od, key=lambda c: od[c][0] + w*h(c))
        sl = gx + w*h(x) - fmin
        if sl > worst[0]: worst = (sl, (x, gx, argmin, od[argmin][0]))
        closed, od, vis = _succ_state(M, closed, od, x, gx, px)
    print(f'w={w}: largest violation along Table-2 order = {worst[0]:.3f} at pop {worst[1]}')
