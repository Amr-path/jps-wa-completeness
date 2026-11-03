# cross-check my successor function against core.Model.expand on all (cell,dir) for the 6 endpoints + pinwheel
import sys, json
sys.path.insert(0,'/home/claude/jps-wa/agent_math/round3')
from core import Model, Grid
from myjps import Inst, D8
eps=json.load(open('/home/claude/jps-wa/agent_math/round3/logs_v2/climb_endpoints.json'))
eps.append(dict(name='pinwheel',w=1,N=9,s=[1,1],t=[4,4],bl=[[2,3],[5,2],[6,5],[3,6]]))
for e in eps:
    I=Inst(e['N'],e['bl'],e['s'],e['t']); G=Grid(e['N'],e['N'],[tuple(b) for b in e['bl']]); M=Model(G,tuple(e['s']))
    t=tuple(e['t']); bad=0; n=0
    for x in range(e['N']):
        for y in range(e['N']):
            if not I.free(x,y): continue
            for d in D8+[(0,0)]:
                mine,mv=I.expand((x,y),d)
                ref,rv=M.expand((x,y),d,t)
                a=sorted((c,round(g,9)) for c,g,_ in mine); b=sorted((c,round(g,9)) for c,g in ref)
                n+=1
                if a!=b or mv!=rv: bad+=1
    print(e['name'],'pairs',n,'mismatches',bad)
