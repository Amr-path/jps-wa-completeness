"""Parse logs/lazyv2_N*_w*.log into a results table (N, w, wa, t -> status, solve time, lazy iterations)."""
import glob, re, os, collections
rows = collections.OrderedDict()
for f in sorted(glob.glob('/home/claude/jps-wa/agent_math/sat/logs/lazyv2_N*_w*.log')):
    m = re.match(r'.*lazyv2_N(\d+)_w(\d+)_(\d+)(_noWA)?(?:_t\d+)?\.log', f)
    if not m: continue
    N, p, q, nowa = int(m.group(1)), int(m.group(2)), int(m.group(3)), bool(m.group(4))
    for line in open(f):
        mm = re.match(r"t=\((\d+), (\d+)\): (\w+)\s+build (\d+)s solve (\d+)s iters (\d+)", line)
        if mm:
            key = (N, 'any order' if nowa else f'{p}/{q}', (int(mm.group(1)), int(mm.group(2))))
            rows[key] = (mm.group(3), int(mm.group(5)), int(mm.group(6)))
print(f'{"N":>2} {"order":>10} {"t":>8} {"status":>8} {"solve[s]":>9} {"iters":>5}')
for (N, w, t), (st, dt, it) in sorted(rows.items(), key=lambda kv: (kv[0][0], kv[0][1] != 'any order', kv[0][1], kv[0][2])):
    print(f'{N:>2} {w:>10} {str(t):>8} {st:>8} {dt:>9} {it:>5}')
