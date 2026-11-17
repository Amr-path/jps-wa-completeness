"""Memory counters and the re-expansion baseline (results_mem, jpswa_exact2; every 100th instance, w in {1,2,10}).
Exact bound check against the optimum in each row (opt_a/opt_b computed by the program). Per collection and weight:
mean expansions, mean g-records written, mean peak open-list size, ratios to cell-closing; for jps_reopen also
failures, bound violations, re-expansions and the largest cost ratio."""
import csv, glob, re, sys
from collections import defaultdict
sys.path.insert(0, '/path/to/jps-wa/cpp')
from analyze_extra import within
ROOT = '/path/to/jps-wa'; ALGS = ['jps_cell', 'jps_state', 'jps_fls', 'jps_reopen']
S = defaultdict(lambda: defaultdict(float)); bad = defaultdict(int); nf = defaultdict(int); mx = defaultdict(float); runs = 0
for fn in glob.glob(ROOT + '/results_mem/*.csv'):
    c, mp, a, w = re.search(r'/([^/.]+)\.(.*)\.(jps_cell|jps_state|jps_fls|jps_reopen)\.w([0-9.]+)\.csv$', fn).groups()
    for r in csv.DictReader(open(fn)):
        if r['opt_a'] == '-1': continue
        runs += 1; k = (c, w, a)
        if r['found'] != '1': nf[k] += 1; continue
        if not within(r, w): bad[k] += 1
        d = S[k]; d['n'] += 1
        for col in ('expanded', 'records', 'peak_open', 'reexp'): d[col] += int(r[col])
        x = float(r['cost']) / float(r['opt']); mx[k] = max(mx[k], x); d['ratio'] += x
print('runs', runs, 'not found', sum(nf.values()), 'bound violations', sum(bad.values()), {k: v for k, v in bad.items() if v})
R = defaultdict(list)
for c in ['dao', 'da2', 'bg512', 'sc1', 'rooms', 'random', 'mazes']:
    for w in ['1', '2', '10']:
        if not S[(c, w, 'jps_cell')]['n']: continue
        m = {a: {col: S[(c, w, a)][col] / S[(c, w, a)]['n'] for col in ('expanded', 'records', 'peak_open', 'reexp', 'ratio')} for a in ALGS}
        for a in ALGS[1:]:
            for col in ('records', 'peak_open', 'expanded'):
                R[(a, col)].append(m[a][col] / m['jps_cell'][col])
        print(c, w, 'n', int(S[(c, w, 'jps_cell')]['n']),
              '| records cell %.0f state/cell %.2f fls/cell %.2f | peak open cell %.0f state/cell %.2f fls/cell %.2f'
              % (m['jps_cell']['records'], m['jps_state']['records'] / m['jps_cell']['records'], m['jps_fls']['records'] / m['jps_cell']['records'],
                 m['jps_cell']['peak_open'], m['jps_state']['peak_open'] / m['jps_cell']['peak_open'], m['jps_fls']['peak_open'] / m['jps_cell']['peak_open']),
              '| reopen exp/cell %.3f reexp %.1f meanratio %.4f (cell %.4f) maxratio %.3f' % (
                  m['jps_reopen']['expanded'] / m['jps_cell']['expanded'], m['jps_reopen']['reexp'], m['jps_reopen']['ratio'], m['jps_cell']['ratio'], mx[(c, w, 'jps_reopen')]))
for (a, col), v in sorted(R.items()): print('range', a, col, '%.3f %.3f' % (min(v), max(v)))
print('max ratio per alg', {a: '%.3f' % max([v for k, v in mx.items() if k[2] == a] or [0]) for a in ALGS})
