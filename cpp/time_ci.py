"""95% bootstrap confidence intervals (percentile, 2000 resamples of instances, seed 1) for the ratio of mean running
times state/cell and FLS/cell in each row of Table 5 (results_time_x: per-instance median of five repetitions;
instances without an optimum in results_x excluded, as in time_table_x.py)."""
import csv, glob, re, statistics as st, random
from collections import defaultdict
ROOT = '/path/to/jps-wa'
OPT = {}
for fn in glob.glob(ROOT + '/results_x/*.jps_cell.w1.csv'):
    c, mp = re.search(r'/([^/.]+)\.(.*)\.jps_cell\.w1\.csv$', fn).groups()
    for r in csv.DictReader(open(fn)): OPT[(c, mp, r['id'])] = r['opt_a']
T = defaultdict(list)
for fn in glob.glob(ROOT + '/results_time_x/*.csv'):
    c, mp, a, w, rep = re.search(r'/([^/.]+)\.(.*)\.(jps_cell|jps_state|jps_fls|wastar)\.w([0-9.]+)\.r(\d)\.csv$', fn).groups()
    for r in csv.DictReader(open(fn)):
        if OPT.get((c, mp, r['id']), '-1') == '-1': continue  # unreachable target or no optimum: excluded as in Table 5
        T[(c, w, a, mp, r['id'])].append(int(r['micros']))
MED = {k: st.median(v) for k, v in T.items() if len(v) == 5}
rows = defaultdict(lambda: defaultdict(dict))
for (c, w, a, mp, i), m in MED.items(): rows[(c, w)][(mp, i)][a] = m
rng = random.Random(1); lo_all = {}
for c in ['dao', 'da2', 'bg512', 'sc1', 'rooms', 'random', 'mazes']:
    for w in ['1', '2', '10']:
        inst = [v for v in rows[(c, w)].values() if len(v) == 4]; n = len(inst)
        out = []
        for a in ('jps_state', 'jps_fls'):
            pt = sum(v[a] for v in inst) / sum(v['jps_cell'] for v in inst); bs = []
            for _ in range(2000):
                smp = [inst[rng.randrange(n)] for _ in range(n)]
                bs.append(sum(v[a] for v in smp) / sum(v['jps_cell'] for v in smp))
            bs.sort(); out.append('%s %.3f [%.3f, %.3f]' % (a, pt, bs[49], bs[1949])); lo_all[(c, w, a)] = (bs[49], bs[1949])
        print(c, w, n, ' | '.join(out))
for a in ('jps_state', 'jps_fls'):
    print(a, 'min lower', min(v[0] for k, v in lo_all.items() if k[2] == a), 'max upper', max(v[1] for k, v in lo_all.items() if k[2] == a))
