"""Re-run of search_designed.py seed 11 on the same 4,370 instances (the generator depends only on the seed),
recording every outcome of the WA* adversary (complete / FAIL / limit) at limit 300k, and the unrestricted
min_slack status at cap 20k (FAIL / LB / complete)."""
import sys, time, math, random, collections
sys.path.insert(0, '/path/to/jps-wa/verification/round3')
sys.argv = ['x', '11', '0']
src = open('/path/to/jps-wa/verification/round3/search_designed.py').read()
src = src[:src.index('t0 = time.time(); n_inst')]
exec(src)
cnt = collections.Counter(); ms = collections.Counter(); n_inst = 0
out = open('/path/to/jps-wa/verification/round3/logs_v2/designed_recount.log', 'w')
while n_inst < 4370:
    inst = instance()
    if inst is None: continue
    fam, g, s, t = inst; n_inst += 1
    M = Model(g, s)
    st, v, _ = min_slack(g, s, t, 1.0, cap=20_000, M=M); ms[st] += 1
    for w in WS:
        r, order = wa_adversary(g, s, t, w, limit=300_000, M=M); cnt[r] += 1
        if r != 'complete': print('NONCOMPLETE', r, fam, g.W, w, s, t, sorted(g.blocked), file=out, flush=True)
    if n_inst % 500 == 0: print(n_inst, dict(cnt), dict(ms), file=out, flush=True)
print('DONE', n_inst, dict(cnt), dict(ms), file=out, flush=True)
