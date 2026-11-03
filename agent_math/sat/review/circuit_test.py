"""Independent unit test of the Tseitin arithmetic circuits in lazy.py (Circuits.add/sub/mulc/le_const_signed) and of
exact_sign.  For random integer inputs, the circuit is built over fresh literals, inputs are fixed by unit clauses,
CaDiCaL evaluates it, and the output literal is compared with Python integer arithmetic (two's complement, VB bits).
A wrong comparator would make lazily added WA*/eqg/min clauses too strong -> spurious UNSAT, so this is load-bearing."""
import sys, random
sys.path.insert(0, '/home/claude/jps-wa/agent_math/sat')
from pysat.solvers import Cadical153
from lazy import Circuits, exact_sign
import math

rng = random.Random(7)
VB = 34
fails = 0
for trial in range(400):
    clauses = []
    C = Circuits(0, clauses.append)
    nbits_in = 9
    xa = [C.new() for _ in range(nbits_in)]; xb = [C.new() for _ in range(nbits_in)]
    ya = [C.new() for _ in range(nbits_in)]; yb = [C.new() for _ in range(nbits_in)]
    S, R = rng.choice([(985, 1393), (2378, 3363), (5741, 8119)])
    q = rng.choice([1, 2, 3]); p = rng.choice([1, 2, 3, 5, 10, 1000])
    va = {}
    def setval(bits, v):
        for i, b in enumerate(bits):
            va[b] = (v >> i) & 1
    A, B, A2, B2 = [rng.randrange(0, 300) for _ in range(4)]
    setval(xa, A); setval(xb, B); setval(ya, A2); setval(yb, B2)
    Vx = C.add(C.mulc(xa, S, VB), C.mulc(xb, R, VB), VB)
    Vy = C.add(C.mulc(ya, S, VB), C.mulc(yb, R, VB), VB)
    Hs = rng.randrange(0, 7 * (S + R))
    Fx = C.add(C.mulc(Vx, q, VB) if q != 1 else Vx, C.const(p * Hs, VB), VB)
    qVy = C.mulc(Vy, q, VB) if q != 1 else Vy
    D = C.sub(Fx, qVy, VB)
    E = C.sub(Vx, Vy, VB)
    # pick K near the true value to exercise equality / off-by-one
    trueD = q * (S * A + R * B) + p * Hs - q * (S * A2 + R * B2)
    trueE = (S * A + R * B) - (S * A2 + R * B2)
    KD = trueD + rng.choice([-1, 0, 1, -5, 5, rng.randrange(-10 ** 6, 10 ** 6)])
    KE = trueE + rng.choice([-1, 0, 1, -3, 3, rng.randrange(-10 ** 6, 10 ** 6)])
    assert abs(trueD) < 2 ** (VB - 1) and abs(KD) < 2 ** (VB - 1) and abs(KE) < 2 ** (VB - 1)
    lD = C.le_const_signed(D, KD, VB)
    lE = C.le_const_signed(E, KE, VB)
    sol = Cadical153(bootstrap_with=clauses)
    for b, v in va.items():
        sol.add_clause([b if v else -b])
    assert sol.solve()
    m = set(l for l in sol.get_model() if l > 0)
    def ev(l):
        if isinstance(l, bool): return l
        return (abs(l) in m) == (l > 0)
    def num(bits):
        v = sum((1 << i) for i, b in enumerate(bits) if ev(b))
        return v - (1 << VB) if v >= (1 << (VB - 1)) else v
    okD = num(D) == trueD and ev(lD) == (trueD <= KD)
    okE = num(E) == trueE and ev(lE) == (trueE <= KE)
    if not (okD and okE):
        fails += 1
        print('FAIL', trial, dict(A=A, B=B, A2=A2, B2=B2, S=S, R=R, q=q, p=p, Hs=Hs, trueD=trueD, D=num(D), KD=KD, lD=ev(lD),
                                  trueE=trueE, E=num(E), KE=KE, lE=ev(lE)))
    sol.delete()
print('circuit trials 400, failures', fails)

# exact_sign vs float
bad = 0
for _ in range(20000):
    a, b = rng.randrange(-800, 801), rng.randrange(-800, 801)
    v = a + b * math.sqrt(2)
    s = exact_sign(a, b)
    if (a, b) == (0, 0):
        ok = s == 0
    else:
        ok = s == (1 if v > 0 else -1)
    bad += not ok
print('exact_sign mismatches', bad)
