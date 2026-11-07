"""Parse FLIRTLib CARMEN-style logs: VERTEX2 (corrected poses) + ROBOTLASER1 (scans), paired by order."""
import numpy as np
def parse(fn):
    V={}; scans=[]
    for line in open(fn):
        t=line.split()
        if not t: continue
        if t[0]=='VERTEX2': V[int(t[1])]=tuple(map(float,t[2:5]))
        elif t[0]=='ROBOTLASER1':
            start=float(t[2]); fov=float(t[3]); res=float(t[4]); mx=float(t[5]); n=int(t[8])
            r=np.array(t[9:9+n],float)
            ang=start+res*np.arange(n)
            scans.append((ang,r,mx))
    poses=np.array([V[i] for i in range(len(V))])
    assert len(poses)==len(scans), (len(poses),len(scans))
    return poses, scans
