import math
from myjps import Inst, bottleneck, replay
from thr import thr_dfs
pin=dict(N=9,s=[1,1],t=[4,4],bl=[[2,3],[5,2],[6,5],[3,6]])
mk=lambda: Inst(pin['N'],pin['bl'],pin['s'],pin['t'])
for w in [1.0,1.1,1.2,1.5,2.0,3.0,5.0,10.0,100.0,1e6]:
    st,v,o=bottleneck(mk(),w); rb,_=replay(mk(),w,o)
    lo=thr_dfs(mk(),w,v-1e-6)[0]; at=thr_dfs(mk(),w,v)[0]; z=thr_dfs(mk(),w,0.0)
    print('w=%g slack %.6f replay %.6f  theta=v-1e-6:%s theta=v:%s  WA*(theta=0):%s states %d  slack-sqrt2w %.6f'%(w,v,rb,lo,at,z[0],z[1],v-math.sqrt(2)*w))
I=Inst(9,[(1,4),(2,3),(3,6),(5,2),(6,5),(6,6)],(8,8),(4,4))
st,v,o=bottleneck(I,1.0)
J=lambda: Inst(9,[(1,4),(2,3),(3,6),(5,2),(6,5),(6,6)],(8,8),(4,4))
print('climb_1 ev4: %.6f replay %.6f v-1e-6:%s v:%s WA*:%s'%(v,replay(J(),1.0,o)[0],thr_dfs(J(),1.0,v-1e-6)[0],thr_dfs(J(),1.0,v)[0],thr_dfs(J(),1.0,0.0)[0]))
