# Re-derive the "order-dependent" count of the 7x7 exhaustive family with my own any-order search
import sys, math, collections
from myjps import Inst, exhaustive
N=7; c=(3,3)
D=[(1,0),(0,1),(-1,0),(0,-1)]
bl=set()
for i in range(4):
    dp,d=D[(i-1)%4],D[i]; bl.add((c[0]-2*dp[0]-d[0],c[1]-2*dp[1]-d[1]))
bl={b for b in bl if 0<=b[0]<N and 0<=b[1]<N}
from collections import deque
def reach(B,s,t):
    I=Inst(N,B,s,t); seen={s}; q=deque([s])
    while q:
        x,y=q.popleft()
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
            if I.legal(x,y,dx,dy) and (x+dx,y+dy) not in seen: seen.add((x+dx,y+dy)); q.append((x+dx,y+dy))
    return t in seen
cnt=collections.Counter(); n=0
for ex in [(x,y) for y in range(N) for x in range(N) if (x,y) not in bl and (x,y)!=c]:
    B=bl|{ex}
    for s in [(x,y) for y in range(N) for x in range(N) if (x,y) not in B and (x,y)!=c]:
        if not reach(B,s,c): continue
        n+=1
        r=exhaustive(Inst(N,B,s,c),limit=int(sys.argv[1]))
        cnt[r[0]]+=1
print('instances',n,dict(cnt))
