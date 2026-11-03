"""Test LS: for every closed (x,dA) and every feasible arrival d' into x, all cells scanned by a full
(top-level) expansion of (x,d') are in V (terminal visited set), under random orders, no target."""
import random, sys, time
from jpswa import Grid, CanonicalJPS, grid_to_str, DIRS8
from lemma_tests import terminal

def vscan(J, grid, x, d):
    vis=set()
    def jr(x0,y0,dx,dy):
        g=J.g
        while True:
            if not g.legal(x0,y0,dx,dy): return None
            x0+=dx;y0+=dy; vis.add((x0,y0))
            if dx and dy:
                if jr(x0,y0,dx,0) is not None or jr(x0,y0,0,dy) is not None: return (x0,y0)
            else:
                if J.has_forced(x0,y0,dx,dy): return (x0,y0)
    for e in J.successor_dirs(x[0],x[1],d[0],d[1]): jr(x[0],x[1],e[0],e[1])
    return vis

rng=random.Random(int(sys.argv[1])); runs=0; viol=0; t0=time.time()
for _ in range(int(sys.argv[2])):
    W=H=rng.choice((6,8,10)); p=rng.choice((0.2,0.3,0.4,0.5))
    grid=Grid(W,H,[(x,y) for y in range(H) for x in range(W) if rng.random()<p]); cells=grid.free_cells()
    if not cells: continue
    for _ in range(2):
        s=rng.choice(cells)
        for k in range(8):
            runs+=1; J,V,C=terminal(grid,s,rng)
            for x,dA in C.items():
                for d2 in DIRS8:
                    if not grid.legal(x[0]-d2[0],x[1]-d2[1],d2[0],d2[1]): continue
                    miss=vscan(J,grid,x,d2)-V
                    if miss:
                        viol+=1
                        if viol<=3: print('LS violation at',x,'closed dir',dA,'alt dir',d2,'missing',sorted(miss)); print(grid_to_str(grid,s,None,sorted(miss)))
print(f'runs {runs}, LS violations {viol}, {time.time()-t0:.0f}s')
