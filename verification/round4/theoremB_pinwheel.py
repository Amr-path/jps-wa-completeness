"""Quantitative content of THEOREM B on the 1x1 pinwheel (9x9, blockers (2,3),(5,2),(6,5),(3,6), t=(4,4), s=(1,1)).
Theorem B: in a run that never visits t, every cell z closed no later than the break cell of the canonical optimal
J-path pi* satisfies dist(s,z) + w h(z) <= g(z) + w h(z) <= w C*.
pi* = s -> (2,2) -> (3,2) -> (4,3) -> t, C* = 4.828.  In the only (T)-failing structure for this start the break of
pi* is at the blocker (4,3), closed with arrival W from a ring origin o on row 3 east of (4,3).  Every such o and every
cell of its parent chain must satisfy dist(s,o) + w h(o) <= w C*.  We print, for each candidate ring origin o, the
smallest w for which this is satisfiable, i.e. the smallest w for which Theorem B alone does not exclude the failure."""
import sys, math
sys.path.insert(0, '/path/to/jps-wa/ref'); sys.path.insert(0, '/path/to/jps-wa/verification/round3')
from jpswa import dijkstra, octile
from core import pinwheel1
g, t = pinwheel1(N=9); s = (1, 1)
C = dijkstra(g, s, t); print('C* =', round(C, 3))
for o in [(5, 3), (6, 3), (7, 3), (8, 3)]:
    d = dijkstra(g, s, o); h = octile(*o, *t)
    # need d + w h <= w C  <=>  w >= d / (C - h)
    wmin = d / (C - h) if C > h else math.inf
    print(f'ring origin {o}: dist(s,o)={d:.3f} h={h:.3f} -> Theorem B allows only w >= {wmin:.3f}')
# the spiral chain actually used by the min-slack failing order (round 3 / round4/trace.py):
chain = [(1, 4), (2, 5), (2, 7), (4, 7), (5, 6), (7, 6), (7, 4), (6, 3)]
print('spiral chain of the found failing order: w needed by Theorem B =',
      max(dijkstra(g, s, z) / (C - octile(*z, *t)) for z in chain))
