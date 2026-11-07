"""Analysis of the exact-arithmetic runs (results_x/, results_tie_x/, results_time_x/).
Writes paper/exp_table.tex (Table: mean expansions and scanned cells), paper/time_table.tex (mean of per-instance
medians of five repetitions), and prints every summary number used in Section 8.
usage: python3 analyze_exact.py [main|tie|time|all]"""
import csv, glob, os, re, sys, statistics as st
from collections import defaultdict

ROOT = '/home/claude/jps-wa'
COLLS = ['dao', 'da2', 'bg512', 'sc1', 'rooms', 'random', 'mazes']
ALGS = ['jps_cell', 'jps_state', 'jps_fls', 'wastar']
WS = ['1', '1.5', '2', '3', '5', '10']
SQ2 = 2 ** 0.5


def exact_ok(row, w):
    """bound check from the integer columns: cost <= w * opt exactly (w a multiple of 1/2)."""
    ca, cb, oa, ob = (int(row[k]) for k in ('cost_a', 'cost_b', 'opt_a', 'opt_b'))
    w2 = round(2 * float(w))
    A, B = w2 * oa - 2 * ca, w2 * ob - 2 * cb  # sign of A + B sqrt2 must be >= 0
    if A >= 0 and B >= 0: return True
    if A <= 0 and B <= 0: return A == 0 and B == 0
    s = A * A - 2 * B * B
    return s > 0 if A > 0 else s < 0


def fmt(v):
    v = int(round(v)); s = str(v)
    return s[:-3] + '\\,' + s[-3:] if v >= 10000 else s


def main():
    D = defaultdict(dict)  # (coll, map, alg, w) -> {id: row}
    for fn in glob.glob(ROOT + '/results_x/*.csv'):
        m = re.search(r'/([^/.]+)\.(.*)\.(jps_cell|jps_state|jps_fls|wastar)\.w([0-9.]+)\.csv$', fn)
        c, mp, a, w = m.groups()
        D[(c, mp, a, w)] = {r['id']: r for r in csv.DictReader(open(fn))}
    maps = sorted({(c, mp) for (c, mp, a, w) in D})
    complete = all((c, mp, a, w) in D for c, mp in maps for a in ALGS for w in WS)
    print('maps', len(maps), 'complete', complete, 'files', len(D))
    n = defaultdict(int); E = defaultdict(int); S = defaultdict(int); nf = 0; bad = 0; runs = 0
    maxr = defaultdict(float); sumr = defaultdict(float); inst = set(); flsdiff = 0; flsmax = 0; flscost = 0
    for (c, mp, a, w), rows in D.items():
        for i, r in rows.items():
            if r['opt_a'] == '-1': continue  # disconnected pair
            runs += 1; inst.add((c, mp, i))
            if r['found'] != '1': nf += 1; continue
            if r['bound_ok'] != '1' or not exact_ok(r, w): bad += 1
            k = (c, a, w); n[k] += 1; E[k] += int(r['expanded']); S[k] += int(r['scanned'])
            ratio = float(r['cost']) / float(r['opt']); maxr[k] = max(maxr[k], ratio); sumr[k] += ratio
            if a == 'jps_fls' and w == '1':
                rc = D[(c, mp, 'jps_cell', w)][i]
                if rc['expanded'] != r['expanded']:
                    flsdiff += 1; flsmax = max(flsmax, abs(int(rc['expanded']) - int(r['expanded'])))
                if (rc['cost_a'], rc['cost_b']) != (r['cost_a'], r['cost_b']): flscost += 1
    print('runs', runs, 'instances', len(inst), 'not found', nf, 'bound violations', bad)
    per = defaultdict(int)
    for (c, mp, i) in inst: per[c] += 1
    print('instances per collection', dict(per))
    # table
    out = ['\\begin{tabular}{llrrrrrrr}', '\\toprule',
           ' & & \\multicolumn{4}{c}{expansions} & \\multicolumn{3}{c}{scanned ($10^3$)}\\\\',
           '\\cmidrule(lr){3-6}\\cmidrule(lr){7-9}',
           'set & $w$ & cell & state & FLS & grid WA* & cell & state & FLS\\\\', '\\midrule']
    for ci, c in enumerate(COLLS):
        for j, w in enumerate(['1', '2', '10']):
            e = [E[(c, a, w)] / n[(c, a, w)] for a in ALGS]
            s = [S[(c, a, w)] / n[(c, a, w)] / 1000 for a in ALGS[:3]]
            out.append(('%s' % c if j == 0 else '') + ' & ' + w + ' & ' + ' & '.join(fmt(v) for v in e) + ' & '
                       + ' & '.join('%.1f' % v for v in s) + ' \\\\')
        out.append('\\midrule' if ci < len(COLLS) - 1 else '\\bottomrule')
    out.append('\\end{tabular}')
    if complete: open(ROOT + '/paper/exp_table.tex', 'w').write('\n'.join(out) + '\n')
    else: print('(incomplete: table not written)')
    # ratios
    rat = {c: [E[(c, 'jps_state', w)] / n[(c, 'jps_state', w)] / (E[(c, 'jps_cell', w)] / n[(c, 'jps_cell', w)]) for w in WS] for c in COLLS}
    for c in COLLS: print('state/cell expansions', c, ' '.join('%.3f' % x for x in rat[c]),
                          'monotone' if all(rat[c][i] >= rat[c][i + 1] for i in range(5)) else 'NOT monotone')
    allr = [x for c in COLLS for x in rat[c]]
    print('state/cell exp range %.3f %.3f; at w=10 %.3f %.3f' % (min(allr), max(allr), min(rat[c][5] for c in COLLS), max(rat[c][5] for c in COLLS)))
    sr = [S[(c, 'jps_state', w)] / n[(c, 'jps_state', w)] / (S[(c, 'jps_cell', w)] / n[(c, 'jps_cell', w)]) for c in COLLS for w in WS]
    print('state/cell scanned range %.3f %.3f' % (min(sr), max(sr)))
    fr = [(E[(c, 'jps_fls', w)] / n[(c, 'jps_fls', w)]) / (E[(c, 'jps_cell', w)] / n[(c, 'jps_cell', w)]) for c in COLLS for w in WS]
    print('FLS/cell exp: max over all %.3f; per w:' % max(fr), {w: '%.3f' % max((E[(c, 'jps_fls', w)] / n[(c, 'jps_fls', w)]) / (E[(c, 'jps_cell', w)] / n[(c, 'jps_cell', w)]) for c in COLLS) for w in WS})
    print('FLS vs cell at w=1: instances with different expansions', flsdiff, 'max diff', flsmax, 'different cost', flscost)
    for a in ALGS:
        best = sorted(((maxr[(c, a, w)], c, w) for c in COLLS for w in WS), reverse=True)[:3]
        print('max ratio', a, ['%.3f %s w=%s' % b for b in best])
    for c in COLLS:
        print('max ratio', c, {a: '%.3f' % max(maxr[(c, a, w)] for w in WS) for a in ALGS})
    md = 0
    for c in COLLS:
        for w in WS:
            mr = [sumr[(c, a, w)] / n[(c, a, w)] for a in ALGS[:3]]
            md = max(md, (max(mr) - min(mr)) / min(mr))
    print('max relative difference of mean ratios among the three JPS searches %.4f' % md)
    print('pgfplots:')
    for c in COLLS:
        print(c, ' '.join('(%s,%.3f)' % (w, r) for w, r in zip(WS, rat[c])))


def tie():
    n = defaultdict(int); nf = 0; bad = 0; mr = 0; files = 0; inst = set()
    for fn in glob.glob(ROOT + '/results_tie_x/*.csv'):
        files += 1
        m = re.search(r'/([^/.]+)\.(.*)\.jps_cell\.(\w+)\.w([0-9.]+)\.csv$', fn); c, mp, tie, w = m.groups()
        for r in csv.DictReader(open(fn)):
            if r['opt_a'] == '-1': continue
            n[tie] += 1; inst.add((c, mp, r['id']))
            if r['found'] != '1': nf += 1; continue
            if r['bound_ok'] != '1' or not exact_ok(r, w): bad += 1
            mr = max(mr, float(r['cost']) / float(r['opt']))
    print('tie files', files, 'runs', dict(n), 'total', sum(n.values()), 'instances', len(inst), 'not found', nf, 'bound violations', bad, 'max ratio %.3f' % mr)


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if what in ('main', 'all'): main()
    if what in ('tie', 'all'): tie()
