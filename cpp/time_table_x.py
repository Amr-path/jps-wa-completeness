"""Running-time table from results_time_x/ (exact-arithmetic program, --timing 1, five repetitions).
Per instance the median of the five repetitions is taken; the table gives the mean of these medians (microseconds).
Exact optima are taken from results_x/ (same instances: every 100th id is in the every-20th / every-50th sample).
Writes paper/time_table.tex only when every instance has five repetitions for all four algorithms and three weights.
Also prints ratios to cell-closing (of means, from unrounded data), per-instance paired ratios (median, IQR),
the spread of the repetitions, and the number of instances per collection."""
import csv, glob, re, statistics as st, sys
from collections import defaultdict
sys.path.insert(0, '/path/to/jps-wa/cpp')
from analyze_exact import exact_ok, fmt

ROOT = '/path/to/jps-wa'
COLLS = ['dao', 'da2', 'bg512', 'sc1', 'rooms', 'random', 'mazes']
ALGS = ['jps_cell', 'jps_state', 'jps_fls', 'wastar']; WS = ['1', '2', '10']

OPT = {}
for fn in glob.glob(ROOT + '/results_x/*.jps_cell.w1.csv'):
    c, mp = re.search(r'/([^/.]+)\.(.*)\.jps_cell\.w1\.csv$', fn).groups()
    for r in csv.DictReader(open(fn)): OPT[(c, mp, r['id'])] = (r['opt_a'], r['opt_b'])
T = defaultdict(list); bad = 0; missing = 0
for fn in glob.glob(ROOT + '/results_time_x/*.csv'):
    c, mp, a, w, rep = re.search(r'/([^/.]+)\.(.*)\.(jps_cell|jps_state|jps_fls|wastar)\.w([0-9.]+)\.r(\d)\.csv$', fn).groups()
    for r in csv.DictReader(open(fn)):
        k = (c, mp, r['id'])
        if k not in OPT: missing += 1; continue
        oa, ob = OPT[k]
        if oa == '-1': continue
        r = dict(r); r['opt_a'], r['opt_b'] = oa, ob
        if r['found'] != '1' or not exact_ok(r, w): bad += 1
        T[(c, w, a, mp, r['id'])].append(int(r['micros']))
reps = defaultdict(int)
for v in T.values(): reps[len(v)] += 1
print('repetitions per (instance, alg, w):', dict(reps), '| bound violations or not found:', bad, '| ids without optimum:', missing)
MED = {k: st.median(v) for k, v in T.items() if len(v) == 5}
spread = [(max(T[k]) - min(T[k])) / m for k, m in MED.items() if m > 0]
print('relative range of the five repetitions: median %.3f, 90th percentile %.3f' % (st.median(spread), sorted(spread)[int(.9 * len(spread))]))
complete = all(len(v) == 5 for v in T.values()) and reps and len(reps) == 1
inst = defaultdict(set)
for (c, w, a, mp, i) in MED: inst[c].add((mp, i))
print('instances per collection', {c: len(inst[c]) for c in COLLS}, 'total', sum(len(inst[c]) for c in COLLS))
M = defaultdict(list)
for (c, w, a, mp, i), m in MED.items(): M[(c, w, a)].append(m)
out = ['\\begin{tabular}{llrrrr}', '\\toprule', 'set & $w$ & cell & state & FLS & WA*\\\\', '\\midrule']
R = defaultdict(list)
for ci, c in enumerate(COLLS):
    for j, w in enumerate(WS):
        mm = {a: st.mean(M[(c, w, a)]) for a in ALGS}; n = {a: len(M[(c, w, a)]) for a in ALGS}
        assert len(set(n.values())) == 1, (c, w, n)
        for a in ALGS[1:]: R[a].append(mm[a] / mm['jps_cell'])
        paired = {a: [MED[(c, w, a, mp, i)] / MED[(c, w, 'jps_cell', mp, i)] for (mp, i) in inst[c]
                      if MED[(c, w, 'jps_cell', mp, i)] > 0] for a in ALGS[1:]}
        def q(v): v = sorted(v); return '%.2f [%.2f,%.2f]' % (st.median(v), v[len(v) // 4], v[3 * len(v) // 4])
        print(c, w, 'n', n['jps_cell'], 'mean us', ' '.join('%.1f' % mm[a] for a in ALGS),
              '| ratio of means state %.3f fls %.3f wa %.3f' % tuple(mm[a] / mm['jps_cell'] for a in ALGS[1:]),
              '| paired median [IQR] state', q(paired['jps_state']), 'fls', q(paired['jps_fls']),
              '| min mean is cell' if min(mm, key=mm.get) == 'jps_cell' else '| MIN MEAN NOT CELL: ' + min(mm, key=mm.get))
        out.append((c if j == 0 else '') + ' & ' + w + ' & ' + ' & '.join(fmt(mm[a]) for a in ALGS) + ' \\\\')
    out.append('\\midrule' if ci < len(COLLS) - 1 else '\\bottomrule')
out.append('\\end{tabular}')
for a in ALGS[1:]: print('ratio of means to cell', a, 'range %.3f %.3f' % (min(R[a]), max(R[a])))
if complete: open(ROOT + '/paper/time_table.tex', 'w').write('\n'.join(out) + '\n'); print('time_table.tex written')
else: print('(incomplete: table not written)')
