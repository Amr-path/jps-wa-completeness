"""Static test: enumerate configurations (C,dA) satisfying
 P0: s in C (dA(s)=(0,0))
 P1: for x in C every jump point returned by Scan(x,dA(x)) is in C
 with dA(x) any FEASIBLE arrival direction (x-dA free and move legal), or optionally only P2-directions
 (dA(x) is a direction with which x is returned by some closed cell).
Check (T): union of scans == component."""
import sys, random, time
from common import *

def feasible_dirs(M, x):
    g=M.g; out=[]
    for d in DIRS8:
        if g.legal(x[0]-d[0], x[1]-d[1], d[0], d[1]): out.append(d)
    return out

def enum_static(M, mode, limit=200000):
    """DFS: state = frozenset of (cell,dir). Expand: pick an unclosed jump point required by P1 and assign a direction."""
    s=M.s
    start=frozenset({(s,(0,0))})
    seen=set(); stack=[start]; n=0
    while stack:
        st=stack.pop()
        if st in seen: continue
        seen.add(st); n+=1
        if n>limit: return
        cd=dict(st)
        need=set()
        for x,d in st:
            for (y,e) in M.scan(x,d)[0]:
                if y not in cd: need.add(y)
        if not need:
            yield cd
            continue
        y=min(need)
        if mode=='feasible': dirs=feasible_dirs(M,y)
        else:
            dirs=set()
            for x,d in st:
                for (yy,e) in M.scan(x,d)[0]:
                    if yy==y: dirs.add(e)
        for d in dirs:
            stack.append(st|{(y,d)})

if __name__=='__main__':
    mode=sys.argv[3] if len(sys.argv)>3 else 'feasible'
    seed=int(sys.argv[1]); n=int(sys.argv[2]); rng=random.Random(seed)
    confs=0; viol=0; t0=time.time(); shown=0
    for gi in range(n):
        W=rng.choice((4,5,6)); H=rng.choice((4,5,6)); p=rng.choice((0.2,0.3,0.4))
        grid=random_grid(rng,W,H,p); cells=grid.free_cells()
        if not cells: continue
        s=rng.choice(cells); M=Model(grid,s); comp=M.component()
        for cd in enum_static(M,mode,limit=5000):
            confs+=1
            V={s}
            for x,d in cd.items(): V|=M.scan(x,d)[1]
            if V!=comp:
                viol+=1
                if shown<3:
                    shown+=1; print('VIOL missing',sorted(comp-V)); print(grid_to_str(grid,s,None,sorted(comp-V))); print(cd)
    print(f'mode {mode}: configs {confs}, (T) violations {viol}, {time.time()-t0:.0f}s')
