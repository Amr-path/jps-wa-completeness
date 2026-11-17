"""Running times on the failing variants (results_var_time) and of JPS with re-expansions (results_reopen_time).
Per instance the median of five repetitions; instances with an unreachable target (opt_a = -1 in results_var or
results_x) are excluded. Reports, per collection, variant and weight, the mean time of cell-closing, state-closing and
FLS (microseconds), the ratios of means with 95% bootstrap intervals (2000 resamples of instances, seed 1), and the
same for jps_reopen against jps_cell."""
import csv, glob, re, statistics as st, random
from collections import defaultdict
ROOT = '/path/to/jps-wa'; COLLS = ['dao', 'da2', 'bg512', 'sc1', 'rooms', 'random', 'mazes']
rng = random.Random(1)
def boot(inst, a, b):
    n = len(inst); bs = []
    for _ in range(2000):
        smp = [inst[rng.randrange(n)] for _ in range(n)]
        bs.append(sum(v[a] for v in smp) / sum(v[b] for v in smp))
    bs.sort(); return sum(v[a] for v in inst) / sum(v[b] for v in inst), bs[49], bs[1949]
# variants
OPTV = {}
for fn in glob.glob(ROOT + '/results_var/*.jps_cell.w2.csv'):
    c, mp, v = re.search(r'/([^/.]+)\.(.*)\.(bjps8|cc)\.jps_cell\.w2\.csv$', fn).groups()
    for r in csv.DictReader(open(fn)): OPTV[(c, mp, r['id'])] = r['opt_a']
T = defaultdict(list)
for fn in glob.glob(ROOT + '/results_var_time/*.csv'):
    c, mp, v, a, w, rep = re.search(r'/([^/.]+)\.(.*)\.(bjps8|cc)\.(jps_cell|jps_state|jps_fls)\.w([0-9.]+)\.r(\d)\.csv$', fn).groups()
    for r in csv.DictReader(open(fn)):
        if OPTV.get((c, mp, r['id']), '-1') == '-1': continue
        T[(v, w, c, mp, r['id'], a)].append(int(r['micros']))
rows = defaultdict(lambda: defaultdict(dict))
for (v, w, c, mp, i, a), x in T.items():
    if len(x) == 5: rows[(v, w, c)][(mp, i)][a] = st.median(x)
allr = defaultdict(list)
print('VARIANTS: mean us cell/state/fls | state/cell | fls/cell | fls/state [95% CI]')
for v in ('bjps8', 'cc'):
    for w in ('2', '8'):
        pooled = []
        for c in COLLS:
            inst = [d for d in rows[(v, w, c)].values() if len(d) == 3]; pooled += inst
            m = {a: sum(d[a] for d in inst) / len(inst) for a in ('jps_cell', 'jps_state', 'jps_fls')}
            fs = boot(inst, 'jps_fls', 'jps_state'); allr[('fls/state')].append(fs); allr['state/cell'].append(m['jps_state'] / m['jps_cell']); allr['fls/cell'].append(m['jps_fls'] / m['jps_cell'])
            print(v, w, c, len(inst), ' '.join('%.0f' % m[a] for a in ('jps_cell', 'jps_state', 'jps_fls')),
                  '| %.2f | %.2f | %.3f [%.3f, %.3f]' % (m['jps_state'] / m['jps_cell'], m['jps_fls'] / m['jps_cell'], *fs))
        fs = boot(pooled, 'jps_fls', 'jps_state'); print(v, w, 'POOLED', len(pooled), 'fls/state %.3f [%.3f, %.3f]' % fs)
print('ranges over rows: state/cell %.2f-%.2f fls/cell %.2f-%.2f fls/state %.2f-%.2f (max upper %.3f)' % (
    min(allr['state/cell']), max(allr['state/cell']), min(allr['fls/cell']), max(allr['fls/cell']),
    min(x[0] for x in allr['fls/state']), max(x[0] for x in allr['fls/state']), max(x[2] for x in allr['fls/state'])))
# re-expansions
OPT = {}
for fn in glob.glob(ROOT + '/results_x/*.jps_cell.w1.csv'):
    c, mp = re.search(r'/([^/.]+)\.(.*)\.jps_cell\.w1\.csv$', fn).groups()
    for r in csv.DictReader(open(fn)): OPT[(c, mp, r['id'])] = r['opt_a']
T = defaultdict(list)
for fn in glob.glob(ROOT + '/results_reopen_time/*.csv'):
    c, mp, a, w, rep = re.search(r'/([^/.]+)\.(.*)\.(jps_cell|jps_reopen)\.w([0-9.]+)\.r(\d)\.csv$', fn).groups()
    for r in csv.DictReader(open(fn)):
        if OPT.get((c, mp, r['id']), '-1') == '-1': continue
        T[(w, c, mp, r['id'], a)].append(int(r['micros']))
rows = defaultdict(lambda: defaultdict(dict))
for (w, c, mp, i, a), x in T.items():
    if len(x) == 5: rows[(w, c)][(mp, i)][a] = st.median(x)
print('REOPEN: mean us cell/reopen | reopen/cell [95% CI]'); rr = []
for c in COLLS:
    for w in ('1', '2', '10'):
        inst = [d for d in rows[(w, c)].values() if len(d) == 2]
        m = {a: sum(d[a] for d in inst) / len(inst) for a in ('jps_cell', 'jps_reopen')}
        b = boot(inst, 'jps_reopen', 'jps_cell'); rr.append(b[0])
        print(c, w, len(inst), '%.0f %.0f | %.3f [%.3f, %.3f]' % (m['jps_cell'], m['jps_reopen'], *b))
print('reopen/cell range %.2f-%.2f' % (min(rr), max(rr)))
