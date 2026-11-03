"""Builds, with the cloud z3 used for all earlier runs, the CNF + metadata that LazySolver would build for
run_lazy.py 7 1 1 <tmo> 1 tx ty (args identical to LazySolver.__init__), so the Mac can skip z3."""
import pickle, subprocess, sys, os
D = '/home/claude/jps-wa/agent_math/sat/prebuilt'
for tx, ty in [(2,1),(1,3),(3,1),(0,3),(3,0),(0,0),(1,0),(0,1),(2,0),(0,2)]:
    args = dict(N=7, t=(tx, ty), w=(1, 1), wa=True, eqg=True, fixed_grid=None, fixed_s=None, sym_s=True,
                max_blocked=None, slack=(0, 0))
    b = f'{D}/N7_w1_1_wa_t{tx}{ty}'
    pickle.dump(args, open(b + '.args.pkl', 'wb'))
    r = subprocess.run([sys.executable, '/home/claude/jps-wa/agent_math/sat/cnf_build.py', b + '.args.pkl', b + '.cnf', b + '.meta.pkl'], capture_output=True, text=True)
    print(tx, ty, r.returncode, r.stdout.strip(), r.stderr[-200:], flush=True)
