"""I2: at every reachable state, every frontier cell c (free, adjacent by a legal straight move to V, not in V)
lies in the state-closure of the pending entries restricted to unclosed cells."""
import sys, random, time
from common import *
seed=int(sys.argv[1]); n=int(sys.argv[2]); rng=random.Random(seed)
states=0; viol=0; t0=time.time(); shown=0
def closure(M, pend, closed_cells):
    seen=set(); stack=list(pend); cov=set()
    while stack:
        st=stack.pop()
        if st in seen: continue
        seen.add(st)
        jps,vis=M.scan(*st); cov|=vis
        for (y,e) in jps:
            if y not in closed_cells: stack.append((y,e))
    return cov
for gi in range(n):
    W=rng.choice((4,5,6,7)); H=rng.choice((4,5,6,7)); p=rng.choice((0.2,0.3,0.4))
    grid=random_grid(rng,W,H,p); cells=grid.free_cells()
    if not cells: continue
    s=rng.choice(cells); M=Model(grid,s)
    for cd,open_,V in enumerate_states(M, limit=30000):
        states+=1
        pend=[(y,e) for (y,e) in open_ if y not in cd]
        cov=closure(M,pend,set(cd))
        for (p_,c) in frontier_edges(M,V):
            if c not in cov:
                viol+=1
                if shown<3:
                    shown+=1; print('I2 VIOLATION frontier',p_,c,'closed',cd,'pending',pend); print(grid_to_str(grid,s,None,[c]))
print(f'states {states}, I2 violations {viol}, {time.time()-t0:.0f}s')
