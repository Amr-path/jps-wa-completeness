"""Independent (myjps.py only) threshold checks for the climb_2.log ev=483 instance (claimed exact slack
5.242640687119286 at w=2)."""
from myjps import Inst
from thr import thr_dfs
bl=[(0, 0), (0, 2), (0, 6), (0, 8), (1, 0), (2, 0), (2, 1), (2, 3), (2, 6), (3, 1), (3, 6), (3, 7), (4, 7), (5, 0), (5, 2), (6, 5), (6, 6), (6, 8), (7, 2), (7, 3), (8, 1), (8, 7)]
I=Inst(9,[list(b) for b in bl],[2,8],[4,4]); v=5.242640687119286
print('climb2_ev483 w=2 theta=v-1e-6:',thr_dfs(I,2.0,v-1e-6),' theta=v:',thr_dfs(I,2.0,v),' theta=0:',thr_dfs(I,2.0,0.0))
