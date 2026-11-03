"""Greedy minimisation on the 8x8 grid: unblock cells while the targeted adversary still finds a failing order;
then try to add blocked outer cells (to shrink) while it persists."""
import sys
sys.path.insert(0,'/home/claude/jps-wa/ref')
from jpswa import Grid, grid_to_str
from common import Model
from pinwheel import build, targeted
g,s,hole,sh=build()
def ok(bl, s0):
    G=Grid(8,8,list(bl)); M=Model(G,s0); comp=M.component()
    if any(h not in comp for h in hole) or s0 not in comp: return False
    return targeted(M,hole,limit=400000)[0]=='found'
bl=set(g.blocked); changed=True
while changed:
    changed=False
    for b in sorted(bl):
        if ok(bl-{b}, s): bl.discard(b); changed=True
print('minimal blocked set (greedy, s fixed):', sorted(bl)); print(grid_to_str(Grid(8,8,list(bl)),s,None,hole))
# now shrink: block outer cells greedily, rows/cols at a time
bl2=set(bl)
for line in [[(x,0) for x in range(8)],[(x,7) for x in range(8)],[(0,y) for y in range(8)],[(7,y) for y in range(8)]]:
    cand=bl2|set(c for c in line if c!=s)
    if ok(cand,s): bl2=cand; print('blocked line', line[0], line[-1])
print(grid_to_str(Grid(8,8,list(bl2)),s,None,hole))
