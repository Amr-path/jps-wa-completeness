import sys, math
sys.path.insert(0,'/path/to/jps-wa/ref')
from jpswa import *
from pinwheel import build
from pinwheel_verify2 import ORDER
from common import Model
g,s,hole,sh=build(); M=Model(g,s)
names={}
closedset=set(); gval={s:0.0}; parent={s:None}
D={(1,0):'E',(-1,0):'W',(0,1):'S',(0,-1):'N',(1,1):'SE',(1,-1):'NE',(-1,1):'SW',(-1,-1):'NW',(0,0):'0'}
print('grid (y down). hole', hole)
print(grid_to_str(g,s,None,hole))
for i,n in enumerate(ORDER):
    p=parent[n]
    d=(0,0) if p is None else ((n[0]>p[0])-(n[0]<p[0]),(n[1]>p[1])-(n[1]<p[1]))
    jps,vis=M.scan(n,d)
    closedset.add(n)
    out=[]
    for (y,e) in jps:
        tag='CLOSED-dropped' if y in closedset else ''
        jg=None
        out.append(f'{y}<-{D[e]}{" "+tag if tag else ""}')
        if y not in closedset:
            # faithful g update
            pass
    print(f'{i:2d} pop {n} arr={D[d]:2s} succ={[D[e] for e in M.succ_dirs(n,d)]} returns: {out}')
    # update parents like replay
    J=M.J
    for e in M.succ_dirs(n,d):
        r=J.jump(n[0],n[1],e[0],e[1],gval[n])
        if r is None: continue
        j=(r[0],r[1])
        if j in closedset: continue
        if r[2]<gval.get(j,math.inf)-1e-12: gval[j]=r[2]; parent[j]=n
