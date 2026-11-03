import sys, random, math
sys.path.insert(0,'/home/claude/jps-wa/ref')
from jpswa import Grid
from dijps import GridCC, BoundedJPS, JPScc
from adversary_variants import VAdversary, dijkstra_g
seed=int(sys.argv[1]); n=int(sys.argv[2])
for variant in ('cc','bjps'):
    rng=random.Random(seed); inst=fails=und=0
    for _ in range(n):
        W=H=rng.choice((4,5,6)); p=rng.choice((0.25,0.35,0.45))
        blocked=[(x,y) for y in range(H) for x in range(W) if rng.random()<p]
        grid=GridCC(W,H,blocked) if variant=='cc' else Grid(W,H,blocked)
        cells=grid.free_cells()
        if len(cells)<2: continue
        for _ in range(4):
            s,t=rng.sample(cells,2)
            if math.isinf(dijkstra_g(grid,s,t)): continue
            inst+=1
            A=VAdversary(grid,s,t,JPScc) if variant=='cc' else VAdversary(grid,s,t,BoundedJPS,b=2)
            ok,order=A.can_fail(limit_states=200000)
            if ok is None: und+=1
            elif ok: fails+=1
    print(f'seed {seed} variant {variant}: instances {inst} failing {fails} undecided {und}', flush=True)
