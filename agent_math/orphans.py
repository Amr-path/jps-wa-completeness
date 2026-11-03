"""Orphan analysis in terminal configs (random orders). For each orphan f (sub-ray stop, f not closed) with sub-ray dir w from
diagonal cell z (closed), forced side e*: who visits f+w and f+e*? classify origin: z itself, witness of z, other."""
import sys, random
from collections import Counter
from common import *
seed=int(sys.argv[1]); n=int(sys.argv[2]); rng=random.Random(seed)
cnt=Counter(); shown=0; norph=0
for gi in range(n):
    W=H=rng.choice((6,8,10)); p=rng.choice((0.2,0.3,0.4,0.5))
    grid=random_grid(rng,W,H,p); cells=grid.free_cells()
    if not cells: continue
    s=rng.choice(cells); M=Model(grid,s); g=grid
    for k in range(3):
        cd={}; pend=[(s,(0,0))]; visitors={}; orph=[]
        def jr(x0,y0,dx,dy,origin,top,z):
            while True:
                if not g.legal(x0,y0,dx,dy): return None
                x0+=dx;y0+=dy; visitors.setdefault((x0,y0),[]).append((origin,top,(dx,dy),z))
                if dx and dy:
                    r=jr(x0,y0,dx,0,origin,top,(x0,y0))
                    if r is not None: orph.append((r,(dx,0),(x0,y0),origin)); return (x0,y0)
                    r=jr(x0,y0,0,dy,origin,top,(x0,y0))
                    if r is not None: orph.append((r,(0,dy),(x0,y0),origin)); return (x0,y0)
                else:
                    if M.J.has_forced(x0,y0,dx,dy): return (x0,y0)
        while pend:
            x,d=pend.pop(rng.randrange(len(pend)))
            if x in cd: continue
            cd[x]=d
            for e in M.succ_dirs(x,d):
                r=jr(x[0],x[1],e[0],e[1],x,e,None)
                if r is not None and r not in cd: pend.append((r,e))
        # witnesses: cell -> set of closed cells whose scan returns (cell, dA(cell))
        wit={}
        for x,d in cd.items():
            for (y,e) in M.scan(x,d)[0]:
                if y in cd and cd[y]==e: wit.setdefault(y,set()).add(x)
        for (f,w,z,o) in orph:
            if f in cd: continue
            norph+=1
            es=[e for e in ([(0,1),(0,-1)] if w[0] else [(1,0),(-1,0)]) if not g.free(f[0]-w[0]+e[0],f[1]-w[1]+e[1]) and g.free(f[0]+e[0],f[1]+e[1])]
            targets=[('fwd',(f[0]+w[0],f[1]+w[1]))]+[('side',(f[0]+e[0],f[1]+e[1])) for e in es]
            for kind,c in targets:
                if not g.free(*c): continue
                vs=visitors.get(c,[])
                if not vs and c!=s: print('UNVISITED', c)
                cls=set()
                for (origin,top,rd,zz) in vs:
                    if origin==z: cls.add('z-scan')
                    elif origin in wit.get(z,()): cls.add('z-witness')
                    elif origin==o: cls.add('o-scan')
                    else: cls.add('other')
                cnt[(kind,frozenset(cls))]+=1
                if shown<5 and cls=={'other'}:
                    shown+=1
                    print(f'orphan f={f} w={w} z={z} dA(z)={cd[z]} o={o} kind={kind} c={c} visitors={[(a,b,c2) for a,b,c2,_ in vs]}')
                    print(grid_to_str(grid,s,None,[f,c,z]))
print('orphans',norph)
for k,v in cnt.most_common(): print(' ',k[0],sorted(k[1]),v)
