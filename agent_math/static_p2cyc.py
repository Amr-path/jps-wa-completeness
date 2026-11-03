import sys, random, time
from common import *
from static_configs import enum_static, feasible_dirs
seed=int(sys.argv[1]); n=int(sys.argv[2]); rng=random.Random(seed)
confs=0; viol=0; cyc=0; t0=time.time(); shown=0
for gi in range(n):
    W=rng.choice((4,5,6)); H=rng.choice((4,5,6)); p=rng.choice((0.2,0.3,0.4))
    grid=random_grid(rng,W,H,p); cells=grid.free_cells()
    if not cells: continue
    s=rng.choice(cells); M=Model(grid,s); comp=M.component()
    for cd in enum_static(M,'feasible',limit=20000):
        # P2 check with witnesses anywhere in C
        ret=set()
        for x,d in cd.items():
            for (y,e) in M.scan(x,d)[0]: ret.add((y,e))
        if not all((x,d) in ret for x,d in cd.items() if x!=s): continue
        confs+=1
        # acyclic? witness graph: edge x->y if (y,dA(y)) returned by x
        # check if config is reachable by the real adversary: need an order where each x's dA witness is closed earlier
        par={y:[x for x,d in cd.items() for (yy,e) in M.scan(x,d)[0] if (yy,e)==(y,cd[y])] for y in cd if y!=s}
        done={s}; prog=True
        while prog:
            prog=False
            for y in cd:
                if y not in done and any(x in done for x in par[y]): done.add(y); prog=True
        if len(done)<len(cd): cyc+=1
        V={s}
        for x,d in cd.items(): V|=M.scan(x,d)[1]
        if V!=comp:
            viol+=1
            if shown<3:
                shown+=1; print('VIOL missing',sorted(comp-V),'cyclic' if len(done)<len(cd) else 'acyclic'); print(grid_to_str(grid,s,None,sorted(comp-V))); print(cd)
print(f'P2-cyclic configs {confs} (of which not tree-realisable {cyc}), (T) violations {viol}, {time.time()-t0:.0f}s')
