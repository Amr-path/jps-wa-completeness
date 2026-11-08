"""Random-order runs on bigger grids; check depth-K closure invariant at every intermediate state."""
import sys, random, time
from common import *

seed=int(sys.argv[1]); n=int(sys.argv[2]); K=int(sys.argv[3]); rng=random.Random(seed)
states=0; viol=0; t0=time.time(); shown=0
for gi in range(n):
    W=H=rng.choice((6,8,10,12)); p=rng.choice((0.2,0.3,0.4,0.5))
    grid=random_grid(rng,W,H,p); cells=grid.free_cells()
    if not cells: continue
    s=rng.choice(cells); M=Model(grid,s)
    for k in range(4):
        cd={}; pend=[(s,(0,0))]; V={s}
        while pend:
            states+=1
            pl=[(y,e) for (y,e) in pend if y not in cd]
            cov=closure(M,pl,set(cd),K)
            for (p_,c) in frontier_edges(M,V):
                if c not in cov:
                    viol+=1
                    if shown<3:
                        shown+=1; print('VIOL K',K,'frontier',p_,c); print(grid_to_str(grid,s,None,[c]))
            x,d=pend.pop(rng.randrange(len(pend)))
            if x in cd: continue
            cd[x]=d; jps,vis=M.scan(x,d); V|=vis
            for (y,e) in jps:
                if y not in cd: pend.append((y,e))
print(f'K={K}: states {states}, violations {viol}, {time.time()-t0:.0f}s')
