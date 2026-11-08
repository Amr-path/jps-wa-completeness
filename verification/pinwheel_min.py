"""Robustness / minimality of the pinwheel counterexample: toggle single cells and re-run the targeted DFS.
Also try trimming the grid (removing an outer row/column)."""
import sys
sys.path.insert(0,'/path/to/jps-wa/ref')
from jpswa import Grid, grid_to_str
from common import Model
from pinwheel import build, targeted
g,s,hole,sh=build()
def test(grid, s):
    M=Model(grid,s); comp=M.component()
    if any(h not in comp for h in hole): return 'hole unreachable'
    res,cd=targeted(M,hole,limit=400000)
    return res
print('blocked cells whose removal keeps the failure:')
for b in sorted(g.blocked):
    g2=Grid(8,8,[c for c in g.blocked if c!=b]); print(' ',b, test(g2,s))
print('free cells whose blocking keeps the failure (s and hole excluded):')
keep=[]
for c in g.free_cells():
    if c==s or c in hole: continue
    g2=Grid(8,8,list(g.blocked)+[c]); r=test(g2,s)
    if r=='found': keep.append(c)
print(' ',keep)
# other start cells
print('start cells for which the failure exists:', [c for c in g.free_cells() if c not in hole and test(g,c)=='found'])
