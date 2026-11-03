import sys, random
from collections import Counter
from common import *
exec(open('sweep_test.py').read().split("seed=int")[0])
seed=int(sys.argv[1]); n=int(sys.argv[2]); rng=random.Random(seed)
cnt=Counter(); shown=0; rays=0
for gi in range(n):
    W=H=rng.choice((6,8,10)); p=rng.choice((0.2,0.3,0.4,0.5))
    grid=random_grid(rng,W,H,p); cells=grid.free_cells()
    if not cells: continue
    s=rng.choice(cells); M=Model(grid,s); g=grid
    for k in range(3):
        cd={}; pend=[(s,(0,0))]; steps={}; straight=[]
        def jr(x0,y0,dx,dy,kind):
            cellsr=[]; ox,oy=x0,y0
            while True:
                if not g.legal(x0,y0,dx,dy): break
                x0+=dx;y0+=dy; cellsr.append((x0,y0)); steps.setdefault((x0,y0),set()).add((dx,dy))
                if dx and dy:
                    if jr(x0,y0,dx,0,'sub') is not None or jr(x0,y0,0,dy,'sub') is not None: return (x0,y0)
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
                de=(w[0]+e[0],w[1]+e[1])
                # i=1 claim
                f0=M.J.has_forced(S[0][0],S[0][1],w[0],w[1])
                ok1 = w in steps.get(S[1],set()) or de in steps.get(S[1],set())
                if not ok1:
                    cnt[('i1', kind, 'S0forced' if f0 else 'S0free', 'oc' if o in cd else 'od', str(cd.get(o)))]+=1
                    if shown<4 and not f0:
                        shown+=1; print(f'EXC1 kind={kind} o={o} dA={cd.get(o)} w={w} e={e} S1={S[1]} by {steps.get(S[1])} S0 by {steps.get(S[0])} S0closed={S[0] in cd}'); print(grid_to_str(grid,s,None,[S[1],o]))
                # i>=2 claim: no forced S_l for 1<=l<i  => S_i stepped by w
                for i in range(2,m+1):
                    if any(M.J.has_forced(S[l][0],S[l][1],w[0],w[1]) for l in range(1,i)): break
                    if w not in steps.get(S[i],set()):
                        cnt[('i>=2',kind,i,'S1 by '+str(steps.get(S[1])), 'S1closed' if S[1] in cd else '')]+=1
print('rays with strip',rays)
for k,v in cnt.most_common(30): print(' ',k,v)
