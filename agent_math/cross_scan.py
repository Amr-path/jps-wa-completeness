"""For terminal configs: pairs (p,c=p+u), c free, both in V. 'same-scan' if some closed o has p,c both in Scan(o)∪{o}.
Otherwise cross-scan: classify how c is visited: ('ray-dir of visit to c' relative to u, whether c closed, kind)."""
import sys, random, time
from collections import Counter
from common import *
from static_mutate import random_terminal
seed=int(sys.argv[1]); n=int(sys.argv[2]); rng=random.Random(seed)
pairs=0; cross=0; cnt=Counter(); t0=time.time(); ex=[]
def rel(u,v):
    if v==u: return 'fwd'
    if v==(-u[0],-u[1]): return 'back'
    if v[0]==0 or v[1]==0: return 'perp'
    dot=u[0]*v[0]+u[1]*v[1]
    return 'diag+' if dot>0 else 'diag-'
for gi in range(n):
    W=H=rng.choice((6,8,10)); p=rng.choice((0.2,0.3,0.4,0.5))
    grid=random_grid(rng,W,H,p); cells=grid.free_cells()
    if not cells: continue
    s=rng.choice(cells); M=Model(grid,s)
    for k in range(3):
        cd=random_terminal(M,rng)
        scanof={}   # cell -> set of closed origins whose scan contains it (or itself)
        visdirs={}  # cell -> set of ray directions (straight: w ; diagonal: (a,b)) of rays stepping on it
        for x,d in cd.items():
            scanof.setdefault(x,set()).add(x)
            for e in M.succ_dirs(x,d):
                # replay ray to get directions
                g=M.g
                def jr(x0,y0,dx,dy):
                    while True:
                        if not g.legal(x0,y0,dx,dy): return None
                        x0+=dx;y0+=dy; scanof.setdefault((x0,y0),set()).add(x); visdirs.setdefault((x0,y0),set()).add((dx,dy))
                        if dx and dy:
                            if jr(x0,y0,dx,0) is not None or jr(x0,y0,0,dy) is not None: return (x0,y0)
                        else:
                            if M.J.has_forced(x0,y0,dx,dy): return (x0,y0)
                jr(x[0],x[1],e[0],e[1])
        V=set(scanof)|{s}
        for p_ in V:
            for u in STRAIGHT:
                c=(p_[0]+u[0],p_[1]+u[1])
                if not M.g.free(*c): continue
                pairs+=1
                if c not in V: print('T VIOLATION'); continue
                if scanof.get(p_,set())&scanof.get(c,set()): continue
                cross+=1
                key=(c in cd, p_ in cd, frozenset(rel(u,v) for v in visdirs.get(c,())))
                cnt[key]+=1
                if len(ex)<6 and not (c in cd) and not(p_ in cd): ex.append((grid,s,p_,c,cd,visdirs.get(c)))
print(f'pairs {pairs}, cross-scan {cross}')
for k,v in cnt.most_common(): print('  c_closed',k[0],'p_closed',k[1],sorted(k[2]),v)
for grid,s,p_,c,cd,vd in ex[:4]:
    print('p',p_,'c',c,'c visited by ray dirs',vd); print(grid_to_str(grid,s,None,[p_,c]))
