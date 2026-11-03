"""Test of the direct proof of Lemma 4.1 (J contains a C*-path).
(A) the move-level canonical graph G_c (states (x,d), arcs (x,d)->(x+e,e) for e in succ(x,d), legal move)
    contains, for every reachable t, a path from (s,0) to a state of t of cost dist(s,t);
(B) the state graph J (jump arcs) contains such a path (Dijkstra on J).
usage: python3 lemma_jpath_test.py SEED NMAPS"""
import sys, math, heapq, random
sys.path.insert(0, '/home/claude/jps-wa/ref')
from jpswa import Grid, CanonicalJPS, DIRS8, SQ2

def all_dist(g, s):
    dist = {s: 0.0}; pq = [(0.0, s)]
    while pq:
        d, (x, y) = heapq.heappop(pq)
        if d > dist[(x, y)] + 1e-12: continue
        for dx, dy in DIRS8:
            if g.legal(x, y, dx, dy):
                n = (x + dx, y + dy); nd = d + (SQ2 if dx and dy else 1.0)
                if nd < dist.get(n, math.inf) - 1e-12: dist[n] = nd; heapq.heappush(pq, (nd, n))
    return dist

def gc_dist(g, s):
    J = CanonicalJPS(g, s, None)
    best = {}; st0 = (s, (0, 0)); dist = {st0: 0.0}; pq = [(0.0, st0)]
    while pq:
        d, st = heapq.heappop(pq)
        if d > dist[st] + 1e-12: continue
        (x, y), (a, b) = st
        best[(x, y)] = min(best.get((x, y), math.inf), d)
        for e in J.successor_dirs(x, y, a, b):
            if g.legal(x, y, *e):
                n = ((x + e[0], y + e[1]), e); nd = d + (SQ2 if e[0] and e[1] else 1.0)
                if nd < dist.get(n, math.inf) - 1e-12: dist[n] = nd; heapq.heappush(pq, (nd, n))
    return best

def j_dist(g, s, t):
    J = CanonicalJPS(g, s, t); st0 = (s, (0, 0)); dist = {st0: 0.0}; pq = [(0.0, st0)]
    while pq:
        d, st = heapq.heappop(pq)
        if d > dist[st] + 1e-12: continue
        (x, y), (a, b) = st
        if (x, y) == t: return d
        for e in J.successor_dirs(x, y, a, b):
            r = J.jump(x, y, e[0], e[1], d)
            if r is None: continue
            n = ((r[0], r[1]), e); nd = r[2]
            if nd < dist.get(n, math.inf) - 1e-12: dist[n] = nd; heapq.heappush(pq, (nd, n))
    return math.inf

seed, nmaps = int(sys.argv[1]), int(sys.argv[2]); rng = random.Random(seed)
na = nb = bad = 0
for k in range(nmaps):
    W, H = rng.randint(3, 14), rng.randint(3, 14); p = rng.uniform(0.0, 0.5)
    g = Grid(W, H, [(x, y) for x in range(W) for y in range(H) if rng.random() < p])
    fr = g.free_cells()
    if len(fr) < 2: continue
    for s in rng.sample(fr, min(4, len(fr))):
        D = all_dist(g, s); C = gc_dist(g, s)
        for t, dt in D.items():
            if t == s: continue
            na += 1
            if abs(C.get(t, math.inf) - dt) > 1e-9: bad += 1; print('A FAIL', W, H, sorted(g.blocked), s, t, dt, C.get(t))
        for t in rng.sample([t for t in D if t != s], min(6, len(D) - 1)):
            nb += 1; v = j_dist(g, s, t)
            if abs(v - D[t]) > 1e-9: bad += 1; print('B FAIL', W, H, sorted(g.blocked), s, t, D[t], v)
print(f'DONE seed={seed} maps={nmaps} A-pairs={na} B-pairs={nb} failures={bad}')
