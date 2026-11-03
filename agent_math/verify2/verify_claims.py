#!/usr/bin/env python3
"""Recompute the numerical claims of the Experiments section from results/*.csv and results_time/*.csv."""
import csv, glob, os, sys
from collections import defaultdict

R = '/home/claude/jps-wa/results'
RT = '/home/claude/jps-wa/results_time'
colls = ['dao', 'da2', 'bg512', 'sc1', 'rooms', 'random', 'mazes']
algs = ['jps_cell', 'jps_state', 'jps_fls', 'wastar']

def load(root):
    A = defaultdict(lambda: dict(n=0, exp=0, scan=0, us=0, maxr=0.0, viol=0, nf=0, sumr=0.0, ids=set()))
    nrows = 0; ninf = 0; per_w_inst = defaultdict(set)
    for fn in glob.glob(os.path.join(root, '*.csv')):
        base = os.path.basename(fn); coll = base.split('.')[0]
        if coll not in colls: continue
        mapname = '.'.join(base.split('.')[1:-3])
        with open(fn) as f:
            for row in csv.DictReader(f):
                nrows += 1
                if row['opt'] == 'inf': ninf += 1; continue
                w = float(row['w']); a = A[(coll, w, row['alg'])]
                a['n'] += 1; a['exp'] += int(row['expanded']); a['scan'] += int(row['scanned']); a['us'] += int(row['micros'])
                a['ids'].add((mapname, row['id']))
                per_w_inst[(w, row['alg'])].add((coll, mapname, row['id']))
                if row['found'] == '1':
                    r = float(row['ratio']); a['maxr'] = max(a['maxr'], r); a['sumr'] += r
                else: a['nf'] += 1
                if row['bound_ok'] == '0': a['viol'] += 1
    return A, nrows, ninf, per_w_inst

A, nrows, ninf, pwi = load(R)
T, trows, tinf, tpwi = load(RT)

print('== totals (full sweep) ==')
tot_n = sum(a['n'] for a in A.values()); tot_v = sum(a['viol'] for a in A.values()); tot_nf = sum(a['nf'] for a in A.values())
print(f'rows {nrows}, rows with opt=inf (excluded) {ninf}, solvable instance-runs {tot_n}, viol {tot_v}, notfound {tot_nf}')
sizes = {k: len(v) for k, v in pwi.items()}
print('distinct solvable instances per (w,alg):', sorted(set(sizes.values())))
print('solvable instances (w=1, jps_cell):', sizes[(1.0, 'jps_cell')])
# check each (set,w) has same n across algs
bad = [(c, w) for c in colls for w in [1, 1.5, 2, 3, 5, 10] if len({A[(c, w, a)]['n'] for a in algs}) != 1]
print('sets with unequal n across algs:', bad)
ws_seen = sorted({k[1] for k in A}); print('weights seen:', ws_seen)

print('\n== expansion ratios (mean state/mean cell, mean FLS/mean cell), scanned ratios ==')
for c in colls:
    for w in [1, 1.5, 2, 3, 5, 10]:
        ce, st, fl = (A[(c, w, a)] for a in algs[:3])
        print(f'{c:7s} w={w:<4g} exp cell {ce["exp"]/ce["n"]:9.1f} state/cell {st["exp"]/ce["exp"]:.3f} FLS/cell {fl["exp"]/ce["exp"]:.3f}'
              f'   scan state/cell {st["scan"]/ce["scan"]:.3f} FLS/cell {fl["scan"]/ce["scan"]:.3f}')

print('\n== max cost ratios ==')
for c in colls:
    for w in [10]:
        print(c, 'w=10 max', ' / '.join(f'{A[(c, w, a)]["maxr"]:.3f}' for a in algs), '  mean', ' / '.join(f'{A[(c, w, a)]["sumr"]/A[(c, w, a)]["n"]:.4f}' for a in algs))
# global max per alg
for a in algs:
    m = max(((A[k]['maxr'], k) for k in A if k[2] == a)); print('global max', a, m)
# mean ratio spread among JPS searches
print('\n== mean-ratio spread among the three JPS searches (max/min of means - 1) ==')
worst = 0
for c in colls:
    for w in [1.5, 2, 3, 5, 10]:
        ms = [A[(c, w, a)]['sumr']/A[(c, w, a)]['n'] for a in algs[:3]]
        sp = max(ms)/min(ms) - 1; worst = max(worst, sp)
        if sp > 0.01: print(f'{c} w={w}: spread {sp*100:.2f}%  means {ms}')
print('worst spread among JPS means: %.2f%%' % (worst*100))
# excess of mean ratio over 1 (another reading of "within 1-4%")
print('mean ratio - 1, per set w=10 (cell):', {c: round(A[(c, 10, 'jps_cell')]['sumr']/A[(c, 10, 'jps_cell')]['n'] - 1, 4) for c in colls})

print('\n== timing run ==')
tt = sum(a['n'] for a in T.values()); print(f'timing rows {trows}, inf {tinf}, solvable runs {tt}, instances per (w,alg):', sorted({len(v) for v in tpwi.values()}))
print('timing weights:', sorted({k[1] for k in T}))
for c in colls:
    for w in [1, 2, 10]:
        ce, st, fl, wa = (T[(c, w, a)] for a in algs)
        ms = lambda a: a['us']/a['n']/1000
        print(f'{c:7s} w={w:<3g} ms cell {ms(ce):6.2f} state {ms(st):6.2f} FLS {ms(fl):6.2f} WA* {ms(wa):6.2f} | state/cell {ms(st)/ms(ce):.2f} FLS/cell {ms(fl)/ms(ce):.2f} WA*/cell {ms(wa)/ms(ce):.2f} WA*/state {ms(wa)/ms(st):.2f} WA*/FLS {ms(wa)/ms(fl):.2f}')
