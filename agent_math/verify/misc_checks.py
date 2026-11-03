"""(a) Theorem 3.1(iii): can the start be expanded more than once under state-closing (direction 0 plus a stopping direction)?
   (b) (L): popped f monotone at w=1 for cell-closing JPS with 4 tie rules; and "late improving arrival" never occurs at w=1.
   (c) equal-g arrivals with different directions (tie in parent choice) -- how often?"""
import sys, random, math
sys.path.insert(0,'/home/claude/jps-wa/ref')
from jpswa import Grid, CanonicalJPS, octile, dijkstra, SQ2, DIRS8
from dijps import DIJPS
rng = random.Random(7)
s_multi = 0; maxexp = 0; nonmono = 0; late_improve = 0; eqg_diffdir = 0; runs = 0; ex = None
for it in range(3000):
    W = H = rng.choice((5,6,7,8)); p = rng.choice((0.2,0.3,0.4))
    g = Grid(W,H,[(x,y) for y in range(H) for x in range(W) if rng.random()<p])
    cells = g.free_cells()
    if len(cells) < 2: continue
    s,t = rng.sample(cells,2)
    if math.isinf(dijkstra(g,s,t)): continue
    runs += 1
    # (a)
    D = DIJPS(g,s,t,1.0,'hig')
    # instrument: count expansions of s
    import itertools, heapq
    gval={(s,(0,0)):0.0}; closed=set(); open_=[]; cnt=itertools.count()
    def push(st,gc): heapq.heappush(open_,((gc+octile(st[0][0],st[0][1],t[0],t[1]),-gc,next(cnt)),st,gc))
    push((s,(0,0)),0.0); per={}
    while open_:
        _,st,gn=heapq.heappop(open_)
        if st in closed or gn>gval[st]+1e-12: continue
        closed.add(st); x,d=st; per[x]=per.get(x,0)+1
        if x==t: break
        for e in D.successor_dirs(x[0],x[1],d[0],d[1]):
            r=D.jump(x[0],x[1],e[0],e[1],gn)
            if r is None: continue
            j=((r[0],r[1]),e)
            if j in closed: continue
            if r[2]<gval.get(j,math.inf)-1e-12: gval[j]=r[2]; push(j,r[2])
    if per.get(s,0) > 1:
        s_multi += 1
        if ex is None: ex = (g, s, t, per[s])
    maxexp = max(maxexp, max(per.values()))
    # (b) and (c): cell-closing, w=1, all tie rules; instrument via subclass
    for tie in ('hig','log','fifo','lifo'):
        J = CanonicalJPS(g,s,t,1.0,tie)
        # replicate search with instrumentation
        gval={s:0.0}; parent={s:None}; closed=set(); cnt=itertools.count(); open_=[]; lastf=-1
        def push2(cell,gc):
            f=gc+octile(cell[0],cell[1],t[0],t[1]); c=next(cnt)
            key={'hig':(f,-gc,c),'log':(f,gc,c),'fifo':(f,c),'lifo':(f,-c)}[tie]
            heapq.heappush(open_,(key,cell,gc))
        push2(s,0.0)
        while open_:
            key,n,gn=heapq.heappop(open_)
            if n in closed or gn>gval[n]+1e-12: continue
            f=gn+octile(n[0],n[1],t[0],t[1])
            if f < lastf-1e-9: nonmono += 1
            lastf=max(lastf,f)
            closed.add(n)
            if n==t: break
            x,y=n; pp=parent[n]; d=(0,0) if pp is None else ((x>pp[0])-(x<pp[0]),(y>pp[1])-(y<pp[1]))
            for ddx,ddy in J.successor_dirs(x,y,d[0],d[1]):
                r=J.jump(x,y,ddx,ddy,gn)
                if r is None: continue
                j=(r[0],r[1])
                if j in closed:
                    if r[2] < gval[j]-1e-12: late_improve += 1
                    continue
                if abs(r[2]-gval.get(j,math.inf))<=1e-12:
                    # equal g: different direction than stored parent's?
                    pp=parent[j]; d0=((j[0]>pp[0])-(j[0]<pp[0]),(j[1]>pp[1])-(j[1]<pp[1]))
                    if d0 != (ddx,ddy): eqg_diffdir += 1
                if r[2]<gval.get(j,math.inf)-1e-12: gval[j]=r[2]; parent[j]=n; push2(j,r[2])
print(f'runs {runs}; state-closing: start expanded >1 times in {s_multi} runs, max expansions of a cell {maxexp}')
if ex:
    from jpswa import grid_to_str
    print('example (start expanded %d times):' % ex[3]); print(grid_to_str(ex[0], ex[1], ex[2]))
print(f'w=1 cell-closing: non-monotone popped f events {nonmono}; late improving arrivals into closed cells {late_improve}; equal-g arrivals with a different direction {eqg_diffdir}')
