"""Core WA* feasibility of the 2x2 pinwheel (design coords, y up).  Each arm i gives an upper bound U_i on
D_i = G_{i+1} - G_i (origin g-values); feasible iff sum U_i >= 0 (D_i sum to 0 around the cycle).
Arm constraints (B_i = end of rho_{i+1} from o_{i+1}, blocker on rho_i's strip, host h_i = o_i + diagonal):
 mode B: f(o_{i+1}) <= f(h_i) and f_ring(B_i) <= f(h_i)
 mode A: f_sweep(B_i) >= f(o_{i+1}) and g_ring(B_i) < g_sweep(B_i) and f_ring(B_i) <= f(h_i)"""
import math
SQ2 = math.sqrt(2)
def oct(a, b):
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1]); return max(dx, dy) + (SQ2 - 1) * min(dx, dy)
def L1(a, b): return abs(a[0] - b[0]) + abs(a[1] - b[1])
o = [(-2, -1), (0, 4), (5, 2), (3, -3)]; h = [(-1, 0), (1, 3), (4, 1), (2, -2)]; B = [(0, 0), (1, 2), (3, 1), (2, -1)]
hole = [(1, 0), (2, 0), (1, 1), (2, 1)]
for w in (1.0, 1.1, 1.2, 1.5, 2.0, 3.0, 10.0):
    for t in hole:
        Us = []
        for i in range(4):
            j = (i + 1) % 4
            cB = min(SQ2 + w * oct(h[i], t) - w * oct(o[j], t), SQ2 + w * oct(h[i], t) - L1(o[j], B[i]) - w * oct(B[i], t))
            cA = min(SQ2 + L1(h[i], B[i]) + w * oct(B[i], t) - w * oct(o[j], t), SQ2 + L1(h[i], B[i]) - L1(o[j], B[i]) - 1e-9,
                     SQ2 + w * oct(h[i], t) - L1(o[j], B[i]) - w * oct(B[i], t))
            Us.append(max(cB, cA))
        print(f'w={w:5} t={t}: U={["%.2f" % u for u in Us]} sum={sum(Us):.2f} {"FEASIBLE" if sum(Us) >= -1e-9 else "infeasible"}')
