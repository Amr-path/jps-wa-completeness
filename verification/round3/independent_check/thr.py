import json, math
from myjps import Inst
def thr_dfs(I,w,theta,EPS=1e-9):
    od0={I.s:(0.0,(0,0))}; seen={I.key(0,od0)}; st=[(0,od0)]
    while st:
        m,od=st.pop()
        fmin=min(I.f(w,c,g) for c,(g,d) in od.items())
        for x,(g,d) in list(od.items()):
            if I.f(w,x,g)-fmin>theta+EPS: continue
            nm,no,s=I.step(m,od,x)
            if s: continue
            if not no: return 'FAIL',len(seen)
            k=I.key(nm,no)
            if k in seen: continue
            seen.add(k); st.append((nm,no))
    return 'complete',len(seen)
if __name__=="__main__":
    E={e['name']:e for e in json.load(open('/path/to/jps-wa/verification/round3/logs_v2/climb_endpoints.json'))}
    for nm,v in [('climb3',1000006.1715728752),('climb6',1414226.9765866576)]:
        e=E[nm]; I=Inst(e['N'],e['bl'],e['s'],e['t'])
        print(nm,'theta=v-1e-6:',thr_dfs(I,e['w'],v-1e-6),' theta=v:',thr_dfs(I,e['w'],v),' theta=0:',thr_dfs(I,e['w'],0.0))
    pin=dict(N=9,s=[1,1],t=[4,4],bl=[[2,3],[5,2],[6,5],[3,6]])
    for w,v in [(1.0,8.000000000000002),(2.0,7.6568542494923815)]:
        I=Inst(pin['N'],pin['bl'],pin['s'],pin['t'])
        print('pinwheel',w,thr_dfs(I,w,v-1e-6),thr_dfs(I,w,v))
    