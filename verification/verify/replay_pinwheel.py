"""Independent replay of the 18-expansion run of Theorem 4.1 (pinwheel).
Own implementation of succ / Jump / forced sides following Section 2 of main.tex literally,
then cross-checked against ref/jpswa.py successor_dirs / jump.
Prints a table in the format of Table 2 and checks liveness of every popped entry.
"""
import sys, math
sys.path.insert(0, '/path/to/jps-wa/ref')
from jpswa import Grid, CanonicalJPS, SQ2, DIRS8

NAME = {(1,0):'E',(0,1):'S',(-1,0):'W',(0,-1):'N',(1,1):'SE',(1,-1):'NE',(-1,1):'SW',(-1,-1):'NW',(0,0):'start'}

W = H = 9
blocked = {(2,3),(5,2),(6,5),(3,6)}
s = (1,1); t = (4,4)

def free(c):
    x,y = c
    return 0 <= x < W and 0 <= y < H and c not in blocked

def legal(x, m):
    n = (x[0]+m[0], x[1]+m[1])
    if not free(n): return False
    if m[0] and m[1]:
        return free((x[0]+m[0], x[1])) and free((x[0], x[1]+m[1]))
    return True

def forced_sides(x, d):
    """straight d; return list of perpendicular unit vectors e with x-d+e blocked and x+e free"""
    out = []
    if d[0]:
        perps = [(0,1),(0,-1)]
    else:
        perps = [(1,0),(-1,0)]
    for e in perps:
        back = (x[0]-d[0]+e[0], x[1]-d[1]+e[1])
        side = (x[0]+e[0], x[1]+e[1])
        if not free(back) and free(side):
            out.append(e)
    return out

def succ(x, d):
    if d == (0,0): return list(DIRS8)
    a,b = d
    if a and b: return [(a,b),(a,0),(0,b)]
    out = [d]
    for e in forced_sides(x, d):
        out.append(e)
        out.append((a+e[0], b+e[1]))
    return out

def jump(x, e, visited, target=None):
    """returns (cell, cost) or None.  visited: set to record stepped-on cells"""
    cost = 0.0
    while True:
        if not legal(x, e): return None
        x = (x[0]+e[0], x[1]+e[1]); cost += SQ2 if (e[0] and e[1]) else 1.0
        visited.add(x)
        if target is not None and x == target: return (x, cost)
        if e[0] and e[1]:
            if jump(x, (e[0],0), visited, target) is not None or jump(x, (0,e[1]), visited, target) is not None:
                return (x, cost)
        else:
            if forced_sides(x, e): return (x, cost)

order = [(1,1),(2,2),(1,4),(2,5),(2,7),(4,7),(5,6),(4,5),(7,6),
         (7,4),(6,3),(5,4),(6,1),(7,2),(4,3),(3,2),(3,4),(4,1)]

# cross-check own succ/jump against the reference on all (cell, dir)
ref = CanonicalJPS(Grid(W,H,blocked), s, (-99,-99))
for x in [(i,j) for i in range(W) for j in range(H) if free((i,j))]:
    for d in DIRS8 + [(0,0)]:
        assert sorted(succ(x,d)) == sorted(ref.successor_dirs(x[0],x[1],d[0],d[1])), (x,d)
        for e in DIRS8:
            r1 = jump(x, e, set()); r2 = ref.jump(x[0],x[1],e[0],e[1],0.0)
            assert (r1 is None) == (r2 is None), (x,e)
            if r1: assert r1[0] == (r2[0],r2[1]) and abs(r1[1]-r2[2])<1e-9
print('own succ/jump agree with reference on all (cell,dir)')

# replay, Section 4 abstraction: pending entries (cell, dir, g); live iff cell unclosed and g == best g
entries = [(s,(0,0),0.0)]          # list of all pending entries ever created, not yet consumed
best = {s:0.0}
closed = {}
visited = {s}
rows = []
for k, x in enumerate(order):
    live = [e for e in entries if e[0] not in closed and abs(e[2]-best[e[0]])<1e-9]
    cands = [e for e in live if e[0]==x]
    assert cands, f'step {k}: {x} has no live entry'
    assert len({e[1] for e in cands})==1, f'step {k}: ambiguous live direction for {x}: {cands}'
    cell, d, g = cands[0]
    closed[x] = d
    entries = [e for e in entries if e[0] != x]
    dirs = succ(x, d)
    ret = []
    for e in dirs:
        r = jump(x, e, visited)
        if r is None: continue
        y, c = r
        gy = g + c
        if y in closed:
            ret.append(f'{y} {NAME[e]} dropped'); continue
        if gy < best.get(y, math.inf) - 1e-9:
            tag = f' (improves {best[y]:.3f})' if y in best else ''
            best[y] = gy; entries.append((y, e, gy)); ret.append(f'{y} {NAME[e]}{tag}')
        else:
            ret.append(f'{y} {NAME[e]} stale')
    rows.append((k, x, NAME[d], g, ','.join(NAME[e] for e in dirs), '; '.join(ret)))

for r in rows: print('%2d & %s & %s & %.3f & %s & %s' % r)
live = [e for e in entries if e[0] not in closed and abs(e[2]-best[e[0]])<1e-9]
print('live entries after run:', live)
print('pending (incl. stale/closed) after run:', entries)

# component
comp = {s}; dq=[s]
while dq:
    x = dq.pop()
    for m in DIRS8:
        if legal(x,m):
            n=(x[0]+m[0],x[1]+m[1])
            if n not in comp: comp.add(n); dq.append(n)
print('component size', len(comp), 'of free', 81-4, '; unvisited reachable:', sorted(comp-visited))
print('t visited?', t in visited)

# Mechanism checks
for cell, d in [((4,5),(1,0)),((5,4),(0,-1)),((4,3),(-1,0)),((3,4),(0,1))]:
    print(cell, NAME[d], 'forced sides', [NAME[e] for e in forced_sides(cell,d)], 'succ', [NAME[e] for e in succ(cell,d)])
# sweep arrivals: which executed scans (top-level) returned a neighbour of t with a direction towards t?
print('closed directions of the four neighbours:', {c:NAME[closed[c]] for c in [(4,5),(5,4),(4,3),(3,4)]})
print('closed (4,1):', NAME[closed[(4,1)]], ' closed cells in column 4:', {c:NAME[d] for c,d in closed.items() if c[0]==4})
# Mechanism sentence: "(2,3) with g=19.24 while (1,3) with g=1.41 live" -- check in the WA section
print('cells expanded with g>=19:', [(r[1],r[3]) for r in rows if r[3]>=19])
