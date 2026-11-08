"""Random P0+P1+P2 (cyclic witnesses allowed) configs on larger grids via mutation + repair."""
import sys, random, time
from common import *

def returned(M, cd):
    ret={}
    for x,d in cd.items():
        for (y,e) in M.scan(x,d)[0]: ret.setdefault(y,set()).add(e)
    return ret

def repair(M, cd, rng):
    """make P1 hold: add missing jump points with a random returned direction. Then check P2."""
    while True:
        ret=returned(M,cd)
        need=[y for y in ret if y not in cd]
        if not need: break
        y=rng.choice(need); cd[y]=rng.choice(sorted(ret[y]))
    ret=returned(M,cd)
    return all(x==M.s or cd[x] in ret.get(x,()) for x in cd)

def random_terminal(M, rng):
    cd={}; pend=[(M.s,(0,0))]
    while pend:
        x,d=pend.pop(rng.randrange(len(pend)))
        if x in cd: continue
        cd[x]=d
        for (y,e) in M.scan(x,d)[0]:
            if y not in cd: pend.append((y,e))
    return cd

def is_tree(M,cd):
    ret={}
    for x,d in cd.items():
        for (y,e) in M.scan(x,d)[0]:
            if y in cd and cd[y]==e: ret.setdefault(y,set()).add(x)
    done={M.s}; prog=True
    while prog:
        prog=False
        for y in cd:
            if y not in done and any(x in done for x in ret.get(y,())): done.add(y); prog=True
    return len(done)==len(cd)

seed=int(sys.argv[1]); n=int(sys.argv[2]); rng=random.Random(seed)
confs=0; cyc=0; viol=0; t0=time.time()
for gi in range(n):
    W=H=rng.choice((6,8,10)); p=rng.choice((0.2,0.3,0.4,0.5))
    grid=random_grid(rng,W,H,p); cells=grid.free_cells()
    if not cells: continue
    s=rng.choice(cells); M=Model(grid,s); comp=M.component()
    for k in range(5):
        cd=random_terminal(M,rng)
        for it in range(30):
            cd2=dict(cd); ret=returned(M,cd2)
            # mutate: flip directions of a few cells to other returned directions
            cand=[x for x in cd2 if x!=s and len(ret.get(x,()))>1]
            if not cand: break
            for x in rng.sample(cand, min(len(cand), rng.randint(1,3))):
                cd2[x]=rng.choice(sorted(ret[x]))
            # optionally delete some closed cells not needed? keep simple
            if not repair(M,cd2,rng): continue
            confs+=1
            if not is_tree(M,cd2): cyc+=1
            V={s}
            for x,d in cd2.items(): V|=M.scan(x,d)[1]
            if V!=comp:
                viol+=1
                if viol<=3: print('VIOL',sorted(comp-V)); print(grid_to_str(grid,s,None,sorted(comp-V))); print(cd2)
            cd=cd2
print(f'configs {confs}, non-tree {cyc}, violations {viol}, {time.time()-t0:.0f}s')
