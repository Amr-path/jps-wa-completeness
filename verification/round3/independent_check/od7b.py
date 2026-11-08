import sys, collections
sys.path.insert(0,'/path/to/jps-wa/verification/round3')
from core import min_slack, pinwheel1, Grid, Model, dijkstra
from slack_threshold import decide
import math
from myjps import Inst, exhaustive
base,t=pinwheel1(N=7); N=7
cnt=collections.Counter(); shown=0
cells=[c for c in Grid(N,N,[]).free_cells() if c not in base.blocked and c!=t]
for ex in cells:
    g=Grid(N,N,sorted(base.blocked|{ex}))
    for s in g.free_cells():
        if s==t or dijkstra(g,s,t)==math.inf: continue
        st,v,_=min_slack(g,s,t,1.0,cap=5000)
        mine=exhaustive(Inst(N,sorted(g.blocked),s,t),limit=200000)[0]
        cnt[(st,mine)]+=1
        if st=='LB' and mine=='complete' and shown<3:
            shown+=1; print('cross-check decide(1e9):',ex,s,decide(g,s,t,1.0,1e9,2_000_000)[0],flush=True)
print(dict(cnt))
