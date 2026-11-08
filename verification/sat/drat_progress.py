"""Live progress display for run_drat.sh (reads only the files in drat/; changes nothing).
Each target has three stages: lazy loop, CaDiCaL with proof, drat-trim check. The bar counts finished stages
(48 in all), so it shows how much of the work list is done, not a time estimate.
usage: python3 drat_progress.py "1 3|3 1|..." <stop-flag-file>"""
import os, sys, time, re, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, 'drat')
TARGETS = [tuple(p.split()) for p in sys.argv[1].split('|')]
STOP = sys.argv[2]
T0 = time.time()
TTY = sys.stdout.isatty()


def hms(s):
    s = int(s); return '%d:%02d:%02d' % (s // 3600, s % 3600 // 60, s % 60)


def state(tx, ty):
    """(stages done 0..3, label) for one target, from the part of its log after the last start line."""
    tag = 't%s%s' % (tx, ty)
    try: txt = open(os.path.join(D, 'drat_%s.log' % tag)).read()
    except OSError: txt = ''
    if 'RESULT' in txt:
        ok = 's VERIFIED' in [l for l in txt.splitlines() if l.startswith('RESULT')][-1]
        return 3, ('VERIFIED' if ok else 'FINISHED, NOT VERIFIED (see log)')
    st = ''
    try: st = open(os.path.join(D, 'state_%s' % tag)).read().split()
    except OSError: pass
    if not st: return 0, 'waiting'
    since = time.time() - float(st[1])
    if st[0] == 'ended': return 0, 'STOPPED WITHOUT RESULT (see log)'
    cur = txt.split('=== ')[-1] if '=== ' in txt else ''
    if 'cadical exit' in cur: return 2, '3/3 drat-trim, %s' % hms(since)
    if 'lazy:' in cur:
        p = os.path.join(D, 'proof_%s.drat' % tag)
        g = os.path.getsize(p) / 1e9 if os.path.exists(p) else 0
        return 1, '2/3 CaDiCaL, proof %.2f GB, %s' % (g, hms(since))
    return 0, '1/3 lazy loop, %s' % hms(since)


prev = 0
while True:
    rows = [(t, *state(*t)) for t in TARGETS]
    done = sum(1 for r in rows if r[1] == 3)
    stages = sum(r[1] for r in rows)
    frac = stages / (3 * len(TARGETS))
    run = [r for r in rows if r[2][:2] in ('1/','2/','3/')]
    fail = sum(1 for r in rows if 'NOT VERIFIED' in r[2] or 'STOPPED' in r[2])
    W = 20; fill = int(round(frac * W))
    free = shutil.disk_usage(D).free / 1e9
    lines = ['DRAT [%s%s] %3d%%  ok %d/%d  fail %d  run %d  left %d  %s  disk %.0fGB' % (
        '#' * fill, '.' * (W - fill), round(100 * frac), sum(1 for r in rows if r[2] == 'VERIFIED'), len(TARGETS),
        fail, len(run), len(TARGETS) - done - len(run) - fail + sum(1 for r in rows if 'NOT VERIFIED' in r[2]), hms(time.time() - T0), free)]
    for (tx, ty), s, lab in rows:
        if lab != 'waiting': lines.append('  t=(%s,%s)  %s' % (tx, ty, lab))
    if free < 10: lines.append('  WARNING: less than 10 GB free; a proof file may not fit.')
    cols = shutil.get_terminal_size((100, 24)).columns - 1
    lines = [l[:cols] for l in lines]
    if TTY:
        sys.stdout.write('\033[%dA' % prev if prev else '')
        sys.stdout.write(''.join('\r\033[K' + l + '\n' for l in lines)); prev = len(lines)
    else:
        print(lines[0])
    sys.stdout.flush()
    if os.path.exists(STOP): break
    time.sleep(5)
