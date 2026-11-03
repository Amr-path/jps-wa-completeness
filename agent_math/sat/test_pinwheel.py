"""Validation (i): fixed 9x9 pinwheel, WA* constraint removed -> must be SAT and the model must replay as a failure."""
import sys, time
sys.path.insert(0, '/home/claude/jps-wa/agent_math/sat')
from enc import Encoding, check_model
import z3

blocked = {(2, 3), (5, 2), (6, 5), (3, 6)}
t0 = time.time()
E = Encoding(9, (4, 4), w=(1, 1), wa=False, fixed_grid=blocked, fixed_s=(1, 1))
print('built', time.time() - t0, 'assertions', len(E.sol.assertions()))
t0 = time.time()
r = E.sol.check()
print(r, time.time() - t0)
if r == z3.sat:
    res = E.extract(E.sol.model())
    print('order', res['order'])
    print('g', {c: round(a + b * 2 ** .5, 3) for c, (a, b) in res['g'].items()})
    ok, wa_ok, log, rep = check_model(res, 1.0)
    print("model replay faithful:", ok, "wa-consistent:", wa_ok, log[:3])
    print('reference replay:', rep)
