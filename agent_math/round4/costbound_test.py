"""Does cell-closing canonical JPS + WA* satisfy g(t) <= w*C* (the standard WA* bound)?  Reference implementation,
random grids, tie rules hig/log/fifo/lifo.  Also records the number of runs where t was NOT found (should be 0)."""
import sys, random, math
sys.path.insert(0, '/home/claude/jps-wa/ref')
from jpswa import Grid, CanonicalJPS, dijkstra
rnd = random.Random(7)
viol = {}; runs = 0; notfound = 0; worst = {}
for it in range(3000):
    N = rnd.randint(5, 16); dens = rnd.choice([0.1, 0.2, 0.3, 0.4])
    cells = [(x, y) for x in range(N) for y in range(N)]
    g = Grid(N, N, [c for c in cells if rnd.random() < dens]); fr = [c for c in cells if g.free(*c)]
    if len(fr) < 2: continue
    s, t = rnd.sample(fr, 2); C = dijkstra(g, s, t)
    if C == math.inf: continue
    for w in (1.0, 1.2, 1.5, 2.0, 3.0, 5.0):
        for tie in ('hig', 'log', 'fifo', 'lifo'):
            c, _ = CanonicalJPS(g, s, t, w, tie).search(); runs += 1
            if c == math.inf: notfound += 1; continue
            if c > w * C + 1e-9:
                viol[w] = viol.get(w, 0) + 1; worst[w] = max(worst.get(w, 0), c / C)
                if viol[w] <= 2: print(f'VIOLATION w={w} tie={tie} g(t)={c:.3f} C*={C:.3f} ratio={c/C:.3f} N={N} s={s} t={t} blocked={sorted(g.blocked)}')
print('runs', runs, 'not found', notfound, 'violations of g(t)<=w*C* by w:', viol, 'worst ratio', worst)
