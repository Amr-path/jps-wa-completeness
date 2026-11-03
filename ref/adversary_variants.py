import random, math, sys, itertools
from jpswa import Grid, CanonicalJPS, dijkstra, grid_to_str, DIRS8
from dijps import GridCC, BoundedJPS, JPScc
from adversary import Adversary

def dijkstra_g(grid,s,t):
    import heapq
    SQ2=math.sqrt(2); dist={s:0.0}; pq=[(0.0,s)]
    while pq:
        d,(x,y)=heapq.heappop(pq)
        if (x,y)==t: return d
        if d>dist[(x,y)]+1e-12: continue
        for dx,dy in DIRS8:
            if grid.legal(x,y,dx,dy):
                n=(x+dx,y+dy); nd=d+(SQ2 if dx and dy else 1)
                if nd<dist.get(n,math.inf)-1e-12: dist[n]=nd; heapq.heappush(pq,(nd,n))
    return math.inf

class VAdversary(Adversary):
    def __init__(self,grid,s,t,Jcls,**kw):
        self.g=grid; self.s,self.t=s,t; self.J=Jcls(grid,s,t,1.0,'hig',**kw); self.jump_cache={}; self.succ_cache={}

def search(variant, seed, n, sizes):
    rng=random.Random(seed); found=[]; inst=0; undecided=0
    for _ in range(n):
        W=H=rng.choice(sizes); p=rng.choice((0.25,0.35,0.45))
        blocked=[(x,y) for y in range(H) for x in range(W) if rng.random()<p]
        grid=GridCC(W,H,blocked) if variant=='cc' else Grid(W,H,blocked)
        cells=grid.free_cells()
        if len(cells)<2: continue
        for _ in range(4):
            s,t=rng.sample(cells,2)
            if math.isinf(dijkstra_g(grid,s,t)): continue
            inst+=1
            if variant=='cc': A=VAdversary(grid,s,t,JPScc)
            else: A=VAdversary(grid,s,t,BoundedJPS,b=2)
            ok,order=A.can_fail(limit_states=200000)
            if ok is None: undecided+=1
            elif ok: found.append((W,grid,s,t,order))
    return inst,found,undecided

if __name__=='__main__':
    seed=int(sys.argv[1]) if len(sys.argv)>1 else 1; n=int(sys.argv[2]) if len(sys.argv)>2 else 400
    for variant in ('cc','bjps'):
        inst,found,und=search(variant,seed,n,(4,5,6))
        print(f'variant {variant}: instances {inst}, adversarial failures {len(found)}, undecided {und}')
        if found:
            found.sort(key=lambda f:(f[0],len(f[4])))
            W,grid,s,t,order=found[0]
            print(' smallest failing instance:'); print(grid_to_str(grid,s,t)); print(' failing order:',order)
            realised=0
            for (W,grid,s,t,order) in found:
                for w in (1.2,2,4,8,20,100):
                    for tie in ('hig','log','fifo','lifo','greedy'):
                        J=JPScc(grid,s,t,w,tie) if variant=='cc' else BoundedJPS(grid,s,t,w,tie,b=2)
                        c,_=J.search()
                        if math.isinf(c): realised+=1
            print(f' failing instances realised by some WA* order (instance x w x tie count): {realised}')
