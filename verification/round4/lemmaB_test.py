"""LEMMA B / THEOREM B test.
Lemma B (proved in the report): if t is never visited, every cell z closed no later than the break cell x_i of a
J-path pi to t satisfies f(z) = g(z) + w h(z) <= w (P_i(pi) + h(x_i)) <= w cost(pi).  With pi = canonical optimal
J-path: f(z) <= w C*.
Here we test the stronger, UNPROVED statement B+ on successful WA* runs (reference implementation): EVERY closed
cell z satisfies f(z) <= w C*  (true for WA* on a fixed graph with consistent h).  We also record the max of
(g(z) + w h(z)) / (w C*) over closings and whether it ever exceeds 1."""
import sys, random, math
sys.path.insert(0, '/path/to/jps-wa/ref')
sys.path.insert(0, '/path/to/jps-wa/verification/round4')
from jpswa import Grid, CanonicalJPS, dijkstra, octile
from lemmaA_test import InstrJPS
rnd = random.Random(11)
viol = {}; runs = 0; worst = {}; closings = 0
for it in range(2500):
    N = rnd.randint(5, 16); dens = rnd.choice([0.1, 0.2, 0.3, 0.4])
    cells = [(x, y) for x in range(N) for y in range(N)]
    g = Grid(N, N, [c for c in cells if rnd.random() < dens]); fr = [c for c in cells if g.free(*c)]
    if len(fr) < 2: continue
    s, t = rnd.sample(fr, 2); C = dijkstra(g, s, t)
    if C == math.inf: continue
    for w in (1.0, 1.2, 1.5, 2.0, 3.0, 5.0):
        for tie in ('hig', 'log', 'fifo', 'lifo'):
            J = InstrJPS(g, s, t, w, tie); J.search(); runs += 1
            for z, (gz, p) in J.closing.items():
                closings += 1
                fz = gz + w * octile(z[0], z[1], t[0], t[1])
                worst[w] = max(worst.get(w, 0), fz / (w * C))
                if fz > w * C + 1e-9:
                    viol[w] = viol.get(w, 0) + 1
                    if viol[w] <= 2: print(f'B+ VIOLATION w={w} tie={tie} z={z} f={fz:.3f} wC*={w*C:.3f} N={N} s={s} t={t} blocked={sorted(g.blocked)}')
print('runs', runs, 'closings', closings, 'violations of f(z)<=w C* by w:', viol)
print('max f(z)/(w C*) by w:', {k: round(v, 4) for k, v in worst.items()})
