import os,csv,math,collections
def rd(d,prio):
    R={}
    for fn in os.listdir(d):
        if not fn.endswith('.csv'): continue
        p=fn[:-4].split('.'); st,sc=p[0],p[1]; pf=p[3] if prio else 'wa'
        for r in csv.DictReader(open(os.path.join(d,fn))):
            if math.isinf(float(r['opt'])): continue
            R[(st,sc,int(r['id']),r['alg'],float(r['w']),pf)]=float(r['ratio'])
    return R
P=rd('/path/to/jps-wa/results_prio',True); W=rd('/path/to/jps-wa/results',False)
agg=collections.defaultdict(list)
for (st,sc,i,a,w,pf),v in P.items():
    k=(st,sc,i,a,w,'wa')
    if k not in W: continue
    agg[(st,a,w,pf)].append(v); agg[(st,a,w,'wa_'+pf)].append(W[k])
bad=[]
for st in ['dao','da2','bg512','sc1','rooms','random','mazes']:
  for w in [1.5,2.0,5.0,10.0]:
    for a in ['jps_cell','jps_state','wastar']:
        m=lambda k: sum(agg[k])/len(agg[k])
        xd,xu,wa=m((st,a,w,'xdp')),m((st,a,w,'xup')),m((st,a,w,'wa_xdp'))
        tag=''
        if not (xd<=wa+1e-12): tag+=' XDP>=WA*'
        if not (xu>=wa-1e-12): tag+=' XUP<=WA*'
        if tag: bad.append((st,w,a,round(xd,4),round(wa,4),round(xu,4),tag))
print(len(bad),'exceptions (same-instance comparison)'); [print(b) for b in bad]
