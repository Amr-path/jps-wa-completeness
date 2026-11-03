"""Greedy minimisation under the FAITHFUL model (g-values, parent = best-g generator)."""
import sys
sys.path.insert(0,'/home/claude/jps-wa/ref')
from jpswa import Grid, grid_to_str
from common import Model
from pinwheel import build
from pinwheel_verify import faithful_dfs
g,s,hole,sh=build()
def ok(bl, s0):
    G=Grid(8,8,list(bl)); M=Model(G,s0); comp=M.component()
    if any(h not in comp for h in hole) or s0 not in comp: return False
    return faithful_dfs(G,s0,hole,limit=600000)[0]=='found'
bl=set(g.blocked); changed=True
while changed:
    changed=False
    for b in sorted(bl):
        if ok(bl-{b}, s): bl.discard(b); changed=True; print('removed',b); sys.stdout.flush()
print('minimal blocked set (greedy, faithful model, s fixed):', sorted(bl)); print(grid_to_str(Grid(8,8,list(bl)),s,None,hole))
