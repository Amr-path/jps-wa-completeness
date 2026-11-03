"""Does every reachable cell get visited with cost exactly g*(v) under arbitrary order? (likely false; test)"""
import random, sys, math, time
from jpswa import Grid, CanonicalJPS, grid_to_str, DIRS8, SQ2
import heapq
def dists(grid,s):
    dist={s:0.0}; pq=[(0.0,s)]
    while pq:
        d,(x,y)=heapq.heappop(pq)
        if d>dist[(x,y)]+1e-12: continue
        for dx,dy in DIRS8:
            if grid.legal(x,y,dx,dy):
                n=(x+dx,y+dy); nd=d+(SQ2 if dx and dy else 1)
                if nd<dist.get(n,math.inf)-1e-12: dist[n]=nd; heapq.heappush(pq,(nd,n))
    return dist
def terminal(grid,s,rng):
    J=CanonicalJPS(grid,s,(-99,-99),1.0,'hig'); best={s:0.0}
    def jr(x,y,dx,dy,gg):
        g=J.g
        while True:
            if not g.legal(x,y,dx,dy): return None
            x+=dx;y+=dy;gg+=SQ2 if dx and dy else 1
            if gg<best.get((x,y),math.inf): best[(x,y)]=gg
            if dx and dy:
                if jr(x,y,dx,0,gg) is not None or jr(x,y,0,dy,gg) is not None: return (x,y,gg)
            else:
                if J.has_forced(x,y,dx,dy): return (x,y,gg)
    closed={}; open_=[(s,(0,0),0.0)]; gval={s:0.0}
    while open_:
        x,d,gx=open_.pop(rng.randrange(len(open_)))
        if x in closed: continue
        closed[x]=(d,gx)
        for e in J.successor_dirs(x[0],x[1],d[0],d[1]):
            r=jr(x[0],x[1],e[0],e[1],gx)
            if r is None: continue
            y=(r[0],r[1])
            if y in closed: continue
            open_.append((y,e,r[2]))
    return best,closed
rng=random.Random(int(sys.argv[1])); runs=0; bad_runs=0; badcells=0; tot=0
for _ in range(int(sys.argv[2])):
    W=H=rng.choice((6,8,10)); p=rng.choice((0.2,0.3,0.4,0.5))
    grid=Grid(W,H,[(x,y) for y in range(H) for x in range(W) if rng.random()<p]); cells=grid.free_cells()
    if not cells: continue
    s=rng.choice(cells); dist=dists(grid,s)
    for k in range(5):
        runs+=1; best,closed=terminal(grid,s,rng); b=0
        for v,dv in dist.items():
            tot+=1
            if abs(best.get(v,math.inf)-dv)>1e-9: b+=1
        if b: bad_runs+=1; badcells+=b
print(f'runs {runs}, runs with some cell never visited at optimal cost: {bad_runs}; such cells {badcells}/{tot}')
