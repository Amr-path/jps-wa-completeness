import json, sys, time, resource
from myjps import Inst, exhaustive, replay
nm=sys.argv[1]; lim=int(sys.argv[2])
e={e['name']:e for e in json.load(open('/home/claude/jps-wa/agent_math/round3/logs_v2/climb_endpoints.json'))}[nm]
I=Inst(e['N'],e['bl'],e['s'],e['t'])
t0=time.time(); r=exhaustive(I,lim)
print(nm,'w',e['w'],r[0], r[1] if r[0]!='FAIL' else len(r[1]),'%.0fs'%(time.time()-t0),'maxrss MB',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss//1024,flush=True)
if r[0]=='FAIL': print(r[1]); print('replay',replay(Inst(e['N'],e['bl'],e['s'],e['t']),e['w'],r[1]))
