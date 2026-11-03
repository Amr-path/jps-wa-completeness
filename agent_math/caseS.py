"""Case S: sub-jump stopping cells p (forced w.r.t. the sub-jump direction d) that are NEVER closed.
For their forced-side cells c=p+u (p-d+u blocked, c free): who visits c? classify."""
import sys, random
from collections import Counter, defaultdict
sys.path.insert(0,'/home/claude/jps-wa/ref')
from jpswa import Grid, CanonicalJPS, DIRS8, grid_to_str

def run(grid, s, rng):
    J=CanonicalJPS(grid,s,(-99,-99),1.0,'hig')
    visits=defaultdict(list)   # cell -> list of (origin, topdir, kind) kind: 'top','sub','diag'
    substop=[]                 # (p, d, z, origin)  sub-jump from z in dir d stopped at p
    closed={}; cur={}
    def jr(x,y,dx,dy,top,sub_from):
        while True:
            if not grid.legal(x,y,dx,dy): return None
            x+=dx;y+=dy
            kind='diag' if (dx and dy) else ('sub' if sub_from else 'top')
            visits[(x,y)].append((cur['o'],top,kind))
            if dx and dy:
                r=jr(x,y,dx,0,top,(x,y))
                if r is not None: substop.append((r,(dx,0),(x,y),cur['o'])); return (x,y)
                r=jr(x,y,0,dy,top,(x,y))
                if r is not None: substop.append((r,(0,dy),(x,y),cur['o'])); return (x,y)
            else:
                if J.has_forced(x,y,dx,dy): return (x,y)
    pend=[(s,(0,0))]
    while pend:
        x,d=pend.pop(rng.randrange(len(pend)))
        if x in closed: continue
        closed[x]=d; cur['o']=x
        for e in J.successor_dirs(x[0],x[1],d[0],d[1]):
            y=jr(x[0],x[1],e[0],e[1],e,None)
            if y is not None and y not in closed: pend.append((y,e))
    return J,visits,closed,substop

rng=random.Random(int(sys.argv[1])); cnt=Counter(); tot=0; shown=0; nsub=0
for _ in range(int(sys.argv[2])):
    W=H=rng.choice((6,8,10,12)); p=rng.choice((0.2,0.3,0.4,0.5))
    grid=Grid(W,H,[(x,y) for y in range(H) for x in range(W) if rng.random()<p]); cells=grid.free_cells()
    if not cells: continue
    s=rng.choice(cells)
    for k in range(3):
        J,visits,closed,substop=run(grid,s,rng)
        for (p_,d,z,o) in substop:
            if p_ in closed: continue
            nsub+=1
            dx,dy=d
            for u in ([(0,1),(0,-1)] if dx else [(1,0),(-1,0)]):
                if (not grid.free(p_[0]-dx+u[0],p_[1]-dy+u[1])) and grid.free(p_[0]+u[0],p_[1]+u[1]):
                    c=(p_[0]+u[0],p_[1]+u[1]); tot+=1
                    vs=visits.get(c,[])
                    kinds=frozenset((('z' if oo==z else 'o' if oo==o else 'other'),kind) for oo,top,kind in vs)
                    cnt[kinds]+=1
                    if not vs: print('UNVISITED!!')
                    if shown<4 and all(k[0]=='other' for k in kinds):
                        shown+=1
                        print('p',p_,'d',d,'z',z,'dA(z)',closed.get(z),'origin',o,'c',c,'visitors',vs)
                        print(grid_to_str(grid,s,None,[c,p_,z]))
print('never-closed sub-stop cells',nsub,'forced-side cells',tot)
for k,v in cnt.most_common(): print(' ',sorted(k),v)
