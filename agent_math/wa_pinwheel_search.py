"""Random search for a WA*-realisable failure in a pinwheel family: NxN grid, central 2x2 hole, the four
pinwheel obstacles at parametrised offsets, random extra obstacles (0-6), random s, t in hole, w in a set,
exhaustive WA*-restricted adversary (adversarial ties)."""
import sys, math, random, time
sys.path.insert(0,'/home/claude/jps-wa/ref')
from jpswa import Grid, grid_to_str, dijkstra
from pinwheel_wastar import wastar_adversary
seed=int(sys.argv[1]); n=int(sys.argv[2]); rng=random.Random(seed)
ws=[1.0,1.1,1.25,1.5,2.0,3.0,10.0,1000.0]
t0=time.time(); fails=0; runs=0
for it in range(n):
    N=rng.choice((8,9,10)); c=N//2   # hole = (c-1..c, c-1..c)
    hole=[(c-1,c-1),(c,c-1),(c-1,c),(c,c)]
    a=rng.randint(1,3); b=rng.randint(1,3)   # pinwheel obstacle offsets
    # obstacles: above-left-ish of hole corners, rotated 4-fold about hole centre (c-0.5,c-0.5)
    def rot(p): x,y=p; return (c-0.5-(y-(c-0.5)), c-0.5+(x-(c-0.5)))
    p=(c-1-a+0.0, c-1-b-1.0)   # e.g. a=b=1 gives (c-2, c-3) ~ (3,1) for N=8,c=4 ... approximate
    obs=set()
    q=(c-1-a, c-1-b)
    for _ in range(4):
        obs.add((int(round(q[0])),int(round(q[1])))); q=rot(q)
    for _ in range(rng.randint(0,6)):
        obs.add((rng.randrange(N),rng.randrange(N)))
    obs-= set(hole)
    g=Grid(N,N,list(obs)); free=[x for x in g.free_cells() if x not in hole]
    s=rng.choice(free); t=rng.choice(hole)
    if dijkstra(g,s,t)==math.inf: continue
    for w in ws:
        runs+=1
        r,o=wastar_adversary(g,s,t,w,limit=200000)
        if r=='FAIL':
            fails+=1; print('WA* FAILURE w=',w,'s=',s,'t=',t); print(grid_to_str(g,s,t)); print(o); sys.stdout.flush(); break
    if (it+1)%100==0: print(f'{it+1} grids {runs} runs {fails} failures {time.time()-t0:.0f}s'); sys.stdout.flush()
print('done',fails)
