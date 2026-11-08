import os, csv, math, collections, sys
def load(d, prio=False):
    S=collections.defaultdict(list)  # (set,alg,w[,pf]) -> rows
    ids=collections.defaultdict(set)
    for fn in os.listdir(d):
        if not fn.endswith('.csv'): continue
        parts=fn[:-4].split('.')
        st=parts[0]
        with open(os.path.join(d,fn)) as f:
            for r in csv.DictReader(f):
                key=(st,r['alg'],float(r['w'])) + ((parts[3],) if prio else ())
                S[key].append(r); ids[st].add((parts[1],int(r['id'])))
    return S, ids
def summ(S):
    tot=0; inf=0; viol=0; nf=0
    for k,rows in S.items():
        for r in rows:
            if r['opt'] in ('inf','nan') or math.isinf(float(r['opt'])): inf+=1; continue
            tot+=1
            if r['bound_ok']!='1': viol+=1
            if r['found']!='1': nf+=1
    return tot,inf,viol,nf
S,ids=load('/path/to/jps-wa/results')
print('full sweep: solvable runs, inf rows, viol, notfound', summ(S))
sets=['dao','da2','bg512','sc1','rooms','random','mazes']
ninst=set()
for (st,a,w),rows in S.items():
    if a=='jps_cell' and w==1:
        ninst |= {(st,r['id']) for r in rows if not math.isinf(float(r['opt']))} if False else set()
# solvable instances counts
cnt=collections.Counter()
for (st,a,w),rows in S.items():
    if a=='jps_cell' and w==1.0: cnt[st]+=sum(1 for r in rows if not math.isinf(float(r['opt'])))
print('solvable instances per set (jps_cell,w=1):',dict(cnt),'total',sum(cnt.values()))
def mean(xs): return sum(xs)/len(xs)
print('set w | exp cell state fls wa | scan(k) cell state fls | max ratio cell state fls wa | mean ratio')
for st in sets:
    for w in [1.0,1.5,2.0,3.0,5.0,10.0]:
        line=[st,w]
        E={};SC={};MX={};MN={}
        for a in ['jps_cell','jps_state','jps_fls','wastar']:
            rows=[r for r in S[(st,a,w)] if not math.isinf(float(r['opt']))]
            E[a]=mean([float(r['expanded']) for r in rows]); SC[a]=mean([float(r['scanned']) for r in rows])/1000
            MX[a]=max(float(r['ratio']) for r in rows); MN[a]=mean([float(r['ratio']) for r in rows])
        print(st,w,'| %.0f %.0f %.0f %.0f | %.1f %.1f %.1f %.1f | %.3f %.3f %.3f %.3f | %.4f %.4f %.4f %.4f | st/cell %.2f fls/cell %.3f scan st/cell %.2f'%(
            E['jps_cell'],E['jps_state'],E['jps_fls'],E['wastar'],SC['jps_cell'],SC['jps_state'],SC['jps_fls'],SC['wastar'],
            MX['jps_cell'],MX['jps_state'],MX['jps_fls'],MX['wastar'],MN['jps_cell'],MN['jps_state'],MN['jps_fls'],MN['wastar'],
            E['jps_state']/E['jps_cell'],E['jps_fls']/E['jps_cell'],SC['jps_state']/SC['jps_cell']))
T,_=load('/path/to/jps-wa/results_time')
print('timing:',summ(T))
cntT=collections.Counter()
for (st,a,w),rows in T.items():
    if a=='jps_cell' and w==1.0: cntT[st]+=sum(1 for r in rows if not math.isinf(float(r['opt'])))
print('timing instances',dict(cntT),sum(cntT.values()))
for st in sets:
    for w in [1.0,2.0,10.0]:
        M={a:mean([float(r['micros']) for r in T[(st,a,w)] if not math.isinf(float(r['opt']))])/1000 for a in ['jps_cell','jps_state','jps_fls','wastar']}
        print('time',st,w,' '.join('%.2f'%M[a] for a in ['jps_cell','jps_state','jps_fls','wastar']),
              'st/cell %.2f fls/cell %.2f wa/cell %.2f wa/state %.2f wa/fls %.2f'%(M['jps_state']/M['jps_cell'],M['jps_fls']/M['jps_cell'],M['wastar']/M['jps_cell'],M['wastar']/M['jps_state'],M['wastar']/M['jps_fls']))
P,_=load('/path/to/jps-wa/results_prio',prio=True)
print('prio:',summ(P))
cntP=collections.Counter(); keys=set()
for (st,a,w,pf),rows in P.items():
    keys.add((a,w,pf))
    if a=='jps_cell' and w==2.0 and pf=='xdp': cntP[st]+=sum(1 for r in rows if not math.isinf(float(r['opt'])))
print('prio instances',dict(cntP),sum(cntP.values()),'alg/w/pf combos',sorted(keys))
for st in sets:
  for w in [1.5,2.0,5.0,10.0]:
    out=[]
    for a in sorted({k[0] for k in keys}):
        for pf in ['xdp','xup']:
            rows=[r for r in P[(st,a,w,pf)] if not math.isinf(float(r['opt']))]
            out.append('%s/%s %.4f'%(a,pf,mean([float(r['ratio']) for r in rows])))
    wa=[ '%s %.4f'%(a,mean([float(r['ratio']) for r in S[(st,a,w)] if not math.isinf(float(r['opt']))])) for a in ['jps_cell','jps_state','wastar']]
    print('prio',st,w,' '.join(out),'| WA*:',' '.join(wa))
