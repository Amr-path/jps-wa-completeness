import json, time, math
from myjps import Inst, bottleneck, replay, exhaustive
eps={e['name']:e for e in json.load(open('/path/to/jps-wa/verification/round3/logs_v2/climb_endpoints.json'))}
pin=dict(N=9,s=[1,1],t=[4,4],bl=[[2,3],[5,2],[6,5],[3,6]])
run=[(1,1),(2,2),(1,4),(2,5),(2,7),(4,7),(5,6),(4,5),(7,6),(7,4),(6,3),(5,4),(6,1),(7,2),(4,3),(3,2),(3,4),(4,1)]
I=Inst(pin['N'],pin['bl'],pin['s'],pin['t'])
b,vt=replay(I,1.0,run); print('table run: slack w=1',b,'t visited',vt)
# table check: g values / directions
for w in [1.0,1.1,1.2,1.5,2.0,3.0,5.0,10.0,100.0,1e6]:
    t0=time.time(); st,v,o=bottleneck(Inst(pin['N'],pin['bl'],pin['s'],pin['t']),w)
    I2=Inst(pin['N'],pin['bl'],pin['s'],pin['t'])
    rb,vt=replay(I2,w,o) if o else (None,None)
    print('pinwheel w',w,st,v,'replay',rb,'t visited',vt,'len',len(o) if o else None,'%.0fs'%(time.time()-t0))
    if w in (1.0,2.0): print('   order',o)
for nm in ['climb3','climb6']:
    e=eps[nm]; I=Inst(e['N'],e['bl'],e['s'],e['t']); w=e['w']
    t0=time.time(); st,v,o=bottleneck(I,w)
    rb,vt=replay(Inst(e['N'],e['bl'],e['s'],e['t']),w,o)
    print(nm,'w',w,st,repr(v),'v-w',v-w,'v-sqrt2 w',v-math.sqrt(2)*w,'replay',rb,'len',len(o),'t visited',vt,'%.0fs'%(time.time()-t0))
    print('   order',o)
