"""Convert ROS-style PGM+YAML occupancy grids to Moving AI .map + .map.scen.
usage: python3 -I to_movingai.py OUT_DIR STATS_JSON YAML [YAML ...]
Procedure (per map):
 1. occupancy p = (255-v)/255 (negate=0) or v/255 (negate=1); FREE iff p < free_thresh;
    everything else (occupied and unknown) is BLOCKED.
 2. inflate: R = floor(0.25/res + 0.5) cells; a cell becomes blocked if any blocked cell
    (or the area outside the grid) lies within Euclidean distance R (in cells, centre to centre).
 3. crop to the bounding box of the remaining free cells plus a 1-cell blocked border.
 4. write .map (type octile; '.' free, '@' blocked).
 5. largest connected free component under the no-corner-cutting 8-move rule; since a
    diagonal move requires both orthogonal neighbours free, this equals the 4-connected
    component.
 6. 200 (start, goal) pairs, start != goal, drawn uniformly from that component with
    random.Random(SEED + crc32(name)); optimal = octile cost (1, sqrt 2) under the
    no-corner-cutting rule, computed with A* (octile heuristic, consistent); bucket = floor(cost/4).
"""
import sys, os, json, math, random, zlib, heapq
import numpy as np
from scipy import ndimage
ROBOT_RADIUS = 0.25; NSCEN = 200; SEED = 20261105
SQ2 = math.sqrt(2.0)

def read_yaml(fn):
    d = {}
    for line in open(fn):
        if ':' in line:
            k, v = line.split(':', 1); d[k.strip()] = v.strip()
    return d

def read_pgm(fn):
    data = open(fn, 'rb').read()
    toks = []; i = 0
    while len(toks) < 4:
        while data[i:i+1].isspace(): i += 1
        if data[i:i+1] == b'#':
            while data[i:i+1] not in (b'\n', b''): i += 1
            continue
        j = i
        while not data[j:j+1].isspace(): j += 1
        toks.append(data[i:j]); i = j
    assert toks[0] == b'P5' and int(toks[3]) == 255
    W, H = int(toks[1]), int(toks[2])
    return np.frombuffer(data[i+1:i+1+W*H], np.uint8).reshape(H, W)

def free_mask(yfn):
    y = read_yaml(yfn)
    img = read_pgm(os.path.join(os.path.dirname(yfn), y['image']))
    p = img / 255.0 if int(y.get('negate', 0)) else (255 - img.astype(float)) / 255.0
    return p < float(y['free_thresh']), float(y['resolution'])

def inflate(free, R):
    blocked = np.pad(~free, R, constant_values=True)
    yy, xx = np.mgrid[-R:R+1, -R:R+1]
    disk = (xx*xx + yy*yy) <= R*R
    infl = ndimage.binary_dilation(blocked, structure=disk)
    return ~infl[R:-R, R:-R] if R > 0 else ~blocked

def astar(pas, W, s, g):
    gx, gy = g % W, g // W
    def h(n):
        dx = abs(n % W - gx); dy = abs(n // W - gy)
        return max(dx, dy) + (SQ2 - 1) * min(dx, dy)
    INF = float('inf'); dist = {s: 0.0}; closed = set()
    pq = [(h(s), 0.0, s)]
    while pq:
        f, d, n = heapq.heappop(pq)
        if n in closed: continue
        if n == g: return d
        closed.add(n)
        x = n % W
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            m = n + dx + dy*W
            if not pas[m]: continue
            if dx and dy:
                if not (pas[n+dx] and pas[n+dy*W]): continue
                c = d + SQ2
            else:
                c = d + 1.0
            if c < dist.get(m, INF):
                dist[m] = c; heapq.heappush(pq, (c + h(m), c, m))
    return None

def dijkstra_all(pas, W, s):
    dist = {s: 0.0}; pq = [(0.0, s)]; done = set()
    while pq:
        d, n = heapq.heappop(pq)
        if n in done: continue
        done.add(n)
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            m = n + dx + dy*W
            if not pas[m]: continue
            if dx and dy:
                if not (pas[n+dx] and pas[n+dy*W]): continue
                c = d + SQ2
            else: c = d + 1.0
            if c < dist.get(m, float('inf')):
                dist[m] = c; heapq.heappush(pq, (c, m))
    return dist

def process(yfn, outdir):
    name = os.path.basename(yfn)[:-5]
    free0, res = free_mask(yfn)
    R = int(math.floor(ROBOT_RADIUS / res + 0.5))
    free = inflate(free0, R)
    ys, xs = np.nonzero(free)
    free = free[ys.min()-1:ys.max()+2, xs.min()-1:xs.max()+2] if len(ys) else free
    # guarantee blocked border (crop margin may fall outside the array only if free touches the edge, impossible after inflation with R>=1)
    H, W = free.shape
    with open(os.path.join(outdir, name + '.map'), 'w') as f:
        f.write('type octile\nheight %d\nwidth %d\nmap\n' % (H, W))
        for row in free: f.write(''.join('.' if c else '@' for c in row) + '\n')
    lab, nlab = ndimage.label(free, structure=[[0,1,0],[1,1,1],[0,1,0]])
    sizes = np.bincount(lab.ravel()); sizes[0] = 0
    big = int(sizes.argmax()); comp = np.flatnonzero(lab.ravel() == big)
    pas = bytearray(free.ravel().astype(np.uint8).tobytes())
    rng = random.Random(SEED + zlib.crc32(name.encode()))
    rows = []
    for _ in range(NSCEN):
        while True:
            s = int(comp[rng.randrange(len(comp))]); g = int(comp[rng.randrange(len(comp))])
            if s != g: break
        c = astar(pas, W, s, g); assert c is not None
        rows.append((s % W, s // W, g % W, g // W, c))
    # independent check: full Dijkstra from 3 starts
    for sx, sy, gx, gy, c in rows[:3]:
        dd = dijkstra_all(pas, W, sy*W + sx)
        assert abs(dd[gy*W + gx] - c) < 1e-9, (name, c, dd[gy*W+gx])
    rows.sort(key=lambda t: int(t[4] // 4))
    with open(os.path.join(outdir, name + '.map.scen'), 'w') as f:
        f.write('version 1\n')
        for sx, sy, gx, gy, c in rows:
            f.write('%d\t%s.map\t%d\t%d\t%d\t%d\t%d\t%d\t%.8f\n' % (int(c // 4), name, W, H, sx, sy, gx, gy, c))
    st = dict(name=name, resolution=res, radius_cells=R, src_w=free0.shape[1], src_h=free0.shape[0],
              src_free=int(free0.sum()), width=W, height=H, free_cells=int(free.sum()),
              n_components=int(nlab), lcc_cells=int(sizes[big]), n_scen=len(rows),
              mean_cost=float(np.mean([r[4] for r in rows])), max_cost=float(max(r[4] for r in rows)))
    print(json.dumps(st), flush=True)
    return st

if __name__ == '__main__':
    outdir, statsfn = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    allst = json.load(open(statsfn)) if os.path.exists(statsfn) else {}
    for y in sys.argv[3:]:
        allst[os.path.basename(y)[:-5]] = process(y, outdir)
        json.dump(allst, open(statsfn, 'w'), indent=1)
