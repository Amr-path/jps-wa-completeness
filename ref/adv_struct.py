import random, math, sys, time
from jpswa import Grid, dijkstra, grid_to_str
from adversary import Adversary

def maze(rng, W, H):
    # recursive-backtracker maze on odd lattice, plus random extra openings
    cells=set(); W2=W if W%2 else W-1; H2=H if H%2 else H-1
    blocked=set((x,y) for x in range(W) for y in range(H))
    stack=[(1,1)]; blocked.discard((1,1))
    while stack:
        x,y=stack[-1]; nb=[(x+dx,y+dy,x+dx//2,y+dy//2) for dx,dy in((2,0),(-2,0),(0,2),(0,-2)) if 1<=x+dx<W2-0 and 1<=y+dy<H2 and (x+dx,y+dy) in blocked]
        if nb:
            nx,ny,mx,my=rng.choice(nb); blocked.discard((nx,ny)); blocked.discard((mx,my)); stack.append((nx,ny))
        else: stack.pop()
    for (x,y) in list(blocked):
        if rng.random()<0.08: blocked.discard((x,y))
    return Grid(W,H,blocked)

def rooms(rng, W, H):
    blocked=set()
    for x in range(W):
        for y in range(H):
            if (x%4==3 or y%4==3) and rng.random()>0.3: blocked.add((x,y))
    for _ in range(W*H//10): blocked.add((rng.randrange(W),rng.randrange(H)))
    return Grid(W,H,blocked)

def main(seed,n):
    rng=random.Random(seed); inst=fails=und=0; t0=time.time()
    for i in range(n):
        W=H=rng.choice((7,8,9,10,11))
        grid=maze(rng,W,H) if i%2==0 else rooms(rng,W,H)
        cells=grid.free_cells()
        if len(cells)<2: continue
        for _ in range(4):
            s,t=rng.sample(cells,2)
            if math.isinf(dijkstra(grid,s,t)): continue
            inst+=1
            ok,order=Adversary(grid,s,t).can_fail(limit_states=300000)
            if ok is None: und+=1
            elif ok:
                fails+=1; print('ADVERSARIAL FAILURE'); print(grid_to_str(grid,s,t)); print(order); sys.stdout.flush()
    print(f'seed {seed}: instances {inst}, adversarial failures {fails}, undecided {und}, {time.time()-t0:.0f}s')
main(int(sys.argv[1]),int(sys.argv[2]))
