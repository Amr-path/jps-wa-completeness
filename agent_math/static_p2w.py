"""P2w: dA(x) feasible AND x is a stopping cell for arrival dA(x) (forced for straight; some sub-jump returns for diagonal).
No requirement that the ray from a closed origin reaches x."""
import sys, random, time
from common import *
from static_configs import feasible_dirs

def stopping_dirs(M,x):
    out=[]
    for d in feasible_dirs(M,x):
        if d[0] and d[1]:
            if M.jump(x,(d[0],0))[0] is not None or M.jump(x,(0,d[1]))[0] is not None: out.append(d)
        else:
            if M.J.has_forced(x[0],x[1],d[0],d[1]): out.append(d)
    return out

def enum_w(M, limit):
    s=M.s; start=frozenset({(s,(0,0))}); seen=set(); stack=[start]; n=0
    while stack:
        st=stack.pop()
        if st in seen: continue
        seen.add(st); n+=1
        if n>limit: return
        cd=dict(st); need=set()
        for x,d in st:
            for (y,e) in M.scan(x,d)[0]:
                if y not in cd: need.add(y)
        if not need: yield cd; continue
        y=min(need)
        for d in stopping_dirs(M,y): stack.append(st|{(y,d)})

seed=int(sys.argv[1]); n=int(sys.argv[2]); rng=random.Random(seed)
confs=0; viol=0; t0=time.time(); shown=0
for gi in range(n):
    W=rng.choice((4,5,6)); H=rng.choice((4,5,6)); p=rng.choice((0.2,0.3,0.4))
    grid=random_grid(rng,W,H,p); cells=grid.free_cells()
    if not cells: continue
    s=rng.choice(cells); M=Model(grid,s); comp=M.component()
    for cd in enum_w(M,20000):
        confs+=1; V={s}
        for x,d in cd.items(): V|=M.scan(x,d)[1]
        if V!=comp:
            viol+=1
            if shown<3:
                shown+=1; print('VIOL missing',sorted(comp-V)); print(grid_to_str(grid,s,None,sorted(comp-V))); print(cd)
print(f'P2w configs {confs}, (T) violations {viol}, {time.time()-t0:.0f}s')
