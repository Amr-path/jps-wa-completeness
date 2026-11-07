"""Rasterise a reproducible random subset of HouseExpo JSON layouts at 0.05 m/cell.
usage: python3 -I houseexpo2pgm.py JSON_DIR OUT_DIR [N=100] [SEED=20201025]
Method: the 'verts' polygon (metres) is the boundary of the free space.
 * grid covers the polygon bounding box plus a 0.5 m margin; cell (i,j) has centre
   (x0+(j+0.5)r, y1-(i+0.5)r), row 0 = max y;
 * a cell is FREE if its centre is inside the polygon (even-odd rule);
 * every cell touched by a polygon edge (edge sampled every r/8) is BLOCKED (walls);
 * everything outside the polygon is BLOCKED.
Output: <id>.pgm (254 free, 0 blocked) + <id>.yaml (ROS map_server style), plus subset.txt.
"""
import sys, os, json, random, math
import numpy as np
jdir, odir = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 100
SEED = int(sys.argv[4]) if len(sys.argv) > 4 else 20201025
r = 0.05
ids = sorted(f[:-5] for f in os.listdir(jdir) if f.endswith('.json'))
sub = random.Random(SEED).sample(ids, N)
os.makedirs(odir, exist_ok=True)
with open(os.path.join(odir, 'subset.txt'), 'w') as f:
    f.write('# HouseExpo subset: random.Random(%d).sample(sorted(all %d ids), %d)\n' % (SEED, len(ids), N))
    f.write('\n'.join(sub) + '\n')
for k, hid in enumerate(sub):
    V = np.array(json.load(open(os.path.join(jdir, hid + '.json')))['verts'], float)
    x0, y0 = V.min(0) - 0.5; x1, y1 = V.max(0) + 0.5
    W = int(math.ceil((x1 - x0) / r)); H = int(math.ceil((y1 - y0) / r))
    cx = x0 + (np.arange(W) + 0.5) * r; cy = y1 - (np.arange(H) + 0.5) * r
    X, Y = np.meshgrid(cx, cy)
    inside = np.zeros((H, W), bool)
    P, Q = V, np.roll(V, -1, axis=0)
    for (xa, ya), (xb, yb) in zip(P, Q):
        if ya == yb: continue
        cond = (ya > Y) != (yb > Y)
        xint = xa + (Y - ya) * (xb - xa) / (yb - ya)
        inside ^= cond & (X < xint)
    wall = np.zeros((H, W), bool)
    for (xa, ya), (xb, yb) in zip(P, Q):
        n = max(2, int(math.hypot(xb - xa, yb - ya) / (r / 8)) + 2)
        t = np.linspace(0, 1, n)
        jj = np.floor((xa + t * (xb - xa) - x0) / r).astype(int)
        ii = np.floor((y1 - (ya + t * (yb - ya))) / r).astype(int)
        ok = (ii >= 0) & (ii < H) & (jj >= 0) & (jj < W)
        wall[ii[ok], jj[ok]] = True
    img = np.where(inside & ~wall, 254, 0).astype(np.uint8)
    stem = os.path.join(odir, 'houseexpo_' + hid)
    with open(stem + '.pgm', 'wb') as f:
        f.write(b'P5\n%d %d\n255\n' % (W, H)); f.write(img.tobytes())
    with open(stem + '.yaml', 'w') as f:
        f.write('image: houseexpo_%s.pgm\nresolution: %.6f\norigin: [%.6f, %.6f, 0.0]\nnegate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n' % (hid, r, x0, y0))
print('wrote', len(sub), 'layouts to', odir)
