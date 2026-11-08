"""Proof-checked UNSAT for one target of the N=7, w=1 WA* sweep (Section 7 / Appendix A).
1. Runs the lazy (CEGAR) loop exactly as run_lazy.py does (prebuilt base CNF, CaDiCaL 1.5.3 via PySAT) and records
   every clause added by the loop.
2. Writes the final formula F = base CNF + all added clauses (DIMACS, gzip copy kept).
3. Solves F from scratch with a standalone CaDiCaL that writes a DRAT proof, and checks the proof with drat-trim.
   The proof file is deleted after checking (it can be several GB); the verdict, sizes, times and sha256 are logged.
usage: python3 drat_run.py tx ty      (run from verification/sat; needs ../../tools/cadical/build/cadical and
                                         ../../tools/drat-trim/drat-trim)"""
import sys, os, time, json, gzip, hashlib, subprocess, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
TEST = os.environ.get('DRAT_TEST') == '1'   # self-test: check the final formula with PySAT instead of the external tools
NN = int(os.environ.get('DRAT_N', '7'))
PRE = os.environ.get('DRAT_PREBUILT', os.path.join(HERE, 'prebuilt'))
os.environ['JPS_PREBUILT'] = PRE
from lazy import LazySolver
TOOLS = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'tools'))
CADICAL = os.path.join(TOOLS, 'cadical', 'build', 'cadical')
DRATTRIM = os.path.join(TOOLS, 'drat-trim', 'drat-trim')
tx, ty = int(sys.argv[1]), int(sys.argv[2])
tag = f't{tx}{ty}'
os.makedirs(os.path.join(HERE, 'drat'), exist_ok=True)
logf = open(os.path.join(HERE, 'drat', f'drat_{tag}.log'), 'a')
def out(*a):
    print(*a, flush=True); print(*a, file=logf, flush=True)
out(f'=== N={NN} w=1 t=({tx},{ty}) {time.ctime()}')
t0 = time.time()
KW = dict(fixed_grid={(2, 3), (5, 2), (6, 5), (3, 6)}, fixed_s=(1, 1)) if os.environ.get('DRAT_PIN') else dict(sym_s=True)
L = LazySolver(NN, (tx, ty), (1, 1), wa=True, verbose=False, **KW)
added = []
emit = L.C.emit
def rec(cl):
    added.append([int(x) for x in cl]); emit(cl)
L.C.emit = rec
r = L.run(timeout=None)
out(f'lazy: {r["status"]} iters {r["iters"]} solve {r["solve"]:.0f}s stats {r["stats"]} recorded {len(added)} clauses')
assert r['status'] == 'unsat', 'expected unsat'
assert len(added) == r['stats']['added_clauses'], 'recorded clause count differs'
nv_final = L.C.nv
L.sol.delete()
# final formula
base = os.path.join(PRE, f'N{NN}_w1_1_wa_{tag}.cnf')
F = os.path.join(HERE, 'drat', f'final_{tag}.cnf')
nb = 0; nvb = 0
with open(base) as fb, open(F, 'w') as ff:
    body = []
    for line in fb:
        if line.startswith('c'): continue
        if line.startswith('p'):
            _, _, nvb, nb = line.split(); nvb, nb = int(nvb), int(nb); continue
        body.append(line)
    ff.write(f'p cnf {max(nvb, nv_final, max((abs(l) for c in added for l in c), default=0))} {nb + len(added)}\n')
    ff.writelines(body)
    for c in added: ff.write(' '.join(map(str, c)) + ' 0\n')
sha = hashlib.sha256(open(F, 'rb').read()).hexdigest()
out(f'final formula: {nb} base + {len(added)} added clauses, sha256 {sha}')
# solve with proof
if TEST:
    from pysat.formula import CNF
    from pysat.solvers import Cadical153
    with Cadical153(bootstrap_with=CNF(from_file=F).clauses) as so: out('TEST: final formula satisfiable?', so.solve())
    sys.exit(0)
P = os.path.join(HERE, 'drat', f'proof_{tag}.drat')
t1 = time.time()
rc = subprocess.run([CADICAL, '-q', F, P]).returncode
out(f'cadical exit {rc} (20 = UNSAT) in {time.time() - t1:.0f}s, proof {os.path.getsize(P) / 1e9:.2f} GB')
assert rc == 20, 'standalone CaDiCaL did not report UNSAT'
t2 = time.time()
chk = subprocess.run([DRATTRIM, F, P, '-t', '10000000'], capture_output=True, text=True)
verdict = [l for l in chk.stdout.splitlines() if l.startswith('s ')]
out(f'drat-trim {verdict} in {time.time() - t2:.0f}s')
out('drat-trim tail: ' + ' | '.join(chk.stdout.strip().splitlines()[-4:]))
os.remove(P)
with open(F, 'rb') as fi, gzip.open(F + '.gz', 'wb') as fo: shutil.copyfileobj(fi, fo)
os.remove(F)
out('RESULT ' + json.dumps({'t': [tx, ty], 'lazy': r['status'], 'cadical': rc, 'drat_trim': verdict, 'sha256': sha,
                            'total_s': round(time.time() - t0)}))
