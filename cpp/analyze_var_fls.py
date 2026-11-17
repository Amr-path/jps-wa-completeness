"""Paired comparison on the failing variants (results_var): per variant and weight, instances on which all three of
cell-closing, state-closing and FLS have a row; failures of each; and, on instances solved by all three, mean
expansions and mean cost ratio. Also the per-collection FLS/state expansion ratio range."""
import csv, glob, re, sys
from collections import defaultdict
sys.path.insert(0, '/path/to/jps-wa/cpp')
from analyze_extra import within
ROOT = '/path/to/jps-wa'; A = ('jps_cell', 'jps_state', 'jps_fls')
R = defaultdict(dict)
for fn in glob.glob(ROOT + '/results_var/*.csv'):
    m = re.search(r'/([^/.]+)\.(.*)\.(bjps8|cc)\.(jps_cell|jps_state|jps_fls)\.w([0-9.]+)\.csv$', fn)
    c, mp, v, a, w = m.groups()
    for r in csv.DictReader(open(fn)):
        if r['opt_a'] == '-1': continue
        ok = r['found'] == '1' and r['bound_ok'] == '1' and within(r, w)
        R[(v, w, c, mp, r['id'])][a] = (ok, int(r['expanded']), float(r['cost']) / float(r['opt']) if r['found'] == '1' else None)
for v in ('bjps8', 'cc'):
    for w in ('1.2', '2', '4', '8'):
        ks = [k for k in R if k[0] == v and k[1] == w and len(R[k]) == 3]
        fail = {a: sum(1 for k in ks if not R[k][a][0]) for a in A}
        both = [k for k in ks if all(R[k][a][0] for a in A)]
        E = {a: sum(R[k][a][1] for k in both) / len(both) for a in A}
        Q = {a: sum(R[k][a][2] for k in both) / len(both) for a in A}
        pc = defaultdict(lambda: [0, 0])
        for k in both: pc[k[2]][0] += R[k]['jps_fls'][1]; pc[k[2]][1] += R[k]['jps_state'][1]
        rr = sorted(x[0] / x[1] for x in pc.values())
        print(v, w, 'inst', len(ks), 'fail', fail, '| solved by all', len(both), '| mean exp', {a: round(E[a]) for a in A},
              'fls/state %.3f fls/cell %.3f' % (E['jps_fls'] / E['jps_state'], E['jps_fls'] / E['jps_cell']),
              '| per-coll fls/state %.2f-%.2f' % (rr[0], rr[-1]), '| mean cost ratio', {a: round(Q[a], 4) for a in A})
