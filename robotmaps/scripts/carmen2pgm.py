"""Read the GRIDMAP chunk of a CARMEN v020 map file (optionally gzipped) and write a ROS-style
PGM+YAML (0 = occupied p>0.65, 254 = free 0<=p<0.196, 205 = unknown/other; p=-1 is unknown).
usage: python3 -I carmen2pgm.py IN.map OUTSTEM"""
import sys, struct, gzip
import numpy as np
fin, out = sys.argv[1], sys.argv[2]
d = open(fin, 'rb').read()
if d[:2] == b'\x1f\x8b': d = gzip.decompress(d)
i = d.find(b'CARMENMAPFILEv020') + len(b'CARMENMAPFILEv020')  # next byte = first chunk type
grid = None
while i < len(d):
    ctype = d[i]; size = struct.unpack('<i', d[i+1:i+5])[0]; desc = d[i+5:i+15]
    if ctype == 1:  # GRIDMAP
        sx, sy = struct.unpack('<ii', d[i+15:i+23]); res = struct.unpack('<f', d[i+23:i+27])[0]
        grid = np.frombuffer(d[i+27:i+27+4*sx*sy], '<f4').reshape(sx, sy)   # grid[x][y]
        break
    i += 5 + size
assert grid is not None
p = grid.T[::-1]                         # rows = y, top row = max y
img = np.full(p.shape, 205, np.uint8)
img[p > 0.65] = 0
img[(p >= 0) & (p < 0.196)] = 254
H, W = img.shape
with open(out + '.pgm', 'wb') as f:
    f.write(b'P5\n%d %d\n255\n' % (W, H)); f.write(img.tobytes())
with open(out + '.yaml', 'w') as f:
    f.write('image: %s.pgm\nresolution: %.6f\norigin: [0.0, 0.0, 0.0]\nnegate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n' % (out.split('/')[-1], res))
vals = grid[grid >= 0]
print(out, 'W', W, 'H', H, 'res %.4f' % res, 'unknown(-1)', int((grid < 0).sum()), 'p quantiles', np.percentile(vals, [1, 10, 50, 90, 99]).round(3),
      'occ', int((img == 0).sum()), 'free', int((img == 254).sum()))
