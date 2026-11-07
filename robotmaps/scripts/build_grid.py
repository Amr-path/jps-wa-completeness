"""Own occupancy-grid mapping from SLAM-corrected poses (counting model, as in GMapping).
usage: python3 -I build_grid.py LOG OUTSTEM [res=0.05]
Each valid beam (range < sensor max range) marks the endpoint cell as hit and every cell
traversed before it as visited-free. occupancy = hits/visits. Beams with no return
(range >= max range) are ignored. Output: OUTSTEM.pgm (ROS map_saver convention: 0 occupied
p>0.65, 254 free p<0.196, 205 unknown/unvisited) + OUTSTEM.yaml.
"""
import sys, math
sys.path.insert(0, '/home/claude/jps-wa/robotmaps/scripts')
import numpy as np
from parse_log import parse
log, out = sys.argv[1], sys.argv[2]
res = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05
poses, scans = parse(log)
# bounds from poses + valid endpoints
pts = []
for (x, y, th), (ang, r, mx) in zip(poses, scans):
    v = r < mx
    pts.append(np.c_[x + r[v]*np.cos(th+ang[v]), y + r[v]*np.sin(th+ang[v])])
pts = np.vstack(pts + [poses[:, :2]])
x0, y0 = pts.min(0) - 1.0; x1, y1 = pts.max(0) + 1.0
W = int(math.ceil((x1-x0)/res)); H = int(math.ceil((y1-y0)/res))
hits = np.zeros(H*W, np.int32); visits = np.zeros(H*W, np.int32)
step = res/2
for (x, y, th), (ang, r, mx) in zip(poses, scans):
    v = r < mx
    a = th + ang[v]; rr = r[v]
    ns = np.floor(rr/step).astype(int)            # samples strictly before endpoint
    rep = np.repeat(np.arange(len(rr)), ns)
    k = np.arange(ns.sum()) - np.repeat(np.cumsum(ns) - ns, ns)
    d = k*step
    fx = ((x + d*np.cos(a[rep]) - x0)/res).astype(int); fy = ((y + d*np.sin(a[rep]) - y0)/res).astype(int)
    ex = ((x + rr*np.cos(a) - x0)/res).astype(int); ey = ((y + rr*np.sin(a) - y0)/res).astype(int)
    hid = np.unique(ey*W + ex)
    fid = np.setdiff1d(np.unique(fy*W + fx), hid)
    visits[fid] += 1; visits[hid] += 1; hits[hid] += 1
p = np.where(visits > 0, hits/np.maximum(visits, 1), -1.0)
img = np.full(H*W, 205, np.uint8)
img[(visits > 0) & (p > 0.65)] = 0
img[(visits > 0) & (p < 0.196)] = 254
img = img.reshape(H, W)[::-1]                       # row 0 = max y (image convention)
with open(out + '.pgm', 'wb') as f:
    f.write(b'P5\n%d %d\n255\n' % (W, H)); f.write(img.tobytes())
with open(out + '.yaml', 'w') as f:
    f.write('image: %s.pgm\nresolution: %.6f\norigin: [%.6f, %.6f, 0.0]\nnegate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n'
            % (out.split('/')[-1], res, x0, y0))
print(out, W, H, 'occ', (img == 0).sum(), 'free', (img == 254).sum(), 'unk', (img == 205).sum())
