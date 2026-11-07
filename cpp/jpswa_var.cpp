// jpswa_bench.cpp — canonical JPS (no corner cutting, rules of CCS Sec. 5.1) under Weighted A*
// ordering without re-expansion, on MovingAI maps. Two closing disciplines:
//   cell  : a cell is expanded once, with the arrival direction of the first popped entry (CHS 2024 setting)
//   state : a (cell, arrival direction) pair is expanded once
// Also: plain WA* on the grid (no re-expansion) as control, and FLS-style canonical JPS (focal list,
// Carlson/Harabor/Stuckey 2024) for comparison.
// Output CSV per instance: id,alg,w,tie,cost,opt,ratio,bound_ok,found,expanded,generated,scanned,maxexp_cell,micros
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <vector>
#include <string>
#include <algorithm>
#include <chrono>
#include <fstream>
#include <sstream>
#include <limits>
#include <cstdint>
#include <unordered_map>


// jpswa_var.cpp: jpswa_exact.cpp extended with two JPS variants of Carlson, Harabor & Stuckey (SoCS 2024):
// BJPS (bounded jumps, --bound b) and JPScc (corner cutting allowed: a diagonal move needs only a free target cell).
// Weights are rationals P/Q; f is stored as Q g + P h. Modes: jps_cell, jps_state, wastar (grid, same move rules).
// (based on) jpswa_exact.cpp: the algorithms of jpswa_bench.cpp (priority g + w h only) with exact arithmetic.
// A cost is a + b*sqrt(2) with integers a, b; f is stored doubled, 2f = 2g + (2w) h, with 2w an integer.
// Comparisons are exact; "improves" means strictly smaller; equal f is broken by the tie rule on exact g.
static const double SQ2 = std::sqrt(2.0);
static const double INF = std::numeric_limits<double>::infinity();
typedef long long ll;
struct C { ll a, b; };
static const ll BIG = (ll)1 << 50;
static inline int sgn(ll a, ll b) { // sign of a + b sqrt2
    if (a >= 0 && b >= 0) return (a || b) ? 1 : 0;
    if (a <= 0 && b <= 0) return -1;
    __int128 s = (__int128)a * a - (__int128)2 * b * b; // nonzero since sqrt2 irrational
    return a > 0 ? (s > 0 ? 1 : -1) : (s > 0 ? -1 : 1);
}
static inline int cmp(C x, C y) { return sgn(x.a - y.a, x.b - y.b); }
static inline bool isinf(C x) { return x.a >= BIG; }
static const C CINF = {BIG, 0};
static inline double dbl(C x) { return isinf(x) ? INF : x.a + x.b * SQ2; }
static inline C oct(int dx, int dy) { dx = std::abs(dx); dy = std::abs(dy); int mn = std::min(dx, dy), mx = std::max(dx, dy); return {mx - mn, mn}; }
static int W2 = 2; // P (numerator of w)
static int QQ = 2; // Q (denominator of w)
static bool CC = false; static int BOUND = 0;
static inline C fval(C g, C h, int w2) { return {QQ * g.a + w2 * h.a, QQ * g.b + w2 * h.b}; }
struct Map {
    int W = 0, H = 0; std::vector<uint8_t> pass;
    inline int id(int x, int y) const { return y * W + x; }
    inline bool in(int x, int y) const { return x >= 0 && y >= 0 && x < W && y < H; }
    inline bool fr(int x, int y) const { return in(x, y) && pass[id(x, y)]; }
    inline bool legal(int x, int y, int dx, int dy) const {
        if (!fr(x + dx, y + dy)) return false;
        if (dx && dy) return CC || (fr(x + dx, y) && fr(x, y + dy));
        return true;
    }
};
static bool load_map(const std::string& fn, Map& m) {
    std::ifstream f(fn); if (!f) return false;
    std::string tok; f >> tok; f >> tok; f >> tok >> m.H; f >> tok >> m.W; f >> tok;
    m.pass.assign(m.W * m.H, 0);
    for (int y = 0; y < m.H; y++) {
        std::string line;
        do { std::getline(f, line); if (!line.empty() && line.back() == '\r') line.pop_back(); } while (line.empty() && f);
        for (int x = 0; x < m.W && x < (int)line.size(); x++) m.pass[m.id(x, y)] = (line[x] == '.' || line[x] == 'G');
    }
    return true;
}
struct Inst { int sx, sy, gx, gy; double opt; };
static bool load_scen(const std::string& fn, std::vector<Inst>& v, std::string& mapname) {
    std::ifstream f(fn); if (!f) return false;
    std::string line; std::getline(f, line);
    while (std::getline(f, line)) {
        if (line.empty()) continue;
        std::istringstream ss(line); int b, w, h; Inst in; std::string mn;
        ss >> b >> mn >> w >> h >> in.sx >> in.sy >> in.gx >> in.gy >> in.opt; mapname = mn; v.push_back(in);
    }
    return true;
}

enum Tie { HIG, LOG, FIFO, LIFO };
struct Entry { C f, g; long seq; int node; int dir; };
struct Heap {
    std::vector<Entry> h; Tie tie;
    bool before(const Entry& a, const Entry& b) const {
        int c = cmp(a.f, b.f); if (c) return c < 0;
        switch (tie) { case HIG: return cmp(a.g, b.g) > 0; case LOG: return cmp(a.g, b.g) < 0; case FIFO: return a.seq < b.seq; default: return a.seq > b.seq; }
    }
    void push(Entry e) { h.push_back(e); size_t i = h.size() - 1; while (i) { size_t p = (i - 1) / 2; if (before(h[i], h[p])) { std::swap(h[i], h[p]); i = p; } else break; } }
    Entry pop() { Entry e = h[0]; h[0] = h.back(); h.pop_back(); size_t i = 0, n = h.size(); while (true) { size_t l = 2 * i + 1, r = l + 1, b = i; if (l < n && before(h[l], h[b])) b = l; if (r < n && before(h[r], h[b])) b = r; if (b == i) break; std::swap(h[i], h[b]); i = b; } return e; }
    bool empty() const { return h.empty(); }
    const Entry& top() const { return h[0]; }
};
static inline bool eq(C x, C y) { return x.a == y.a && x.b == y.b; }
static inline bool lt(C x, C y) { return cmp(x, y) < 0; }
struct Stats { C cost = CINF; long expanded = 0, generated = 0, scanned = 0; int maxexp = 0; };
static const int DX[8] = {1, -1, 0, 0, 1, 1, -1, -1};
static const int DY[8] = {0, 0, 1, -1, 1, -1, 1, -1};
static inline int dirIndex(int dx, int dy) { for (int k = 0; k < 8; k++) if (DX[k] == dx && DY[k] == dy) return k; return 8; }

struct JPSWA {
    const Map& m; int gx, gy; long scanned = 0;
    JPSWA(const Map& mm, int gx_, int gy_) : m(mm), gx(gx_), gy(gy_) {}
    inline bool blocked(int x, int y) const { return !m.fr(x, y); }
    inline bool has_forced(int x, int y, int dx, int dy) const {
        if (CC) { // Harabor & Grastien 2011 rules
            if (dx && dy) return (blocked(x - dx, y) && m.fr(x - dx, y + dy)) || (blocked(x, y - dy) && m.fr(x + dx, y - dy));
            if (dx) return (blocked(x, y + 1) && m.fr(x + dx, y + 1)) || (blocked(x, y - 1) && m.fr(x + dx, y - 1));
            return (blocked(x + 1, y) && m.fr(x + 1, y + dy)) || (blocked(x - 1, y) && m.fr(x - 1, y + dy));
        }
        if (dx) return (blocked(x - dx, y + 1) && m.fr(x, y + 1)) || (blocked(x - dx, y - 1) && m.fr(x, y - 1));
        return (blocked(x + 1, y - dy) && m.fr(x + 1, y)) || (blocked(x - 1, y - dy) && m.fr(x - 1, y));
    }
    bool jump(int x, int y, int dx, int dy, C gg, int& jx, int& jy, C& jg) {
        int steps = 0;
        while (true) {
            if (!m.legal(x, y, dx, dy)) return false;
            x += dx; y += dy; if (dx && dy) gg.b++; else gg.a++; scanned++; steps++;
            if (x == gx && y == gy) { jx = x; jy = y; jg = gg; return true; }
            if (BOUND && steps >= BOUND) { jx = x; jy = y; jg = gg; return true; } // BJPS: bounded jump
            if (dx && dy) { if (CC && has_forced(x, y, dx, dy)) { jx = x; jy = y; jg = gg; return true; }
                            int a, b; C c; if (jump(x, y, dx, 0, gg, a, b, c) || jump(x, y, 0, dy, gg, a, b, c)) { jx = x; jy = y; jg = gg; return true; } }
            else if (has_forced(x, y, dx, dy)) { jx = x; jy = y; jg = gg; return true; }
        }
    }
    int dirs(int x, int y, int dx, int dy, int* ox, int* oy) {
        int n = 0;
        if (!dx && !dy) { for (int k = 0; k < 8; k++) { ox[n] = DX[k]; oy[n] = DY[k]; n++; } return n; }
        if (dx && dy) { ox[n]=dx; oy[n]=dy; n++; ox[n]=dx; oy[n]=0; n++; ox[n]=0; oy[n]=dy; n++;
            if (CC) { if (blocked(x - dx, y)) { ox[n]=-dx; oy[n]=dy; n++; } if (blocked(x, y - dy)) { ox[n]=dx; oy[n]=-dy; n++; } }
            return n; }
        ox[n]=dx; oy[n]=dy; n++;
        if (CC) {
            if (dx) { if (blocked(x, y + 1)) { ox[n]=dx; oy[n]=1; n++; } if (blocked(x, y - 1)) { ox[n]=dx; oy[n]=-1; n++; } }
            else    { if (blocked(x + 1, y)) { ox[n]=1; oy[n]=dy; n++; } if (blocked(x - 1, y)) { ox[n]=-1; oy[n]=dy; n++; } }
            return n;
        }
        if (dx) { if (blocked(x - dx, y + 1) && m.fr(x, y + 1)) { ox[n]=0; oy[n]=1; n++; ox[n]=dx; oy[n]=1; n++; }
                  if (blocked(x - dx, y - 1) && m.fr(x, y - 1)) { ox[n]=0; oy[n]=-1; n++; ox[n]=dx; oy[n]=-1; n++; } }
        else   { if (blocked(x + 1, y - dy) && m.fr(x + 1, y)) { ox[n]=1; oy[n]=0; n++; ox[n]=1; oy[n]=dy; n++; }
                 if (blocked(x - 1, y - dy) && m.fr(x - 1, y)) { ox[n]=-1; oy[n]=0; n++; ox[n]=-1; oy[n]=dy; n++; } }
        return n;
    }
    std::vector<C> gcell; std::vector<C> gst; std::vector<uint8_t> closedCell, closedSt, expCount, expOptimal, inOpen;
    std::vector<int> touchedCell, touchedState;
    void ensure() { int N = m.W * m.H; if ((int)gcell.size() != N) { gcell.assign(N, CINF); closedCell.assign(N, 0); expCount.assign(N, 0); expOptimal.assign(N, 0); inOpen.assign(N, 0); gst.assign((size_t)N * 9, CINF); closedSt.assign((size_t)N * 9, 0); } }
    inline void touchCell(int n) { if (isinf(gcell[n]) && !closedCell[n] && !expCount[n] && !inOpen[n]) touchedCell.push_back(n); }
    inline void touchState(size_t k) { if (isinf(gst[k]) && !closedSt[k]) touchedState.push_back((int)k); }
    void reset() {
        for (int n : touchedCell) { gcell[n] = CINF; closedCell[n] = 0; expCount[n] = 0; expOptimal[n] = 0; inOpen[n] = 0; }
        for (int k : touchedState) { gst[k] = CINF; closedSt[k] = 0; }
        touchedCell.clear(); touchedState.clear(); scanned = 0;
    }
    Stats search(int sx, int sy, Tie tie, int mode) {
        ensure(); reset();
        Stats st; int s = m.id(sx, sy), t = m.id(gx, gy); const C Z = {0, 0};
        Heap open; open.tie = tie; Heap focal; focal.tie = tie; long seq = 0;
        auto hval = [&](int x, int y) { return oct(x - gx, y - gy); };
        touchCell(s); gcell[s] = Z; if (mode == 1) { touchState((size_t)s * 9 + 8); gst[(size_t)s * 9 + 8] = Z; }
        open.push({(mode == 2 ? fval(Z, hval(sx, sy), 2) : fval(Z, hval(sx, sy), W2)), Z, seq++, s, 8}); st.generated++;
        if (mode == 2) { inOpen[s] = 1; focal.push({fval(Z, hval(sx, sy), W2), Z, seq++, s, 8}); }
        while (!open.empty()) {
            Entry e;
            if (mode == 2) {
                while (!focal.empty()) { const Entry& f = focal.top(); if (!eq(f.g, gcell[f.node]) || closedCell[f.node]) focal.pop(); else break; }
                while (!open.empty()) { const Entry& o = open.top(); if (!eq(o.g, gcell[o.node]) || !inOpen[o.node] || expOptimal[o.node]) open.pop(); else break; }
                if (open.empty()) break;
                // focal top f_w <= w * (open top f):  2 f_w  vs  w * 2f  -> compare 2*(2f_w) with (2w)*(2f)
                bool takeF = false;
                if (!focal.empty()) { C a = focal.top().f, b = open.top().f; takeF = cmp({2 * a.a, 2 * a.b}, {W2 * b.a, W2 * b.b}) <= 0; }
                if (takeF) { e = focal.pop(); touchCell(e.node); closedCell[e.node] = 1; inOpen[e.node] = 0; }
                else { e = open.pop(); touchCell(e.node); expOptimal[e.node] = 1; closedCell[e.node] = 1; inOpen[e.node] = 0; }
            } else {
                e = open.pop();
                if (mode == 0) { if (closedCell[e.node] || !eq(e.g, gcell[e.node])) continue; touchCell(e.node); closedCell[e.node] = 1; }
                else { size_t k = (size_t)e.node * 9 + e.dir; if (closedSt[k] || !eq(e.g, gst[k])) continue; touchState(k); closedSt[k] = 1; }
            }
            st.expanded++; touchCell(e.node); expCount[e.node]++; st.maxexp = std::max(st.maxexp, (int)expCount[e.node]);
            if (e.node == t) { st.cost = e.g; st.scanned = scanned; return st; }
            int x = e.node % m.W, y = e.node / m.W; int dx = e.dir < 8 ? DX[e.dir] : 0, dy = e.dir < 8 ? DY[e.dir] : 0;
            int ox[8], oy[8]; int nd = dirs(x, y, dx, dy, ox, oy);
            for (int i = 0; i < nd; i++) {
                int jx, jy; C jg; int di = dirIndex(ox[i], oy[i]);
                if (!jump(x, y, ox[i], oy[i], e.g, jx, jy, jg)) continue;
                int jn = m.id(jx, jy); C hf = hval(jx, jy);
                if (mode == 0) { if (closedCell[jn]) continue; if (lt(jg, gcell[jn])) { touchCell(jn); gcell[jn] = jg; open.push({fval(jg, hf, W2), jg, seq++, jn, di}); st.generated++; } }
                else if (mode == 1) { size_t k = (size_t)jn * 9 + di; if (closedSt[k]) continue; if (lt(jg, gst[k])) { touchState(k); gst[k] = jg; open.push({fval(jg, hf, W2), jg, seq++, jn, di}); st.generated++; } }
                else { if (lt(jg, gcell[jn])) { touchCell(jn); gcell[jn] = jg; inOpen[jn] = 1; open.push({fval(jg, hf, 2), jg, seq++, jn, di}); st.generated++; if (!closedCell[jn]) focal.push({fval(jg, hf, W2), jg, seq++, jn, di}); } }
            }
        }
        st.scanned = scanned; return st;
    }
};

static Stats wastar_grid(const Map& m, int sx, int sy, int gx, int gy, int w2, Tie tie) {
    Stats st; int N = m.W * m.H; int s = m.id(sx, sy), t = m.id(gx, gy); const C Z = {0, 0};
    static std::vector<C> g; static std::vector<uint8_t> closed; static std::vector<int> touched; static const Map* lastm = nullptr;
    if (lastm != &m || (int)g.size() != N) { g.assign(N, CINF); closed.assign(N, 0); touched.clear(); lastm = &m; }
    for (int n : touched) { g[n] = CINF; closed[n] = 0; } touched.clear();
    auto touch = [&](int n) { if (isinf(g[n]) && !closed[n]) touched.push_back(n); };
    Heap open; open.tie = tie; long seq = 0;
    touch(s); g[s] = Z; open.push({fval(Z, oct(sx - gx, sy - gy), w2), Z, seq++, s, 8}); st.generated++;
    while (!open.empty()) {
        Entry e = open.pop(); if (closed[e.node] || !eq(e.g, g[e.node])) continue; touch(e.node); closed[e.node] = 1; st.expanded++;
        if (e.node == t) { st.cost = e.g; return st; }
        int x = e.node % m.W, y = e.node / m.W;
        for (int k = 0; k < 8; k++) { if (!m.legal(x, y, DX[k], DY[k])) continue; int nn = m.id(x + DX[k], y + DY[k]); if (closed[nn]) continue;
            C ng = e.g; if (DX[k] && DY[k]) ng.b++; else ng.a++;
            if (lt(ng, g[nn])) { touch(nn); g[nn] = ng; open.push({fval(ng, oct(x + DX[k] - gx, y + DY[k] - gy), w2), ng, seq++, nn, k}); st.generated++; } }
    }
    return st;
}

int main(int argc, char** argv) {
    if (argc < 4) { fprintf(stderr, "usage: jpswa_var <map> <scen> <alg:jps_cell|jps_state|jps_fls|wastar> [--w W] [--tie hig|log|fifo|lifo] [--every K] [--maxinst N] [--cc 1] [--bound b]\n"); return 1; }
    std::string mapfn = argv[1], scenfn = argv[2], alg = argv[3]; double w = 1.0; Tie tie = HIG; int every = 1, maxinst = 1 << 30; bool timing = false;
    for (int i = 4; i + 1 < argc; i += 2) { std::string k = argv[i]; std::string v = argv[i + 1];
        if (k == "--w") w = atof(v.c_str()); else if (k == "--tie") tie = v == "log" ? LOG : v == "fifo" ? FIFO : v == "lifo" ? LIFO : HIG; else if (k == "--every") every = atoi(v.c_str()); else if (k == "--maxinst") maxinst = atoi(v.c_str()); else if (k == "--timing") timing = v == "1"; }
    { int q = 1; while (q <= 1000 && std::fabs(w * q - std::lround(w * q)) > 1e-9) q++; if (q > 1000) { fprintf(stderr, "w not rational\n"); return 1; }
      W2 = (int)std::lround(w * q); QQ = q; }
    for (int i = 4; i + 1 < argc; i += 2) { std::string k = argv[i]; std::string v = argv[i + 1]; if (k == "--cc") CC = v == "1"; else if (k == "--bound") BOUND = atoi(v.c_str()); }
    if (alg == "jps_fls") { fprintf(stderr, "FLS not supported in jpswa_var\n"); return 1; }
    Map m; if (!load_map(mapfn, m)) { fprintf(stderr, "cannot load map\n"); return 1; }
    std::vector<Inst> insts; std::string mn; if (!load_scen(scenfn, insts, mn)) { fprintf(stderr, "cannot load scen\n"); return 1; }
    printf("id,alg,w,tie,cost_a,cost_b,cost,opt_a,opt_b,opt,bound_ok,found,expanded,generated,scanned,maxexp_cell,micros\n");
    JPSWA J(m, 0, 0);
    int mode = alg == "jps_cell" ? 0 : alg == "jps_state" ? 1 : alg == "jps_fls" ? 2 : -1;
    int done = 0;
    // --timing 1: one untimed warm-up search before the loop, and no optimum computation (bound_ok, opt = -1).
    if (timing) for (size_t i = 0; i < insts.size(); i += every) { const Inst& in = insts[i]; if (in.sx == in.gx && in.sy == in.gy) continue;
        if (mode >= 0) { J.gx = in.gx; J.gy = in.gy; J.search(in.sx, in.sy, tie, mode); } else wastar_grid(m, in.sx, in.sy, in.gx, in.gy, W2, tie); break; }
    for (size_t i = 0; i < insts.size() && done < maxinst; i += every) {
        const Inst& in = insts[i]; if (in.sx == in.gx && in.sy == in.gy) continue; done++;
        Stats st; auto t0 = std::chrono::steady_clock::now();
        if (mode >= 0) { J.gx = in.gx; J.gy = in.gy; st = J.search(in.sx, in.sy, tie, mode); } else st = wastar_grid(m, in.sx, in.sy, in.gx, in.gy, W2, tie);
        long us = std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now() - t0).count();
        Stats o; if (!timing) { int p = W2, q = QQ; W2 = 1; QQ = 1; o = wastar_grid(m, in.sx, in.sy, in.gx, in.gy, 1, HIG); W2 = p; QQ = q; }
        bool found = !isinf(st.cost);
        // bound: 2 cost <= (2w) opt, exactly
        bool ok = found && !isinf(o.cost) && cmp({QQ * st.cost.a, QQ * st.cost.b}, {W2 * o.cost.a, W2 * o.cost.b}) <= 0;
        printf("%zu,%s,%g,%d,%lld,%lld,%.6f,%lld,%lld,%.6f,%d,%d,%ld,%ld,%ld,%d,%ld\n", i, alg.c_str(), w, (int)tie,
               found ? st.cost.a : -1, found ? st.cost.b : -1, dbl(st.cost), isinf(o.cost) ? -1 : o.cost.a, isinf(o.cost) ? -1 : o.cost.b, dbl(o.cost),
               ok ? 1 : 0, found ? 1 : 0, st.expanded, st.generated, st.scanned, st.maxexp, us);
    }
    return 0;
}
