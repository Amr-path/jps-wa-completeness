import json, sys, time, resource, struct
from myjps import Inst
nm=sys.argv[1]; lim=int(sys.argv[2])
e={e['name']:e for e in json.load(open('/path/to/jps-wa/verification/round3/logs_v2/climb_endpoints.json'))}[nm]
I=Inst(e['N'],e['bl'],e['s'],e['t'])
DI={d:i for i,d in enumerate([(0,0),(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)])}
def key(mask,od):
    return mask.to_bytes(11,'little')+b''.join(struct.pack('<BIB',a,g,d) for a,g,d in sorted((I.idx(c),round(g*1e6),DI[d]) for c,(g,d) in od.items()))
t0=time.time()
od0={I.s:(0.0,(0,0))}; seen={key(0,od0)}; stack=[(0,od0)]; res='complete'
while stack:
    mask,od=stack.pop()
    for x in list(od):
        nm2,no,succ=I.step(mask,od,x)
        if succ: continue
        if not no: res='FAIL'; stack=[]; break
        k=key(nm2,no)
        if k in seen: continue
        seen.add(k)
        if len(seen)>lim: res='limit'; stack=[]; break
        stack.append((nm2,no))
print(nm,'w',e['w'],res,len(seen),'%.0fs'%(time.time()-t0),'maxrss MB',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss//1024,flush=True)
