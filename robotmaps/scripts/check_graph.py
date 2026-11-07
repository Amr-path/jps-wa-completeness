import sys, math
import numpy as np
def wrap(a): return (a+math.pi)%(2*math.pi)-math.pi
for fn in sys.argv[1:]:
    V={}; E=[]; seq=True; L=[]
    for line in open(fn):
        if line.startswith('#LOOP'): seq=False
        t=line.split()
        if not t: continue
        if t[0]=='VERTEX2': V[int(t[1])]=tuple(map(float,t[2:5]))
        elif t[0]=='EDGE2': E.append((int(t[1]),int(t[2]),float(t[3]),float(t[4]),float(t[5]), seq))
    res={True:[],False:[]}
    for i,j,dx,dy,dt,s in E:
        xi,yi,ti=V[i]; xj,yj,tj=V[j]
        c,s_=math.cos(ti),math.sin(ti)
        ex=c*(xj-xi)+s_*(yj-yi)-dx; ey=-s_*(xj-xi)+c*(yj-yi)-dy; et=wrap(tj-ti-dt)
        res[s].append((math.hypot(ex,ey),abs(et)))
    for k,name in ((True,'seq'),(False,'loop')):
        a=np.array(res[k]) if res[k] else np.zeros((1,2))
        print(fn.split('/')[-1],name,len(res[k]),'median trans %.3f max %.3f | median rot %.3f max %.3f'%(np.median(a[:,0]),a[:,0].max(),np.median(a[:,1]),a[:,1].max()))
