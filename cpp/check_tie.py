"""Summarise results_tie/: cell-closing under tie rules log/fifo/lifo; counts runs, not-found, bound violations."""
import csv,glob,collections,re
R='/path/to/jps-wa/results_tie'; n=collections.Counter(); nf=collections.Counter(); bv=collections.Counter(); inst=set(); mr=0
for fn in glob.glob(R+'/*.csv'):
    m=re.search(r'/([^/.]+)\..*\.jps_cell\.(\w+)\.w([0-9.]+)\.csv$',fn); col,tie,w=m.groups()
    for r in csv.DictReader(open(fn)):
        if r['opt']=='inf': continue
        n[tie]+=1; inst.add((fn.split('.jps_cell')[0],r['id']))
        if r['found']!='1': nf[tie]+=1
        if r['bound_ok']!='1': bv[tie]+=1
        mr=max(mr,float(r['ratio']))
print('files',len(glob.glob(R+'/*.csv')),'runs',dict(n),'total',sum(n.values()),'notfound',dict(nf),'boundviol',dict(bv),'instances',len(inst),'maxratio',round(mr,3))
