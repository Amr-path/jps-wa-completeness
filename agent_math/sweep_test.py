"""Test the origin-side sweep claim. For every executed straight ray (top-level or sub-ray) with direction w,
origin y0, cells y1..yk, side e: strip S_i=y_i+e free for i=0..m (maximal with m<=k). Let j = first index>=1 with
S_j forced w.r.t. w (from far side), else inf. Claim: for 1<=i<=min(j,m): S_i is stepped on by a straight ray in
direction w (row-parallel sweep) OR i==1 and S_1 is stepped on by a diagonal ray w+e from y0. And S_0 in V.
Report exceptions with details."""
import sys, random
from collections import Counter
from common import *
seed=int(sys.argv[1]); n=int(sys.argv[2]); rng=random.Random(seed)
cnt=Counter(); shown=0; rays=0
for gi in range(n):
    W=H=rng.choice((6,8,10)); p=rng.choice((0.2,0.3,0.4,0.5))
    grid=random_grid(rng,W,H,p); cells=grid.free_cells()
    if not cells: continue
    s=rng.choice(cells); M=Model(grid,s); g=grid
    for k in range(3):
        cd={}; pend=[(s,(0,0))]; steps={}; straight=[]  # straight rays: (origin, w, cells, kind)
        def jr(x0,y0,dx,dy,kind):
            cellsr=[]; ox,oy=x0,y0
            while True:
                if not g.legal(x0,y0,dx,dy): break
                x0+=dx;y0+=dy; cellsr.append((x0,y0)); steps.setdefault((x0,y0),set()).add((dx,dy))
                if dx and dy:
                    if jr(x0,y0,dx,0,'sub') is not None or jr(x0,y0,0,dy,'sub') is not None: 
                        return (x0,y0)
                else:
                    if M.J.has_forced(x0,y0,dx,dy):
                        straight.append(((ox,oy),(dx,dy),cellsr,kind)); return (x0,y0)
            if not (dx and dy): straight.append(((ox,oy),(dx,dy),cellsr,kind))
            return None
        while pend:
            x,d=pend.pop(rng.randrange(len(pend)))
            if x in cd: continue
            cd[x]=d
            for e in M.succ_dirs(x,d):
                r=jr(x[0],x[1],e[0],e[1],'top')
                if r is not None and r not in cd: pend.append((r,e))
        V=set(steps)|{s}
        for (o,w,cs,kind) in straight:
            if not cs: continue
            ys=[o]+cs
            for e in ([(0,1),(0,-1)] if w[0] else [(1,0),(-1,0)]):
                S=[(y[0]+e[0],y[1]+e[1]) for y in ys]
                m=0
                while m+1<len(S) and g.free(*S[m+1]): m+=1
                if not g.free(*S[0]) or m==0: continue
                rays+=1
                if S[0] not in V: print('S0 not in V!')
                j=None
                for i in range(1,m+1):
                    if M.J.has_forced(S[i][0],S[i][1],w[0],w[1]): j=i; break
                lim=min(m, j if j is not None else m)
                for i in range(1,lim+1):
                    ok = w in steps.get(S[i],set()) or (i==1 and (w[0]+e[0],w[1]+e[1]) in steps.get(S[1],set()))
                    if not ok:
                        cnt[(kind, i, 'origin_closed' if o in cd else 'origin_diag', str(cd.get(o)))]+=1
                        if shown<6 and kind=="sub" and o not in cd:
                            shown+=1; print(f'EXC kind={kind} origin={o} dA={cd.get(o)} w={w} e={e} i={i} S_i={S[i]} stepped by {steps.get(S[i])} S1 by {steps.get(S[1])}')
                            print(grid_to_str(grid,s,None,[S[i],o]))
print('rays with strip',rays)
for k,v in cnt.most_common(20): print(' ',k,v)
