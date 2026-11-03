import sys, random, math, time
from jpswa import Grid, CanonicalJPS, dijkstra, grid_to_str
seed=int(sys.argv[1]); n=int(sys.argv[2])
rng=random.Random(seed); fails=[]; inst=0; t0=time.time()
for gi in range(n):
    W=H=rng.choice((5,6,7,8,9,10,12))
    p=rng.choice((0.25,0.35,0.45,0.55))
    grid=Grid(W,H,[(x,y) for y in range(H) for x in range(W) if rng.random()<p])
    cells=grid.free_cells()
    if len(cells)<2: continue
    for _ in range(8):
        s,t=rng.sample(cells,2); opt=dijkstra(grid,s,t)
        if math.isinf(opt): continue
        for k in range(6):
            inst+=1
            J=CanonicalJPS(grid,s,t,1.0,'rand'); J.rng=random.Random(rng.random())
            c,_=J.search()
            if math.isinf(c): fails.append(('RAND',grid,s,t,c,opt))
        inst+=1
        c,_=CanonicalJPS(grid,s,t,1.0,'greedy').search()
        if math.isinf(c): fails.append(('GREEDY',grid,s,t,c,opt))
print(f"seed {seed}: {inst} runs, {len(fails)} failures, {time.time()-t0:.0f}s")
for kind,grid,s,t,c,opt in fails[:10]:
    print('---',kind,c,opt); print(grid_to_str(grid,s,t))
