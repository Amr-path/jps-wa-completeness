"""Shared helpers: scans, exhaustive state enumeration over all expansion orders (no target)."""
import sys, random
sys.path.insert(0, '/path/to/jps-wa/ref')
from jpswa import Grid, CanonicalJPS, DIRS8, grid_to_str
from collections import deque

STRAIGHT = [(1,0),(-1,0),(0,1),(0,-1)]

class Model:
    def __init__(self, grid, s):
        self.g = grid; self.s = s
        self.J = CanonicalJPS(grid, s, (-99,-99), 1.0, 'hig')
        self._scan = {}; self._jp = {}
    def succ_dirs(self, x, d):
        return self.J.successor_dirs(x[0], x[1], d[0], d[1])
    def jump(self, x, e):
        """returns (returned cell or None, visited set)"""
        key = (x, e)
        if key in self._jp: return self._jp[key]
        vis = set(); g = self.g
        def jr(x0,y0,dx,dy):
            while True:
                if not g.legal(x0,y0,dx,dy): return None
                x0+=dx; y0+=dy; vis.add((x0,y0))
                if dx and dy:
                    if jr(x0,y0,dx,0) is not None or jr(x0,y0,0,dy) is not None: return (x0,y0)
                else:
                    if self.J.has_forced(x0,y0,dx,dy): return (x0,y0)
        r = jr(x[0],x[1],e[0],e[1])
        self._jp[key] = (r, frozenset(vis))
        return self._jp[key]
    def scan(self, x, d):
        """full expansion of state (x,d): (list of (jp, e)), visited set"""
        key = (x,d)
        if key in self._scan: return self._scan[key]
        out = []; vis = set()
        for e in self.succ_dirs(x, d):
            r, v = self.jump(x, e); vis |= v
            if r is not None: out.append((r, e))
        self._scan[key] = (tuple(out), frozenset(vis))
        return self._scan[key]
    def component(self):
        seen={self.s}; dq=deque([self.s]); g=self.g
        while dq:
            x,y=dq.popleft()
            for dx,dy in DIRS8:
                if g.legal(x,y,dx,dy):
                    n=(x+dx,y+dy)
                    if n not in seen: seen.add(n); dq.append(n)
        return seen

def enumerate_states(M, limit=300000):
    """DFS over all reachable (closed, open) states. Yields (closed: dict cell->dir, open: frozenset, V: frozenset)."""
    start = (frozenset(), frozenset({(M.s,(0,0))}))
    seen=set(); stack=[start]; n=0
    while stack:
        st = stack.pop()
        if st in seen: continue
        seen.add(st); n+=1
        if n>limit: return
        closed, open_ = st
        cd = dict(closed)
        V = {M.s}
        for x,d in closed: V |= M.scan(x,d)[1]
        yield cd, open_, frozenset(V)
        closed_cells = set(cd)
        pend = [(x,d) for (x,d) in open_ if x not in closed_cells]
        for (x,d) in pend:
            nc = closed | {(x,d)}
            no = set(e for e in open_ if e[0]!=x)
            for (y,e) in M.scan(x,d)[0]:
                if y not in closed_cells: no.add((y,e))
            stack.append((nc, frozenset(no)))

def random_grid(rng, W, H, p):
    return Grid(W, H, [(x,y) for y in range(H) for x in range(W) if rng.random()<p])

def frontier_edges(M, V):
    g=M.g; out=[]
    for (x,y) in V:
        for (dx,dy) in STRAIGHT:
            if g.free(x+dx,y+dy) and (x+dx,y+dy) not in V: out.append(((x,y),(x+dx,y+dy)))
    return out

def closure(M, pend, closed_cells, K):
    """cells covered by depth<=K closure of pending states through unclosed cells"""
    cov=set(); frontier=set(pend); seen=set()
    for depth in range(K):
        nxt=set()
        for st in frontier:
            if st in seen: continue
            seen.add(st); jps,vis=M.scan(*st); cov|=vis
            for (y,e) in jps:
                if y not in closed_cells: nxt.add((y,e))
        frontier=nxt
    return cov
