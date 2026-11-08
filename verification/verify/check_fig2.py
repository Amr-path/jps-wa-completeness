"""Figure 2 check: corner-cutting 5x5 instance. Replays adversary (JPScc on GridCC), prints the failing order
with the pushes at each step, and checks that the no-corner-cutting adversary finds no failing sequence."""
import sys
sys.path.insert(0, '/path/to/jps-wa/ref')
from jpswa import Grid, grid_to_str, CanonicalJPS
from dijps import GridCC, JPScc
from adversary import Adversary
from adversary_variants import VAdversary

rows = ["#.#..",
        ".#S..",
        ".....",
        "T..#.",
        "....."]
W = H = 5
blocked = [(x, y) for y in range(H) for x in range(W) if rows[y][x] == '#']
s = (2, 1); t = (0, 3)
gcc = GridCC(W, H, blocked)
A = VAdversary(gcc, s, t, JPScc)
ok, order = A.can_fail()
print('corner-cutting adversary can fail:', ok)
print('order:', order)
# replay that order step by step, print pushes
NAME = {(1,0):'right',(0,1):'down',(-1,0):'left',(0,-1):'up',(1,1):'down-right',(1,-1):'up-right',(-1,1):'down-left',(-1,-1):'up-left',(0,0):'start'}
if ok:
    closed = {}; open_ = {(s,(0,0))}
    for (x, d) in order:
        assert (x, d) in open_ and x not in closed
        closed[x] = d
        open_ = {e for e in open_ if e[0] != x}
        pushes = []
        for (y, e) in A.succ(x, d):
            if y not in closed:
                open_.add((y, e)); pushes.append(f'{y} {NAME[e]}')
        print(f'expand {x} ({NAME[d]}): scanned {[NAME[e] for e in A.J.successor_dirs(x[0],x[1],d[0],d[1])]} pushes {pushes}')
    print('open at end:', open_)
    # which scans from (1,2) reach t?
    for d in [(-1,1),(-1,0),(0,1),(1,1),(1,0),(0,-1),(-1,-1),(1,-1)]:
        print(' succ((1,2),%s) = %s' % (NAME[d], [NAME[e] for e in A.J.successor_dirs(1,2,d[0],d[1])]), ' rets:', [(y,NAME[e]) for y,e in A.succ((1,2),d)])
# enumerate ALL failing orders to see how many expansions / which cells
# no corner cutting rules on the same map
B = Adversary(Grid(W, H, blocked), s, t)
print('no-corner-cutting (canonical) adversary can fail:', B.can_fail())
# also: all failing orders for cc with the smallest length
import itertools
