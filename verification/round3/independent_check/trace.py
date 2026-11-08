from myjps import Inst, bottleneck, replay
pin=dict(N=9,s=[1,1],t=[4,4],bl=[[2,3],[5,2],[6,5],[3,6]])
I=Inst(pin['N'],pin['bl'],pin['s'],pin['t'])
o=[(1, 1), (2, 2), (1, 4), (2, 5), (6, 1), (2, 7), (4, 7), (5, 6), (4, 5), (5, 4), (6, 3), (4, 3), (3, 2), (3, 4), (7, 6), (7, 2), (7, 4), (4, 1)]
od={I.s:(0.0,(0,0))}; m=0
for x in o:
    g,d=od[x]; jps,vis=I.expand(x,d)
    print(x,'dir',d,'g %.3f'%g,'returns',[(y,e) for y,c,e in jps],'visits t' if I.t in vis else '')
    m,od,_=I.step(m,od,x)
# check table g-values
run=[(1,1),(2,2),(1,4),(2,5),(2,7),(4,7),(5,6),(4,5),(7,6),(7,4),(6,3),(5,4),(6,1),(7,2),(4,3),(3,2),(3,4),(4,1)]
od={I.s:(0.0,(0,0))}; m=0
print('--- table run')
for i,x in enumerate(run):
    g,d=od[x]; print(i,x,d,'%.3f'%g)
    m,od,_=I.step(m,od,x)
