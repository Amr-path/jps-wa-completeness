"""Computational test of Lemma 4.3 (frontier edges lie on strips) and Proposition 4.2.
Instances: pinwheel family with random extra obstacles and random start (the only known source of terminal
configurations with unvisited reachable cells); failing orders found with core.min_slack at random w.
For each failing order we replay (own replay recording every executed scan, top-level and sub-jump) and check,
for every frontier edge (p visited, c=p+u free & unvisited, u straight), that one of the two alternatives holds.
"""
import sys, math, random
sys.path.insert(0, '/home/claude/jps-wa/agent_math/round3')
from core import Model, min_slack, pinwheel1, Grid, SQ2, DIRS8, CanonicalJPS

def replay_scans(grid, s, order):
    J = CanonicalJPS(grid, s, (-99,-99))
    scans = []   # dict(cells=[y0..yk], dir, kind, forced_end(bool))
    visited = {s}
    def jump(x, e, kind):
        cells = [x]; cur = x
        while True:
            if not grid.legal(cur[0], cur[1], e[0], e[1]):
                scans.append(dict(cells=cells, dir=e, kind=kind, forced=False)); return None
            cur = (cur[0]+e[0], cur[1]+e[1]); cells.append(cur); visited.add(cur)
            if e[0] and e[1]:
                if jump(cur, (e[0],0), 'sub') is not None or jump(cur, (0,e[1]), 'sub') is not None:
                    scans.append(dict(cells=cells, dir=e, kind=kind, forced=True)); return cur
            else:
                if J.has_forced(cur[0], cur[1], e[0], e[1]):
                    scans.append(dict(cells=cells, dir=e, kind=kind, forced=True)); return cur
    closed = {}; gval = {s: 0.0}; parent = {s: None}
    for x in order:
        p = parent[x]; d = (0,0) if p is None else ((x[0]>p[0])-(x[0]<p[0]), (x[1]>p[1])-(x[1]<p[1]))
        assert x not in closed
        closed[x] = d
        for e in J.successor_dirs(x[0], x[1], d[0], d[1]):
            r = jump(x, e, 'top')
            if r is None or r in closed: continue
            c = sum(SQ2 if (e[0] and e[1]) else 1.0 for _ in range(max(abs(r[0]-x[0]), abs(r[1]-x[1]))))
            if gval[x] + c < gval.get(r, math.inf) - 1e-12:
                gval[r] = gval[x] + c; parent[r] = x
    # terminal check: no pending unclosed cell
    pending = [c for c in gval if c not in closed]
    return visited, closed, scans, pending

def check_lemma(grid, s, visited, closed, scans):
    comp = Model(grid, s).component()
    assert visited <= comp
    bad = []
    unvis = comp - visited
    # Proposition 4.2: unvisited nonempty => visited not closed under straight moves
    if unvis:
        assert any(grid.legal(p[0],p[1],u[0],u[1]) and (p[0]+u[0],p[1]+u[1]) in unvis
                   for p in visited for u in [(1,0),(-1,0),(0,1),(0,-1)])
    for p in visited:
        for u in [(1,0),(-1,0),(0,1),(0,-1)]:
            c = (p[0]+u[0], p[1]+u[1])
            if not grid.free(*c) or c in visited: continue
            alt1 = False
            for sc in scans:
                w = sc['dir']
                if w[0] and w[1]: continue
                if w[0]*u[0] + w[1]*u[1] != 0: continue      # need w perpendicular to u
                if p not in sc['cells']: continue
                i = sc['cells'].index(p)
                if all(grid.free(y[0]+u[0], y[1]+u[1]) for y in sc['cells'][:i+1]):
                    alt1 = True; break
            alt2 = (p not in closed) and any(sc['kind']=='sub' and sc['forced'] and sc['cells'][-1]==p for sc in scans)
            if not (alt1 or alt2):
                bad.append((p, u, c))
    return unvis, bad

if __name__ == '__main__':
  rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
  ninst = int(sys.argv[2]) if len(sys.argv) > 2 else 60
  tested = edges = 0
  for it in range(ninst):
      N = rng.choice((7, 8, 9, 10))
      centre = (rng.randrange(2, N-2), rng.randrange(2, N-2))
      extra = {(rng.randrange(N), rng.randrange(N)) for _ in range(rng.randrange(0, 7))}
      g, t = pinwheel1(N=N, centre=centre, extra=extra)
      if not g.free(*t): continue
      frees = g.free_cells()
      s = rng.choice([c for c in frees if c != t])
      if t not in Model(g, s).component(): continue
      w = rng.choice((1.0, 1.5, 2.0, 5.0, 1e6))
      st, v, order = min_slack(g, s, t, w, cap=60_000)
      if st != 'FAIL': continue
      visited, closed, scans, pending = replay_scans(g, s, order)
      assert not pending, pending
      unvis, bad = check_lemma(g, s, visited, closed, scans)
      assert t in unvis
      tested += 1
      nedges = sum(1 for p in visited for u in [(1,0),(-1,0),(0,1),(0,-1)]
                   if g.free(p[0]+u[0], p[1]+u[1]) and (p[0]+u[0], p[1]+u[1]) in unvis)
      edges += nedges
      if bad:
          print('LEMMA VIOLATION', N, centre, sorted(g.blocked), s, order, bad)
  print(f'terminal configurations with unvisited cells tested: {tested}, frontier edges checked: {edges}')
