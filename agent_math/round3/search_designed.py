"""Broad exact search for a WA*-realisable failure on DESIGNED geometries.
usage: python3 search_designed.py SEED SECONDS
Families (each instance: random N in 7..11, core at a random position, 0-8 random extra obstacles, random s):
  pin1  : 1x1 pinwheel core (4 knight-offset blockers around t), t = core cell
  pin1c : 1x1 core + each arm closed by a 'corridor wall' (parallel wall at offset 2) at random lengths
  pin2  : 2x2 pinwheel core (round-2 5-obstacle instance), t random in the hole
  pin12 : 1x2 hole with pinwheel-like blockers at the four corners (knight offsets of the hole's bounding box)
For every instance and every w in WS the exhaustive WA* tie-adversary (core.wa_adversary) is run; a 'FAIL'
is reproduced with ReplayJPS / the six built-in tie rules and printed.  Also counts how many instances admit an
order-failure at all (min_slack status FAIL/LB) to show the families are not vacuous."""
import sys, time, math, random
sys.path.insert(0, '/home/claude/jps-wa/agent_math/round3')
from core import *

seed = int(sys.argv[1]); secs = float(sys.argv[2]); rng = random.Random(seed)
WS = [1.0, 1.2, 1.5, 2.0, 3.0, 5.0, 10.0, 100.0, 1e6]
D4 = [(1, 0), (0, 1), (-1, 0), (0, -1)]

def core_pin1(c):
    bl = set()
    for i in range(4):
        dp, d = D4[(i - 1) % 4], D4[i]
        bl.add((c[0] - 2 * dp[0] - d[0], c[1] - 2 * dp[1] - d[1]))
    return bl, [c]

def core_pin2(c):   # round-2 instance, hole (3,3),(4,3),(3,4),(4,4) shifted so that hole's top-left is c
    bl = {(3, 1), (6, 3), (1, 4), (4, 6), (1, 6)}; off = (c[0] - 3, c[1] - 3)
    return {(x + off[0], y + off[1]) for x, y in bl}, [(c[0] + a, c[1] + b) for a in (0, 1) for b in (0, 1)]

def core_pin12(c, horiz):
    # hole = c, c+(1,0) (horiz) or c, c+(0,1); blockers: for each hole cell, knight offsets pointing away
    hole = [c, (c[0] + 1, c[1])] if horiz else [c, (c[0], c[1] + 1)]
    x0, y0 = c; x1, y1 = hole[1]
    # four corner-type blockers (rotational pattern around the bounding box): like pin1 but stretched
    bl = {(x0 - 2, y0 - 1), (x1 + 1, y0 - 2) if horiz else (x0 + 1, y0 - 2),
          (x1 + 2, y1 + 1), (x0 - 1, y1 + 2)}
    return bl, hole

def instance():
    fam = rng.choice(['pin1', 'pin1', 'pin1c', 'pin2', 'pin12'])
    N = rng.randint(7, 11)
    c = (rng.randint(3, N - 4), rng.randint(3, N - 4))
    if fam.startswith('pin1') and fam != 'pin12':
        bl, hole = core_pin1(c)
        if fam == 'pin1c':
            for i in range(4):
                dp, d = D4[(i - 1) % 4], D4[i]
                L = rng.randint(2, 5)
                for j in range(2, 2 + L):   # wall parallel to the ring line of c_i on the far side
                    bl.add((c[0] - 2 * dp[0] - j * d[0], c[1] - 2 * dp[1] - j * d[1]))
    elif fam == 'pin2':
        bl, hole = core_pin2(c)
    else:
        bl, hole = core_pin12(c, rng.random() < 0.5)
    for _ in range(rng.randint(0, 8)):
        bl.add((rng.randrange(N), rng.randrange(N)))
    bl = {b for b in bl if 0 <= b[0] < N and 0 <= b[1] < N} - set(hole)
    g = Grid(N, N, sorted(bl))
    free = [x for x in g.free_cells() if x not in hole]
    s = rng.choice(free); t = rng.choice(hole)
    if dijkstra(g, s, t) == math.inf: return None
    return fam, g, s, t

t0 = time.time(); n_inst = 0; n_runs = 0; n_fail = 0; n_orderfail = 0; fam_count = {}
while time.time() - t0 < secs:
    inst = instance()
    if inst is None: continue
    fam, g, s, t = inst; n_inst += 1; fam_count[fam] = fam_count.get(fam, 0) + 1
    M = Model(g, s)
    st, v, _ = min_slack(g, s, t, 1.0, cap=20_000, M=M)
    if st in ('FAIL', 'LB'): n_orderfail += 1
    for w in WS:
        r, order = wa_adversary(g, s, t, w, limit=300_000, M=M); n_runs += 1
        if r == 'FAIL':
            n_fail += 1
            print('!!!!! WA* FAILURE', fam, 'N=', g.W, 'w=', w, 's=', s, 't=', t, 'blocked=', sorted(g.blocked), flush=True)
            print(grid_to_str(g, s, t)); print('order', order)
            print('reproduce:', reproduce(g, s, t, w, order), flush=True)
    if n_inst % 50 == 0:
        print(f'{time.time()-t0:.0f}s instances={n_inst} runs={n_runs} order-failable={n_orderfail} WA*fails={n_fail} {fam_count}', flush=True)
print(f'DONE instances={n_inst} runs={n_runs} order-failable={n_orderfail} WA*fails={n_fail} {fam_count}')
