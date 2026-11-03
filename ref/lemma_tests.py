"""Candidate-lemma checks on terminal configurations of canonical JPS (no target, random orders)."""
import random, sys, time
from jpswa import Grid, CanonicalJPS, grid_to_str, DIRS8
from coverage_notarget import component

def terminal(grid, s, rng):
    J = CanonicalJPS(grid, s, (-99,-99), 1.0, 'hig')
    visited = {s}
    def jump_rec(x, y, dx, dy):
        g = J.g
        while True:
            if not g.legal(x, y, dx, dy): return None
            x += dx; y += dy; visited.add((x, y))
            if dx and dy:
                if jump_rec(x, y, dx, 0) is not None or jump_rec(x, y, 0, dy) is not None: return (x, y)
            else:
                if J.has_forced(x, y, dx, dy): return (x, y)
    closed = {}; open_ = [(s, (0, 0))]
    while open_:
        x, d = open_.pop(rng.randrange(len(open_)))
        if x in closed: continue
        closed[x] = d
        for e in J.successor_dirs(x[0], x[1], d[0], d[1]):
            y = jump_rec(x[0], x[1], e[0], e[1])
            if y is not None and y not in closed: open_.append((y, e))
    return J, visited, closed

def check_local_saturation(grid, J, visited, closed):
    """For every closed x and every legal arrival d2 into x, all legal canonical successors of (x,d2) are visited."""
    viol = []
    for x, d1 in closed.items():
        for d2 in DIRS8:
            px, py = x[0]-d2[0], x[1]-d2[1]
            if not grid.legal(px, py, d2[0], d2[1]): continue   # d2 not a feasible arrival
            for e in J.successor_dirs(x[0], x[1], d2[0], d2[1]):
                if grid.legal(x[0], x[1], e[0], e[1]):
                    c = (x[0]+e[0], x[1]+e[1])
                    if c not in visited: viol.append((x, d1, d2, e))
    return viol

def check_closed_neighbors(grid, visited, closed):
    """Every legal neighbour of every closed cell is visited."""
    viol=[]
    for x in closed:
        for e in DIRS8:
            if grid.legal(x[0],x[1],e[0],e[1]) and (x[0]+e[0],x[1]+e[1]) not in visited: viol.append((x,e))
    return viol

def main(seed, n):
    rng = random.Random(seed); runs=0; v1=v2=0; t0=time.time()
    for _ in range(n):
        W=H=rng.choice((5,6,7,8,10)); p=rng.choice((0.2,0.3,0.4,0.5,0.6))
        grid=Grid(W,H,[(x,y) for y in range(H) for x in range(W) if rng.random()<p])
        cells=grid.free_cells()
        if not cells: continue
        for _ in range(3):
            s=rng.choice(cells)
            for k in range(10):
                runs+=1
                J,V,C=terminal(grid,s,rng)
                a=check_local_saturation(grid,J,V,C)
                b=check_closed_neighbors(grid,V,C)
                if a:
                    v1+=1
                    if v1<=3: print('LOCAL-SAT violation',a[:3]); print(grid_to_str(grid,s,None,[t[0] for t in a]))
                if b:
                    v2+=1
                    if v2<=3: print('CLOSED-NBR violation',b[:3]); print(grid_to_str(grid,s,None,[t[0] for t in b]))
    print(f'seed {seed}: runs {runs}, local-saturation violations {v1}, closed-neighbour violations {v2}, {time.time()-t0:.0f}s')

if __name__=='__main__': main(int(sys.argv[1]), int(sys.argv[2]))
