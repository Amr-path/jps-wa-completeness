"""Variant: root r with ARBITRARY feasible direction d_r (not 0), P1 everywhere, P2 for all x != r.
Tree-realisable version: run the adversary from state (r,d_r)."""
import sys, random, time
from common import *
from static_configs import feasible_dirs
seed=int(sys.argv[1]); n=int(sys.argv[2]); rng=random.Random(seed)
confs=0; viol=0; t0=time.time(); shown=0
for gi in range(n):
    W=H=rng.choice((5,6,8)); p=rng.choice((0.2,0.3,0.4,0.5))
    grid=random_grid(rng,W,H,p); cells=grid.free_cells()
    if not cells: continue
    r=rng.choice(cells); M=Model(grid,r); comp=M.component()
    for d in feasible_dirs(M,r):
        for k in range(10):
            cd={}; pend=[(r,d)]
            while pend:
                x,dd=pend.pop(rng.randrange(len(pend)))
                if x in cd: continue
                cd[x]=dd
                for (y,e) in M.scan(x,dd)[0]:
                    if y not in cd: pend.append((y,e))
            confs+=1; V={r}
            for x,dd in cd.items(): V|=M.scan(x,dd)[1]
            if V!=comp:
                viol+=1
                if shown<3:
                    shown+=1; print('VIOL root',r,'dir',d,'missing',sorted(comp-V)); print(grid_to_str(grid,r,None,sorted(comp-V)))
print(f'root-configs {confs}, violations {viol}, {time.time()-t0:.0f}s')
