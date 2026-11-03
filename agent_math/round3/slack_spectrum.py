"""Minimal slack (bottleneck) of the best near-miss instances as a function of w; slack/w also shown (h-units)."""
import sys; sys.path.insert(0,'/home/claude/jps-wa/agent_math/round3')
from core import *
INST = {
 'pin1-9x9 s=(8,8)': (pinwheel1(N=9)[0], (8,8), (4,4)),
 'climb1 best (w=1 climb)': (Grid(9,9,[(0,6),(0,7),(2,3),(2,8),(3,6),(3,8),(4,8),(5,2),(6,5),(6,7),(7,1)]), (7,0), (4,4)),
 'climb5 best (w=3 climb)': (Grid(8,8,[(0,4),(0,6),(0,7),(1,1),(1,4),(1,6),(2,1),(3,1),(4,6),(6,3),(6,7),(7,1),(7,7)]), (3,0), (3,4)),
 'round-2 2x2': (Grid(8,8,[(3,1),(6,3),(1,4),(4,6),(1,6)]), (0,2), (3,4)),
}
for name,(g,s,t) in INST.items():
    print(name); print(grid_to_str(g,s,t))
    for w in (1.0,1.5,2.0,3.0,5.0,10.0,100.0,1e6):
        st,v,o = min_slack(g,s,t,w,cap=400_000)
        print(f'   w={w:>9}: {st:8s} slack={v:10.3f}  slack/w={v/w:7.3f}')
