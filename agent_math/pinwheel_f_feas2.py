"""Same as pinwheel_f_feas.py but arm length L is a parameter (4-fold symmetric pinwheel, 2x2 hole)."""
import math
SQ2=math.sqrt(2)
def oct(a,b):
    dx,dy=abs(a[0]-b[0]),abs(a[1]-b[1]); return max(dx,dy)+(SQ2-1)*min(dx,dy)
def L1(a,b): return abs(a[0]-b[0])+abs(a[1]-b[1])
def rot(c): return (c[1]+1, 2-c[0])
def orb(c):
    out=[c]
    for _ in range(3): c=rot(c); out.append(c)
    return out
hole=[(1,0),(2,0),(1,1),(2,1)]
for L in range(4,16):
    o1=(0,L); h1=(1,L-1); B0=(0,0)
    o=orb(o1); h=orb(h1); B=orb(B0)           # o[k]=o_{1+k}, etc.  arm index: ray from o[k] ends at B[k]; strip blocker of that ray's strip is B[k+1]?? 
    # Convention check: ray from o1=(0,L) goes S to B0=(0,0). Its strip blocker is B1=(1,2)=rot(B0)=B[1]. host of that strip is h1=h[0].
    # So for ray k (origin o[k], host h[k]): end cell = B[k], blocker on its strip = B[k+1], whose ring arrival comes from ray k+1 (origin o[k+1]).
    best=None
    for w in (1.0,1.05,1.1,1.2,1.5,2.0,3.0):
        res=[]
        for t in hole:
            Us=[]
            for k in range(4):
                j=(k+1)%4; Bk=B[j]        # blocker on ray k's strip
                # mode B: f(o_j) <= f(h_k); f_ring(Bk) <= f(h_k)   (ring arrival of Bk from o_j, ray length L1(o_j,Bk))
                cB=min(SQ2+w*oct(h[k],t)-w*oct(o[j],t), SQ2+w*oct(h[k],t)-L1(o[j],Bk)-w*oct(Bk,t))
                # mode A: sweep arrival first: f_sweep(Bk)>=f(o_j); g_ring<g_sweep; f_ring<=f(h_k)
                sw=SQ2+L1(h[k],Bk)
                cA=min(sw+w*oct(Bk,t)-w*oct(o[j],t), sw-L1(o[j],Bk)-1e-9, SQ2+w*oct(h[k],t)-L1(o[j],Bk)-w*oct(Bk,t))
                Us.append(max(cB,cA))
            res.append((sum(Us),t,Us))
        s,t,Us=max(res)
        print(f'L={L:2d} w={w:4}: best t={t} U={["%.2f"%u for u in Us]} sum={s:.2f} {"FEASIBLE" if s>=-1e-9 else ""}')
