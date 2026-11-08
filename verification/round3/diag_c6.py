import sys; sys.path.insert(0,'/path/to/jps-wa/verification/round3')
from diag_pin1 import show
from core import *
g=Grid(8,8,[(0, 0), (0, 1), (1, 0), (1, 4), (1, 5), (3, 1), (4, 6), (6, 0), (6, 3), (6, 7), (7, 0), (7, 7)])
show(g,(0,2),(4,4),1e6)
