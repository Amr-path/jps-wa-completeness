"""Canonical JPS with STATE-indexed closing ((cell, arrival-direction) pairs) + WA* ordering, no re-expansion.
Also variants of canonical JPS with CELL closing for the adversary: corner cutting (JPScc), bounded jumps (BJPS)."""
import heapq, itertools, math
from jpswa import Grid, octile, SQ2, DIRS8, CanonicalJPS

class DIJPS(CanonicalJPS):
    """closing keyed by (cell, direction)."""
    def search(self):
        s,t,w=self.s,self.t,self.w
        gval={(s,(0,0)):0.0}; parent={}; closed=set(); counter=itertools.count(); open_=[]
        def push(st,gc):
            f=gc+w*octile(st[0][0],st[0][1],t[0],t[1]); heapq.heappush(open_,((f,-gc,next(counter)),st,gc)); self.generated+=1
        push((s,(0,0)),0.0); expansions_per_cell={}
        while open_:
            _,st,gn=heapq.heappop(open_)
            if st in closed or gn>gval[st]+1e-12: continue
            closed.add(st); self.expanded+=1; x,d=st
            expansions_per_cell[x]=expansions_per_cell.get(x,0)+1
            if x==t: self.maxexp=max(expansions_per_cell.values()); return gn,None
            for e in self.successor_dirs(x[0],x[1],d[0],d[1]):
                r=self.jump(x[0],x[1],e[0],e[1],gn)
                if r is None: continue
                j=((r[0],r[1]),e)
                if j in closed: continue
                if r[2]<gval.get(j,math.inf)-1e-12: gval[j]=r[2]; push(j,r[2])
        self.maxexp=max(expansions_per_cell.values()) if expansions_per_cell else 0
        return math.inf,None

class GridCC(Grid):
    """corner cutting allowed: diagonal legal iff destination free."""
    def legal(self,x,y,dx,dy): return self.free(x+dx,y+dy)

class BoundedJPS(CanonicalJPS):
    """bounded jump length: a top-level/sub jump stops and returns after b steps (Sturtevant & Rabin 2016 style)."""
    def __init__(self,*a,b=3,**k): super().__init__(*a,**k); self.b=b
    def jump(self,x,y,dx,dy,gg):
        g=self.g; steps=0
        while True:
            if not g.legal(x,y,dx,dy): return None
            x+=dx;y+=dy;gg+=SQ2 if (dx and dy) else 1.0; steps+=1; self.scanned+=1
            if (x,y)==self.t: return (x,y,gg)
            if dx and dy:
                if self.jump(x,y,dx,0,gg) is not None or self.jump(x,y,0,dy,gg) is not None: return (x,y,gg)
            else:
                if self.has_forced(x,y,dx,dy): return (x,y,gg)
            if steps>=self.b: return (x,y,gg)

class JPScc(CanonicalJPS):
    """Harabor & Grastien 2011 JPS with corner cutting (use with GridCC)."""
    def successor_dirs(self,x,y,dx,dy):
        g=self.g
        if dx==0 and dy==0: return list(DIRS8)
        if dx and dy:
            out=[(dx,dy),(dx,0),(0,dy)]
            if not g.free(x-dx,y) and g.free(x-dx,y+dy): out.append((-dx,dy))
            if not g.free(x,y-dy) and g.free(x+dx,y-dy): out.append((dx,-dy))
            return out
        out=[(dx,dy)]
        if dx:
            for e in (1,-1):
                if not g.free(x,y+e) and g.free(x+dx,y+e): out.append((dx,e))
        else:
            for e in (1,-1):
                if not g.free(x+e,y) and g.free(x+e,y+dy): out.append((e,dy))
        return out
    def has_forced(self,x,y,dx,dy):
        g=self.g
        if dx and dy:
            return (not g.free(x-dx,y) and g.free(x-dx,y+dy)) or (not g.free(x,y-dy) and g.free(x+dx,y-dy))
        if dx: return any(not g.free(x,y+e) and g.free(x+dx,y+e) for e in (1,-1))
        return any(not g.free(x+e,y) and g.free(x+e,y+dy) for e in (1,-1))
    def jump(self,x,y,dx,dy,gg):
        g=self.g
        while True:
            if not g.legal(x,y,dx,dy): return None
            x+=dx;y+=dy;gg+=SQ2 if (dx and dy) else 1.0; self.scanned+=1
            if (x,y)==self.t: return (x,y,gg)
            if self.has_forced(x,y,dx,dy): return (x,y,gg)
            if dx and dy:
                if self.jump(x,y,dx,0,gg) is not None or self.jump(x,y,0,dy,gg) is not None: return (x,y,gg)
