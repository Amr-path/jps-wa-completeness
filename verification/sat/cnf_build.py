"""Child process: build the Encoding (lazy mode) with z3, bit-blast to CNF, write DIMACS + metadata pickle.
usage: python3 cnf_build.py <args.pkl> <out.cnf> <meta.pkl>   (isolates z3 from the long-running CaDiCaL process)"""
import sys, pickle
sys.path.insert(0, '/path/to/jps-wa/verification/sat')
import z3
from enc import Encoding, to_cnf

args = pickle.load(open(sys.argv[1], 'rb'))
g = z3.Goal()
E = Encoding(solver=g, lazy=True, **args)
clauses, nv, names = to_cnf(g)
with open(sys.argv[2], 'w') as f:
    f.write(f'p cnf {nv} {len(clauses)}\n')
    for c in clauses:
        f.write(' '.join(map(str, c)) + ' 0\n')
meta = dict(N=E.N, t=E.t, cells=E.cells, arc={k: (v[1], v[2]) for k, v in E.arc.items()}, Kwa=E.Kwa, Keq=E.Keq,
            Hs=E.Hs, H=E.H, VB=E.VB, GB=E.GB, S_FP=E.S_FP, R_FP=E.R_FP, nv=nv,
            names={n: v for n, v in names.items() if not n.startswith('k!')})
pickle.dump(meta, open(sys.argv[3], 'wb'))
print('ok', nv, len(clauses))
