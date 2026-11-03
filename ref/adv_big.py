import random, math, sys, time
from jpswa import Grid, dijkstra, grid_to_str
from adversary import Adversary
seed=int(sys.argv[1]); n=int(sys.argv[2]); rng=random.Random(seed); inst=fails=und=0; t0=time.time()
for i in range(n):
    W=rng.choice((7,8,9,10)); H=rng.choice((7,8,9,10)); p=rng.choice((0.2,0.3,0.4,0.5,0.6))
    grid=Grid(W,H,[(x,y) for y in range(H) for x in range(W) if rng.random()<p]); cells=grid.free_cells()
    if len(cells)<2: continue
    for _ in range(3):
        s,t=rng.sample(cells,2)
        if math.isinf(dijkstra(grid,s,t)): continue
        inst+=1
        if inst%50==0: print(f'progress {inst} instances, {fails} failures, {und} undecided, {time.time()-t0:.0f}s', flush=True)
        ok,order=Adversary(grid,s,t).can_fail(limit_states=150000)
        if ok is None: und+=1
        elif ok:
            fails+=1; print('ADVERSARIAL FAILURE'); print(grid_to_str(grid,s,t)); print(order); sys.stdout.flush()
    if time.time()-t0>1500: break
print(f'seed {seed}: instances {inst}, adversarial failures {fails}, undecided {und}, {time.time()-t0:.0f}s')
