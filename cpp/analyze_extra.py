"""Analysis of the robot-map runs (results_robot/) and the positive control (results_var/).
Every number printed here is computed from the integer cost columns (cost = a + b sqrt2) with exact arithmetic.
usage: python3 analyze_extra.py [robot|var|all]"""
import csv, glob, re, sys
from collections import defaultdict
from fractions import Fraction

ROOT = '/home/claude/jps-wa'


def within(row, w):
    """exact check of cost <= w * opt for rational w."""
    q = Fraction(w).limit_denominator(1000); P, Q = q.numerator, q.denominator
    ca, cb, oa, ob = (int(row[k]) for k in ('cost_a', 'cost_b', 'opt_a', 'opt_b'))
    A, B = P * oa - Q * ca, P * ob - Q * cb  # need A + B sqrt2 >= 0
    if A >= 0 and B >= 0: return True
    if A <= 0 and B <= 0: return A == 0 and B == 0
    s = A * A - 2 * B * B
    return s > 0 if A > 0 else s < 0


def robot():
    ALGS = ['jps_cell', 'jps_state', 'jps_fls', 'wastar']; WS = ['1', '1.5', '2', '3', '5', '10']
    n = defaultdict(int); E = defaultdict(int); S = defaultdict(int); mx = defaultdict(float); sr = defaultdict(float)
    runs = nf = bad = 0; inst = defaultdict(set); files = 0; disc = set()
    for fn in glob.glob(ROOT + '/results_robot/*.csv'):
        m = re.search(r'/(real|houseexpo)\.(.*)\.(jps_cell|jps_state|jps_fls|wastar)\.w([0-9.]+)\.csv$', fn)
        st, mp, a, w = m.groups(); files += 1
        for r in csv.DictReader(open(fn)):
            if r['opt_a'] == '-1': disc.add((st, mp, r['id'])); continue
            runs += 1; inst[st].add((mp, r['id']))
            if r['found'] != '1': nf += 1; continue
            if r['bound_ok'] != '1' or not within(r, w): bad += 1
            k = (st, a, w); n[k] += 1; E[k] += int(r['expanded']); S[k] += int(r['scanned'])
            x = float(r['cost']) / float(r['opt']); mx[k] = max(mx[k], x); sr[k] += x
    print('robot files', files, 'runs', runs, 'instances', {s: len(v) for s, v in inst.items()},
          'disconnected pairs', len(disc), 'not found', nf, 'bound violations', bad)
    for st in ('real', 'houseexpo'):
        for w in WS:
            e = {a: E[(st, a, w)] / n[(st, a, w)] for a in ALGS}
            print(st, 'w=' + w, 'mean exp', ' '.join('%s %.1f' % (a, e[a]) for a in ALGS),
                  '| state/cell %.3f fls/cell %.3f' % (e['jps_state'] / e['jps_cell'], e['jps_fls'] / e['jps_cell']),
                  '| scanned state/cell %.3f' % (S[(st, 'jps_state', w)] / S[(st, 'jps_cell', w)]),
                  '| mean ratio', ' '.join('%.4f' % (sr[(st, a, w)] / n[(st, a, w)]) for a in ALGS))
        print(st, 'max ratio', {a: '%.3f' % max(mx[(st, a, w)] for w in WS) for a in ALGS})


def var():
    WS = ['1.2', '2', '4', '8']
    tot = defaultdict(int); fail = defaultdict(int); nfk = defaultdict(int); bk = defaultdict(int)
    E = defaultdict(int); N = defaultdict(int); colls = defaultdict(set); mx = defaultdict(float)
    for fn in glob.glob(ROOT + '/results_var/*.csv'):
        m = re.search(r'/([^/.]+)\.(.*)\.(bjps8|cc)\.(jps_cell|jps_state)\.w([0-9.]+)\.csv$', fn)
        c, mp, v, a, w = m.groups(); colls[c].add(mp)
        for r in csv.DictReader(open(fn)):
            if r['opt_a'] == '-1': continue
            k = (v, a, w); tot[k] += 1
            if r['found'] != '1': fail[k] += 1; nfk[k] += 1; continue
            if r['bound_ok'] != '1' or not within(r, w): fail[k] += 1; bk[k] += 1; continue
            E[k] += int(r['expanded']); N[k] += 1; mx[k] = max(mx[k], float(r['cost']) / float(r['opt']))
    print('var maps per collection', {c: len(s) for c, s in colls.items()})
    for v in ('bjps8', 'cc'):
        for a in ('jps_cell', 'jps_state'):
            print(v, a, ' | '.join('w=%s: %d/%d fail (%d not found, %d bound) meanexp %.0f maxratio %.3f' % (
                w, fail[(v, a, w)], tot[(v, a, w)], nfk[(v, a, w)], bk[(v, a, w)],
                E[(v, a, w)] / max(1, N[(v, a, w)]), mx[(v, a, w)]) for w in WS))


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if what in ('robot', 'all'): robot()
    if what in ('var', 'all'): var()
