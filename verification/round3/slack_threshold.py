"""Memory-lean exact slack computation (replaces the bottleneck search of core.min_slack, which ran out of
memory at cap 3M on the climb endpoints).

decide(theta): DFS over pop orders of the faithful cell-closing model (core.Model / core._succ_state, corrected
criterion: a branch in which t receives an Open entry is a success and is pruned) in which every popped entry
satisfies f_w(popped) - min f_w(live) <= theta + EPS.  Returns ('FAIL', order) if some such order empties Open
without t ever receiving an entry, ('complete', None) if none exists, ('limit', None) if the state limit is hit.
decide(0) is the WA* adversary.

Exact keys: closed set as an integer bitmask, each live entry as (cell index, parent index, round(g*1e6));
distinct g values on these grids are sums of 1 and sqrt2 and differ by far more than 1e-6, so the rounding
is injective; float noise of order 1e-15 between equal g values is merged, which does not change behaviour
(the model compares g with a 1e-12 tolerance).

exact_min(...): find a failing order at some theta, take its actual bottleneck v (recomputed by an independent
replay), and test theta = v - 1e-6.  'complete' there proves min slack = v (violations differ by >> 1e-6).
"""
import sys, math, time, json, struct
sys.path.insert(0, '/path/to/jps-wa/verification/round3')
from core import Grid, Model, _succ_state, octile, EPS


def decide(grid, s, t, w, theta, limit=20_000_000, M=None):
    M = M or Model(grid, s)
    h = lambda c: octile(c[0], c[1], t[0], t[1])
    NN = max(grid.W, grid.H)
    assert NN <= 15
    idx = lambda c: c[1] * NN + c[0]
    MB = (NN * NN + 7) // 8
    def key(closed_mask, od):
        # packed exact key: closed bitmask, then (cell, parent or 255, round(g*1e6)) per live entry, sorted
        ent = sorted((idx(c), idx(p) if p is not None else 255, round(g * 1e6)) for c, (g, p) in od.items())
        return closed_mask.to_bytes(MB, 'little') + b''.join(struct.pack('<BBI', a, b, gg) for a, b, gg in ent)
    seen = set()
    # stack frames: (closed_set, closed_mask, od, children list, next child index)
    def children(closed, od):
        fmin = min(g + w * h(c) for c, (g, p) in od.items())
        out = []
        for x, (gx, px) in sorted(od.items()):
            if gx + w * h(x) - fmin > theta + EPS: continue
            if x == t: continue
            nc, no, _ = _succ_state(M, closed, od, x, gx, px, t)
            if t in no: continue
            out.append((x, nc, no))
        return out
    od0 = {s: (0.0, None)}
    k0 = key(0, od0); seen.add(k0)
    stack = [[frozenset(), 0, od0, children(frozenset(), od0), 0]]
    path = []
    n = 1
    while stack:
        fr = stack[-1]
        if fr[4] >= len(fr[3]):
            stack.pop()
            if path: path.pop()
            continue
        x, nc, no = fr[3][fr[4]]; fr[4] += 1
        mask = fr[1] | (1 << idx(x))
        k = key(mask, no)
        if k in seen: continue
        seen.add(k); n += 1
        if n > limit: return 'limit', None, n
        path.append(x)
        if not no:
            return 'FAIL', list(path), n
        stack.append([nc, mask, no, children(nc, no), 0])
    return 'complete', None, n


def replay(grid, s, t, w, order):
    """Independent replay of a pop order with the reference successor/jump code (core.Model): checks legality
    (popped cell has a live entry), that t never receives an entry, that Open ends empty; returns the bottleneck."""
    M = Model(grid, s)
    h = lambda c: octile(c[0], c[1], t[0], t[1])
    od = {s: (0.0, None)}; closed = set(); b = 0.0
    for x in order:
        assert x in od, f'{x} popped without a live entry'
        gx, px = od[x]
        fmin = min(g + w * h(c) for c, (g, p) in od.items())
        b = max(b, gx + w * h(x) - fmin)
        jps, _ = M.expand(x, M.dir_from(x, px), t)
        closed.add(x); del od[x]
        for j, c in jps:
            if j in closed: continue
            if gx + c < od.get(j, (math.inf,))[0] - 1e-12: od[j] = (gx + c, x)
        assert t not in od, 't received an entry'
    assert not od, 'Open not empty at the end'
    return b


def exact_min(grid, s, t, w, theta0, step, limit, log):
    """theta0: a value known to be a valid lower bound (or 0).  Increase theta by `step` until a failing order is
    found, then tighten."""
    theta = theta0
    while True:
        t0 = time.time(); st, order, n = decide(grid, s, t, w, theta, limit)
        log(f'   decide(theta={theta:.6f}) -> {st}  states {n}  {time.time()-t0:.0f}s')
        if st == 'limit': return 'limit', theta
        if st == 'FAIL': break
        theta += step
    while True:
        v = replay(grid, s, t, w, order)
        log(f'   failing order of bottleneck {v:.6f} (replayed), length {len(order)}')
        t0 = time.time(); st, o2, n = decide(grid, s, t, w, v - 1e-6, limit)
        log(f'   decide(theta={v - 1e-6:.6f}) -> {st}  states {n}  {time.time()-t0:.0f}s')
        if st == 'complete': return 'exact', v, order
        if st == 'limit': return 'upper', v, order
        order = o2


if __name__ == '__main__':
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else 20_000_000
    out = open('/path/to/jps-wa/verification/round3/logs_v2/exact_slacks3.log', 'a')
    def log(*a):
        print(*a, flush=True); print(*a, file=out, flush=True)
    pin = [(2, 3), (5, 2), (6, 5), (3, 6)]
    cands = [dict(name='pinwheel', w=1.0, N=9, s=(1, 1), t=(4, 4), bl=pin, lb=0.0),
             dict(name='pinwheel', w=2.0, N=9, s=(1, 1), t=(4, 4), bl=pin, lb=0.0)]
    eps = json.load(open('/path/to/jps-wa/verification/round3/logs_v2/climb_endpoints.json'))
    which = sys.argv[2].split(',') if len(sys.argv) > 2 else ['climb1', 'climb7', 'climb2', 'climb4', 'climb3', 'climb6']
    for nm in which:
        o = [e for e in eps if e['name'] == nm][0]; o['lb'] = o['reported']   # valid lower bound: exact (FAIL) or cap-hit LB
        cands.append(o)
    log(f'=== exact slacks, limit {lim}, {time.ctime()}')
    for c in cands:
        g = Grid(c['N'], c['N'], [tuple(b) for b in c['bl']]); s, t, w = tuple(c['s']), tuple(c['t']), c['w']
        log(f"{c['name']} w={w} N={c['N']} s={s} t={t} |blocked|={len(c['bl'])}")
        t0 = time.time(); st, _, n = decide(g, s, t, w, 0.0, lim)
        log(f'   WA* adversary (theta=0): {st}  states {n}  {time.time()-t0:.0f}s')
        step = 0.5 if w < 100 else 0.5 * w
        r = exact_min(g, s, t, w, c['lb'], step, lim, log)
        log(f"   RESULT {c['name']} w={w}: {r[0]} {r[1]!r}")
    log('EXACT_SLACKS3_DONE')
