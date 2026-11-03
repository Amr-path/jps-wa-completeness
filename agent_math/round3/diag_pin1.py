"""Diagnostics: for the 1x1 pinwheel (and the best climber instances) print the minimal-slack failing order with
per-pop (cell, arrival dir, g, h, f - fmin) so that the obstruction can be read off."""
import sys, math
sys.path.insert(0, '/home/claude/jps-wa/agent_math/round3')
from core import *
D = {(1, 0): 'E', (-1, 0): 'W', (0, 1): 'S', (0, -1): 'N', (1, 1): 'SE', (1, -1): 'NE', (-1, 1): 'SW', (-1, -1): 'NW', (0, 0): '0'}

def show(grid, s, t, w, cap=400_000):
    M = Model(grid, s)
    st, v, order = min_slack(grid, s, t, w, cap=cap, M=M)
    print(grid_to_str(grid, s, t)); print(f'w={w}: {st} slack={v}')
    if not order: return
    # replay to get g, parent, fmin at each pop
    gval = {s: 0.0}; parent = {s: None}; closed = set(); open_ = {s: 0.0}
    h = lambda c: octile(c[0], c[1], t[0], t[1])
    for x in order:
        fmin = min(gv + w * h(c) for c, gv in open_.items())
        gx = open_.pop(x); d = M.dir_from(x, parent[x]); closed.add(x)
        gap = gx + w * h(x) - fmin
        jps, vis = M.expand(x, d)
        rets = []
        for (j, c) in jps:
            tag = 'CLOSED-drop' if j in closed else ('worse-drop' if gx + c >= gval.get(j, math.inf) - 1e-12 else ('improve' if j in gval else 'new'))
            rets.append(f'{j}{tag}')
            if j in closed: continue
            if gx + c < gval.get(j, math.inf) - 1e-12:
                gval[j] = gx + c; parent[j] = x; open_[j] = gx + c
        print(f'  pop {x} arr={D[d]:2s} g={gx:6.2f} h={h(x):5.2f} gap={gap/ (w if w>100 else 1):6.3f}{"(h-units)" if w>100 else ""}  -> {rets}')

if __name__ == '__main__':
    g, c = pinwheel1(N=9)
    for w in (1.0, 1e6):
        show(g, (8, 8), c, w)
    # climber-5 best (w=3, slack 6.24)
    bl = [(0, 4), (0, 6), (0, 7), (1, 1), (1, 4), (1, 6), (2, 1), (3, 1), (4, 6), (6, 3), (6, 7), (7, 1), (7, 7)]
    show(Grid(8, 8, bl), (3, 0), (3, 4), 3.0)
