"""Empirical catalog of strip-break resolutions.
For executed straight scans (top-level, direction w) from origin o, strip side e: find the first w-forced strip cell z
(z - w + e blocked, z + e free). Record how z is closed and which scan directions visit z+w (if free)."""
import random, sys
from collections import Counter, defaultdict
from jpswa import Grid, CanonicalJPS, DIRS8
from witness_analysis import run

def perp(w): return [(w[1],w[0]),(-w[1],-w[0])]
rng=random.Random(int(sys.argv[1])); cat=Counter(); visdir=Counter(); n=0
for _ in range(int(sys.argv[2])):
    W=H=rng.choice((8,10,12,14)); p=rng.choice((0.2,0.3,0.4))
    grid=Grid(W,H,[(x,y) for y in range(H) for x in range(W) if rng.random()<p]); cells=grid.free_cells()
    if not cells: continue
    s=rng.choice(cells)
    for k in range(2):
        J,visits,closed=run(grid,s,rng)
        for o,(d,par,to) in closed.items():
            for w in J.successor_dirs(o[0],o[1],d[0],d[1]):
                if w[0] and w[1]: continue
                # ray cells
                ray=[]; x,y=o
                while grid.legal(x,y,w[0],w[1]):
                    x+=w[0]; y+=w[1]; ray.append((x,y))
                    if J.has_forced(x,y,w[0],w[1]): break
                for e in perp(w):
                    for m,c in enumerate(ray):
                        z=(c[0]+e[0],c[1]+e[1])
                        if not grid.free(*z): break
                        if m==0: continue
                        if (not grid.free(z[0]-w[0]+e[0],z[1]-w[1]+e[1])) and grid.free(z[0]+e[0],z[1]+e[1]):
                            n+=1
                            dz=closed.get(z)
                            zw=(z[0]+w[0],z[1]+w[1])
                            key=('closed '+str(dz[0]) if dz else 'not closed')
                            if dz and w in J.successor_dirs(z[0],z[1],dz[0][0],dz[0][1]): key+=' [w in succ]'
                            cat[key]+=1
                            if grid.free(*zw):
                                dirs=frozenset(top for (oo,top,tt) in visits.get(zw,[]))
                                # normalise relative to (w,e): express each visiting top-level direction in (w,e) coordinates
                                rel=frozenset((v[0]*w[0]+v[1]*w[1], v[0]*e[0]+v[1]*e[1]) for v in dirs)
                                visdir[(key, 'zw visited' if dirs else 'zw UNVISITED', rel)]+=1
                            break   # only first break per strip
print('strip breaks analysed:',n)
for k,v in cat.most_common(): print(' ',k,v)
print('\nvisitors of z+w (top-level scan direction in (w,e) coordinates):')
for k,v in visdir.most_common(40): print(' ',k,v)
