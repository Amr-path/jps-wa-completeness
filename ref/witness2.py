"""For DROPPED entries only (directions actually generated at x but not chosen), classify who covers the
lost first-level scan cells: ancestors of x (incl. parent), x itself, descendants, or other branches."""
import random, sys
from collections import Counter, defaultdict
from jpswa import Grid, CanonicalJPS, grid_to_str, DIRS8

def run(grid, s, rng):
    J=CanonicalJPS(grid,s,(-99,-99),1.0,'hig'); visits=defaultdict(list); closed={}; gen=defaultdict(set); cur={}
    def jr(x,y,dx,dy,top):
        while True:
            if not grid.legal(x,y,dx,dy): return None
            x+=dx;y+=dy; visits[(x,y)].append((cur['o'],top,cur['t']))
            if dx and dy:
                if jr(x,y,dx,0,top) is not None or jr(x,y,0,dy,top) is not None: return (x,y)
            else:
                if J.has_forced(x,y,dx,dy): return (x,y)
    pend=[(s,(0,0),None)]; t=0
    while pend:
        x,d,par=pend.pop(rng.randrange(len(pend)))
        if x in closed: continue
        closed[x]=(d,par,t); cur['o']=x; cur['t']=t
        for e in J.successor_dirs(x[0],x[1],d[0],d[1]):
            y=jr(x[0],x[1],e[0],e[1],e)
            if y is not None:
                gen[y].add(e)
                if y not in closed: pend.append((y,e,x))
        t+=1
    return J,visits,closed,gen

def vscan_cells(J,grid,x,d):
    vis=set()
    def jr(x0,y0,dx,dy):
        while True:
            if not grid.legal(x0,y0,dx,dy): return None
            x0+=dx;y0+=dy; vis.add((x0,y0))
            if dx and dy:
                if jr(x0,y0,dx,0) is not None or jr(x0,y0,0,dy) is not None: return (x0,y0)
            else:
                if J.has_forced(x0,y0,dx,dy): return (x0,y0)
    for e in J.successor_dirs(x[0],x[1],d[0],d[1]): jr(x[0],x[1],e[0],e[1])
    return vis

def anc(closed,x):
    out=set()
    while x is not None: out.add(x); x=closed[x][1]
    return out

rng=random.Random(int(sys.argv[1])); cls=Counter(); tot=0; nonanc=0; ex=[]
for _ in range(int(sys.argv[2])):
    W=H=rng.choice((6,8,10,12)); p=rng.choice((0.2,0.3,0.4,0.5))
    grid=Grid(W,H,[(x,y) for y in range(H) for x in range(W) if rng.random()<p]); cells=grid.free_cells()
    if not cells: continue
    s=rng.choice(cells)
    for k in range(3):
        J,visits,closed,gen=run(grid,s,rng)
        for x,(dA,par,tx) in closed.items():
            if x==s: continue
            A=anc(closed,x); own=vscan_cells(J,grid,x,dA)
            for d2 in gen[x]:
                if d2==dA: continue
                lost=vscan_cells(J,grid,x,d2)-own
                for c in lost:
                    tot+=1
                    kinds=set()
                    for (o,top,to) in visits.get(c,[]):
                        kinds.add('self' if o==x else 'ancestor' if o in A else 'descendant' if x in anc(closed,o) else 'other')
                    cls[frozenset(kinds)]+=1
                    if not (kinds&{'self','ancestor'}):
                        nonanc+=1
                        if len(ex)<2: ex.append((grid,s,x,dA,par,d2,c,visits.get(c,[]),closed))
print('lost cells of DROPPED entries:',tot)
for k,v in cls.most_common(): print(' ',sorted(k),v)
print('covered by no ancestor/self:',nonanc)
for grid,s,x,dA,par,d2,c,vs,closed in ex:
    print('\nx',x,'closed',dA,'parent',par,'dropped',d2,'lost cell',c,'visitors',[(o,top) for o,top,_ in vs])
    print(grid_to_str(grid,s,None,[c])); print('x:'); print(grid_to_str(grid,s,None,[x]))
