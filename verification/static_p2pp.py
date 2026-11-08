"""P2'': dA(x) such that Jump(o,dA(x)) returns x for some closed o (direction need not be in succ(o,dA(o)))."""
import sys, random, time
from common import *
from static_mutate import random_terminal, is_tree

def returned_any(M, cd):
    ret={}
    for o in cd:
        for e in DIRS8:
            y=M.jump(o,e)[0]
            if y is not None: ret.setdefault(y,set()).add(e)
    return ret
def returned(M, cd):
    ret={}
    for x,d in cd.items():
        for (y,e) in M.scan(x,d)[0]: ret.setdefault(y,set()).add(e)
    return ret

seed=int(sys.argv[1]); n=int(sys.argv[2]); rng=random.Random(seed)
confs=0; viol=0; t0=time.time()
for gi in range(n):
    W=H=rng.choice((6,8)); p=rng.choice((0.2,0.3,0.4,0.5))
    grid=random_grid(rng,W,H,p); cells=grid.free_cells()
    if not cells: continue
    s=rng.choice(cells); M=Model(grid,s); comp=M.component()
    for k in range(5):
        cd=random_terminal(M,rng)
        for it in range(30):
            cd2=dict(cd); ra=returned_any(M,cd2)
            cand=[x for x in cd2 if x!=s and len(ra.get(x,()))>1]
            if not cand: break
            for x in rng.sample(cand, min(len(cand), rng.randint(1,3))): cd2[x]=rng.choice(sorted(ra[x]))
            # repair P1
            while True:
                ret=returned(M,cd2); need=[y for y in ret if y not in cd2]
                if not need: break
                y=rng.choice(need); ra=returned_any(M,cd2); cd2[y]=rng.choice(sorted(ra[y]))
            ra=returned_any(M,cd2)
            if not all(x==s or cd2[x] in ra.get(x,()) for x in cd2): continue
            confs+=1
            V={s}
            for x,d in cd2.items(): V|=M.scan(x,d)[1]
            if V!=comp:
                viol+=1
                if viol<=2: print('VIOL',sorted(comp-V)); print(grid_to_str(grid,s,None,sorted(comp-V))); print(cd2)
            cd=cd2
print(f"P2'' configs {confs}, violations {viol}, {time.time()-t0:.0f}s")
