"""Aggregate results/*.csv into per-collection, per-w, per-algorithm tables.

Rows with opt == inf are instances unsolvable under the no-corner-cutting rule and are excluded
(they are reported separately). Statistics: instances, found rate, bound violations (cost > w*opt),
mean cost ratio, max ratio, mean expansions, mean scanned cells, mean time (micro-seconds), max
expansions per cell.
"""
import csv, glob, os, sys, math
from collections import defaultdict

R = '/path/to/jps-wa/results'
agg = defaultdict(lambda: dict(n=0, found=0, viol=0, ratio=0.0, maxratio=0.0, exp=0, gen=0, scan=0, us=0, maxexp=0, unsolv=0))
for fn in glob.glob(os.path.join(R, '*.csv')):
    coll = os.path.basename(fn).split('.')[0]
    with open(fn) as f:
        for row in csv.DictReader(f):
            key = (coll, row['alg'], float(row['w']))
            a = agg[key]
            if row['opt'] == 'inf':
                a['unsolv'] += 1; continue
            a['n'] += 1
            if row['found'] == '1':
                a['found'] += 1; r = float(row['ratio']); a['ratio'] += r; a['maxratio'] = max(a['maxratio'], r)
            if row['bound_ok'] == '0': a['viol'] += 1
            a['exp'] += int(row['expanded']); a['gen'] += int(row['generated']); a['scan'] += int(row['scanned'])
            a['us'] += int(row['micros']); a['maxexp'] = max(a['maxexp'], int(row['maxexp_cell']))

print(f"{'coll':8s} {'alg':10s} {'w':>4s} {'n':>7s} {'found':>7s} {'viol':>5s} {'mean_r':>8s} {'max_r':>8s} {'exp':>9s} {'scan':>10s} {'us':>8s} {'mxe':>4s} {'unsolv':>6s}")
for key in sorted(agg):
    a = agg[key]; n = max(a['n'], 1); fnd = max(a['found'], 1)
    print(f"{key[0]:8s} {key[1]:10s} {key[2]:4g} {a['n']:7d} {a['found']:7d} {a['viol']:5d} {a['ratio']/fnd:8.4f} {a['maxratio']:8.4f} {a['exp']/n:9.1f} {a['scan']/n:10.1f} {a['us']/n:8.1f} {a['maxexp']:4d} {a['unsolv']:6d}")
