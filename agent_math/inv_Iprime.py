"""Test invariant I': at every reachable intermediate state, every frontier edge (p,c) has a PENDING entry (y,e)
(y not closed) with c in Scan(y,e)."""
import sys, random, time
from common import *
seed=int(sys.argv[1]); n=int(sys.argv[2]); rng=random.Random(seed)
states=0; viol=0; t0=time.time(); shown=0
for gi in range(n):
    W=rng.choice((4,5,6)); H=rng.choice((4,5,6)); p=rng.choice((0.2,0.3,0.4))
    grid=random_grid(rng,W,H,p); cells=grid.free_cells()
    if not cells: continue
    s=rng.choice(cells); M=Model(grid,s)
    for cd,open_,V in enumerate_states(M, limit=20000):
        states+=1
        pend=[(y,e) for (y,e) in open_ if y not in cd]
        cov=set()
        for (y,e) in pend: cov|=M.scan(y,e)[1]
        for (p_,c) in frontier_edges(M,V):
            if c not in cov:
                viol+=1
                if shown<3:
                    shown+=1
                    print('VIOLATION frontier',p_,c,'closed',cd,'pending',pend)
                    print(grid_to_str(grid,s,None,[c]))
print(f'states {states}, violations {viol}, {time.time()-t0:.0f}s')
