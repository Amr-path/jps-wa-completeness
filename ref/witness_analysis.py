"""Who covers the cells lost by a wrong-direction closing?

Run canonical JPS (no target, random order) recording, for every scan visit, (origin cell, top-level
direction, step index, cell). Build the search tree (parent = origin of the chosen entry).
For every closed x with direction dA and every lost cell c = x+e (e in succ(x,d') for some feasible d',
e not in succ(x,dA), move legal), classify the scans that visit c by the tree relation of their origin o
to x: 'self' (o==x), 'ancestor', 'descendant', 'other'; also whether o was closed before or after x.
Report frequency of classes and whether 'ancestor-or-self or arrival-segment' always suffices.
"""
import random, sys, math, time
from collections import Counter, defaultdict
from jpswa import Grid, CanonicalJPS, grid_to_str, DIRS8, SQ2


def run(grid, s, rng):
    J = CanonicalJPS(grid, s, (-99, -99), 1.0, 'hig')
    visits = defaultdict(list)          # cell -> list of (origin, topdir, order_index)
    closed = {}                          # cell -> (dir, parent, time)
    order = []
    cur = {}

    def jr(x, y, dx, dy, top):
        g = J.g
        while True:
            if not g.legal(x, y, dx, dy):
                return None
            x += dx; y += dy
            visits[(x, y)].append((cur['o'], top, cur['t']))
            if dx and dy:
                if jr(x, y, dx, 0, top) is not None or jr(x, y, 0, dy, top) is not None:
                    return (x, y)
            else:
                if J.has_forced(x, y, dx, dy):
                    return (x, y)
    pend = [(s, (0, 0), None)]
    t = 0
    while pend:
        x, d, par = pend.pop(rng.randrange(len(pend)))
        if x in closed:
            continue
        closed[x] = (d, par, t); order.append(x)
        cur['o'] = x; cur['t'] = t
        for e in J.successor_dirs(x[0], x[1], d[0], d[1]):
            y = jr(x[0], x[1], e[0], e[1], e)
            if y is not None and y not in closed:
                pend.append((y, e, x))
        t += 1
    return J, visits, closed


def ancestors(closed, x):
    out = set()
    while x is not None:
        out.add(x); x = closed[x][1]
    return out


def main(seed, n):
    rng = random.Random(seed)
    cls = Counter(); lost_total = 0; only_other = 0; only_desc = 0; examples = []
    for _ in range(n):
        W = H = rng.choice((6, 8, 10, 12)); p = rng.choice((0.2, 0.3, 0.4, 0.5))
        grid = Grid(W, H, [(x, y) for y in range(H) for x in range(W) if rng.random() < p])
        cells = grid.free_cells()
        if not cells: continue
        s = rng.choice(cells)
        for k in range(4):
            J, visits, closed = run(grid, s, rng)
            anc_cache = {}
            for x, (dA, par, tx) in closed.items():
                if x == s: continue
                succA = set(J.successor_dirs(x[0], x[1], dA[0], dA[1]))
                lost = set()
                for d2 in DIRS8:
                    if not grid.legal(x[0]-d2[0], x[1]-d2[1], d2[0], d2[1]): continue
                    for e in J.successor_dirs(x[0], x[1], d2[0], d2[1]):
                        if e not in succA and grid.legal(x[0], x[1], e[0], e[1]):
                            lost.add(e)
                if not lost: continue
                anc = anc_cache.get(x)
                if anc is None:
                    anc = ancestors(closed, x); anc_cache[x] = anc
                for e in lost:
                    c = (x[0]+e[0], x[1]+e[1])
                    lost_total += 1
                    vs = visits.get(c, [])
                    kinds = set()
                    for (o, top, to) in vs:
                        if o == x: kinds.add('self')
                        elif o in anc: kinds.add('ancestor')
                        elif x in ancestors(closed, o): kinds.add('descendant')
                        else: kinds.add('other')
                        kinds.add('before' if to < tx else 'after')
                    cls[frozenset(kinds)] += 1
                    if not (kinds & {'self', 'ancestor'}):
                        only_other += 1
                        if len(examples) < 3:
                            examples.append((grid, s, x, dA, e, c, [(o, top, to) for (o, top, to) in vs], closed))
    print(f'lost cells examined: {lost_total}')
    for k, v in cls.most_common(): print(f'  {sorted(k)}: {v}')
    print(f'lost cells visited by NO ancestor/self scan: {only_other}')
    for grid, s, x, dA, e, c, vs, closed in examples:
        print('\nexample: x', x, 'closed dir', dA, 'parent', closed[x][1], 'lost e', e, 'cell', c)
        print(' visitors:', vs)
        print(grid_to_str(grid, s, None, [c]))
        print(' closed cell marked below as * :'); print(grid_to_str(grid, s, None, [x]))


if __name__ == '__main__':
    main(int(sys.argv[1]), int(sys.argv[2]))
