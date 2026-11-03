"""Re-run min_slack with a large state cap on the lowest-lower-bound instances of gen_nonconvex (regenerated from the seed)."""
import sys, random, math, time
sys.path.insert(0, '/home/claude/jps-wa/agent_math/round4'); sys.path.insert(0, '/home/claude/jps-wa/agent_math/round3')
from gen_nonconvex import instance, SHAPES
from core import Model, min_slack, wa_adversary, reproduce
from jpswa import grid_to_str
targets = {int(a.split(':')[0]): eval(a.split(':')[1]) for a in sys.argv[1:]}   # seed:(shape,s,t)
for seed, (shape0, s0, t0) in targets.items():
    rnd = random.Random(seed)
    while True:
        shape = rnd.choice(list(SHAPES)); g, s, t, R = instance(rnd, shape)
        if (shape, s, t) == (shape0, s0, t0): break
    print(shape, s, t, 'blocked', sorted(g.blocked)); print(grid_to_str(g, s, t)); sys.stdout.flush()
    M = Model(g, s)
    for w in (1.0, 2.0, 1e6):
        t1 = time.time(); st, v, order = min_slack(g, s, t, w, cap=400_000, M=M)
        print(f'  w={w:g}: {st} slack={v:.3f} slack/w={v/w:.3f} ({time.time()-t1:.0f}s)'); sys.stdout.flush()
        if st == 'FAIL' and v < 1e-9: print('!!!!!', order, reproduce(g, s, t, w, order))
    print('  exact wa_adversary w=1:', wa_adversary(g, s, t, 1.0, M=M)[0], ' w=1e6:', wa_adversary(g, s, t, 1e6, M=M)[0]); sys.stdout.flush()
