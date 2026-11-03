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

static const double SQ2 = std::sqrt(2.0);
static const double INF = std::numeric_limits<double>::infinity();

struct Map {
    int W = 0, H = 0; std::vector<uint8_t> pass;
    inline int id(int x, int y) const { return y * W + x; }
    inline bool in(int x, int y) const { return x >= 0 && y >= 0 && x < W && y < H; }
    inline bool fr(int x, int y) const { return in(x, y) && pass[id(x, y)]; }
    inline bool legal(int x, int y, int dx, int dy) const {
        if (!fr(x + dx, y + dy)) return false;
        if (dx && dy) return fr(x + dx, y) && fr(x, y + dy);
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
static inline double octile(int dx, int dy) { dx = std::abs(dx); dy = std::abs(dy); return (dx > dy) ? dx + (SQ2 - 1) * dy : dy + (SQ2 - 1) * dx; }

static const int DX[8] = {1, -1, 0, 0, 1, 1, -1, -1};
static const int DY[8] = {0, 0, 1, -1, 1, -1, 1, -1};
static inline int dirIndex(int dx, int dy) { for (int k = 0; k < 8; k++) if (DX[k] == dx && DY[k] == dy) return k; return 8; } // 8 = start

enum Tie { HIG, LOG, FIFO, LIFO };
// Priority functions Phi(h,g) (Chen & Sturtevant, IJCAI 2019). WA*: g + w h (same order as h + g/w).
// XDP: (g + (2w-1) h + sqrt((g-h)^2 + 4 w g h)) / (2w).  XUP: (g + h + sqrt((g+h)^2 + 4 w (w-1) h^2)) / (2w).
enum Prio { PWA, PXDP, PXUP };
static Prio PRIO = PWA;
static inline double prio(double g, double h, double w) {
    switch (PRIO) {
        case PXDP: return (g + (2 * w - 1) * h + std::sqrt((g - h) * (g - h) + 4 * w * g * h)) / (2 * w);
        case PXUP: return (g + h + std::sqrt((g + h) * (g + h) + 4 * w * (w - 1) * h * h)) / (2 * w);
        default:   return g + w * h;
    }
}
struct Entry { double f, g; long seq; int node; int dir; };
struct Heap {
    std::vector<Entry> h; Tie tie;
    bool before(const Entry& a, const Entry& b) const { // a pops before b?
        if (a.f != b.f) return a.f < b.f;
        switch (tie) { case HIG: return a.g > b.g; case LOG: return a.g < b.g; case FIFO: return a.seq < b.seq; default: return a.seq > b.seq; }
    }
    void push(Entry e) { h.push_back(e); size_t i = h.size() - 1; while (i) { size_t p = (i - 1) / 2; if (before(h[i], h[p])) { std::swap(h[i], h[p]); i = p; } else break; } }
    Entry pop() { Entry e = h[0]; h[0] = h.back(); h.pop_back(); size_t i = 0, n = h.size(); while (true) { size_t l = 2 * i + 1, r = l + 1, b = i; if (l < n && before(h[l], h[b])) b = l; if (r < n && before(h[r], h[b])) b = r; if (b == i) break; std::swap(h[i], h[b]); i = b; } return e; }
    bool empty() const { return h.empty(); }
    const Entry& top() const { return h[0]; }
};

struct Stats { double cost = INF; long expanded = 0, generated = 0, scanned = 0; int maxexp = 0; };

struct JPSWA {
    const Map& m; int gx, gy; long scanned = 0;
    JPSWA(const Map& mm, int gx_, int gy_) : m(mm), gx(gx_), gy(gy_) {}
    inline bool blocked(int x, int y) const { return !m.fr(x, y); }
    inline bool has_forced(int x, int y, int dx, int dy) const {
        if (dx) return (blocked(x - dx, y + 1) && m.fr(x, y + 1)) || (blocked(x - dx, y - 1) && m.fr(x, y - 1));
        return (blocked(x + 1, y - dy) && m.fr(x + 1, y)) || (blocked(x - 1, y - dy) && m.fr(x - 1, y));
    }
    bool jump(int x, int y, int dx, int dy, double gg, int& jx, int& jy, double& jg) {
        while (true) {
            if (!m.legal(x, y, dx, dy)) return false;
            x += dx; y += dy; gg += (dx && dy) ? SQ2 : 1.0; scanned++;
            if (x == gx && y == gy) { jx = x; jy = y; jg = gg; return true; }
            if (dx && dy) { int a, b; double c; if (jump(x, y, dx, 0, gg, a, b, c) || jump(x, y, 0, dy, gg, a, b, c)) { jx = x; jy = y; jg = gg; return true; } }
            else if (has_forced(x, y, dx, dy)) { jx = x; jy = y; jg = gg; return true; }
        }
    }
    int dirs(int x, int y, int dx, int dy, int* ox, int* oy) {
        int n = 0;
        if (!dx && !dy) { for (int k = 0; k < 8; k++) { ox[n] = DX[k]; oy[n] = DY[k]; n++; } return n; }
        if (dx && dy) { ox[n]=dx; oy[n]=dy; n++; ox[n]=dx; oy[n]=0; n++; ox[n]=0; oy[n]=dy; n++; return n; }
        ox[n]=dx; oy[n]=dy; n++;
        if (dx) { if (blocked(x - dx, y + 1) && m.fr(x, y + 1)) { ox[n]=0; oy[n]=1; n++; ox[n]=dx; oy[n]=1; n++; }
                  if (blocked(x - dx, y - 1) && m.fr(x, y - 1)) { ox[n]=0; oy[n]=-1; n++; ox[n]=dx; oy[n]=-1; n++; } }
        else   { if (blocked(x + 1, y - dy) && m.fr(x + 1, y)) { ox[n]=1; oy[n]=0; n++; ox[n]=1; oy[n]=dy; n++; }
                 if (blocked(x - 1, y - dy) && m.fr(x - 1, y)) { ox[n]=-1; oy[n]=0; n++; ox[n]=-1; oy[n]=dy; n++; } }
        return n;
    }
    // persistent per-map buffers, reset lazily through the touched list (so per-instance cost does not
    // depend on map size)
    struct CellStates { double g[9]; uint8_t closed[9]; };  // per-cell packed state records
    static constexpr double FINF = std::numeric_limits<double>::infinity();
    std::vector<double> gcell; std::vector<CellStates> cs; std::vector<uint8_t> closedCell, expCount, expOptimal, inOpen;
    std::vector<int> touchedCell, touchedState;
    void ensure() {
        int N = m.W * m.H;
        if ((int)gcell.size() != N) { gcell.assign(N, INF); closedCell.assign(N, 0); expCount.assign(N, 0); expOptimal.assign(N, 0); inOpen.assign(N, 0);
            CellStates blank; for (int d = 0; d < 9; d++) { blank.g[d] = FINF; blank.closed[d] = 0; } cs.assign(N, blank); }
    }
    inline void touchCell(int n) { if (gcell[n] == INF && !closedCell[n] && !expCount[n] && !inOpen[n]) touchedCell.push_back(n); }
    inline void touchState(size_t k) { if (cs[k / 9].g[k % 9] == FINF && !cs[k / 9].closed[k % 9]) touchedState.push_back((int)k); }
    void reset() {
        for (int n : touchedCell) { gcell[n] = INF; closedCell[n] = 0; expCount[n] = 0; expOptimal[n] = 0; inOpen[n] = 0; }
        for (int k : touchedState) { cs[k / 9].g[k % 9] = FINF; cs[k / 9].closed[k % 9] = 0; }
        touchedCell.clear(); touchedState.clear(); scanned = 0;
    }
    // mode 0: cell closing; 1: state closing; 2: FLS (focal list, cell-level, <=2 expansions per cell)
    Stats search(int sx, int sy, double w, Tie tie, int mode) {
        ensure(); reset();
        Stats st; int s = m.id(sx, sy), t = m.id(gx, gy);
        Heap open; open.tie = tie; Heap focal; focal.tie = tie; long seq = 0;
        auto hval = [&](int x, int y) { return octile(x - gx, y - gy); };
        touchCell(s); gcell[s] = 0; if (mode == 1) { touchState((size_t)s * 9 + 8); cs[s].g[8] = 0; }
        open.push({(mode == 2 ? 0.0 : prio(0.0, hval(sx, sy), w)), 0.0, seq++, s, 8}); st.generated++;
        if (mode == 2) { inOpen[s] = 1; focal.push({w * hval(sx, sy), 0.0, seq++, s, 8}); }
        while (!open.empty()) {
            Entry e;
            if (mode == 2) {
                // FLS (Carlson, Harabor & Stuckey 2024, Alg. 1): OPEN ordered by f = g + h, FOCAL by f_w = g + w h.
                // Take from FOCAL if its top f_w <= w * (top f of OPEN), else from OPEN. A node taken from FOCAL is
                // removed from OPEN (lazily: inOpen = 0); it re-enters OPEN only when its g improves. A node enters
                // FOCAL only while not yet expanded. Hence at most two expansions per node (Lemma 1 of that paper).
                while (!focal.empty()) { const Entry& f = focal.top(); if (f.g > gcell[f.node] + 1e-12 || closedCell[f.node]) focal.pop(); else break; }
                while (!open.empty()) { const Entry& o = open.top(); if (o.g > gcell[o.node] + 1e-12 || !inOpen[o.node] || expOptimal[o.node]) open.pop(); else break; }
                if (open.empty()) break;
                if (!focal.empty() && focal.top().f <= w * open.top().f + 1e-12) { e = focal.pop(); touchCell(e.node); closedCell[e.node] = 1; inOpen[e.node] = 0; }
                else { e = open.pop(); touchCell(e.node); expOptimal[e.node] = 1; closedCell[e.node] = 1; inOpen[e.node] = 0; }
            } else {
                e = open.pop();
                if (mode == 0) { if (closedCell[e.node] || e.g > gcell[e.node] + 1e-12) continue; touchCell(e.node); closedCell[e.node] = 1; }
                else { size_t k = (size_t)e.node * 9 + e.dir; CellStates& c = cs[e.node]; if (c.closed[e.dir] || e.g > c.g[e.dir] + 1e-12) continue; touchState(k); c.closed[e.dir] = 1; }
            }
            st.expanded++; touchCell(e.node); expCount[e.node]++; st.maxexp = std::max(st.maxexp, (int)expCount[e.node]);
            if (e.node == t) { st.cost = e.g; st.scanned = scanned; return st; }
            int x = e.node % m.W, y = e.node / m.W; int dx = e.dir < 8 ? DX[e.dir] : 0, dy = e.dir < 8 ? DY[e.dir] : 0;
            int ox[8], oy[8]; int nd = dirs(x, y, dx, dy, ox, oy);
            for (int i = 0; i < nd; i++) {
                int jx, jy; double jg; int di = dirIndex(ox[i], oy[i]);
                if (!jump(x, y, ox[i], oy[i], e.g, jx, jy, jg)) continue;
                int jn = m.id(jx, jy); double hf = hval(jx, jy);
                if (mode == 0) { if (closedCell[jn]) continue; if (jg < gcell[jn] - 1e-12) { touchCell(jn); gcell[jn] = jg; open.push({prio(jg, hf, w), jg, seq++, jn, di}); st.generated++; } }
                else if (mode == 1) { size_t k = (size_t)jn * 9 + di; CellStates& c = cs[jn]; if (c.closed[di]) continue; if (jg < c.g[di] - 1e-12) { touchState(k); c.g[di] = jg; open.push({prio(jg, hf, w), jg, seq++, jn, di}); st.generated++; } }
                else { // FLS: relax into OPEN always (if improving), into FOCAL if cell not yet expanded
                    if (jg < gcell[jn] - 1e-12) { touchCell(jn); gcell[jn] = jg; inOpen[jn] = 1; open.push({jg + hf, jg, seq++, jn, di}); st.generated++; if (!closedCell[jn]) focal.push({jg + w * hf, jg, seq++, jn, di}); }
                }
            }
        }
        st.scanned = scanned; return st;
    }
};

// plain WA* on the grid, no re-expansion (control)
static Stats wastar_grid(const Map& m, int sx, int sy, int gx, int gy, double w, Tie tie) {
    Stats st; int N = m.W * m.H; int s = m.id(sx, sy), t = m.id(gx, gy);
    static std::vector<double> g; static std::vector<uint8_t> closed; static std::vector<int> touched; static const Map* lastm = nullptr;
    if (lastm != &m || (int)g.size() != N) { g.assign(N, INF); closed.assign(N, 0); touched.clear(); lastm = &m; }
    for (int n : touched) { g[n] = INF; closed[n] = 0; } touched.clear();
    auto touch = [&](int n) { if (g[n] == INF && !closed[n]) touched.push_back(n); };
    Heap open; open.tie = tie; long seq = 0;
    touch(s); g[s] = 0; open.push({prio(0.0, octile(sx - gx, sy - gy), w), 0.0, seq++, s, 8}); st.generated++;
    while (!open.empty()) {
        Entry e = open.pop(); if (closed[e.node] || e.g > g[e.node] + 1e-12) continue; touch(e.node); closed[e.node] = 1; st.expanded++;
        if (e.node == t) { st.cost = e.g; return st; }
        int x = e.node % m.W, y = e.node / m.W;
        for (int k = 0; k < 8; k++) { if (!m.legal(x, y, DX[k], DY[k])) continue; int nn = m.id(x + DX[k], y + DY[k]); if (closed[nn]) continue;
            double ng = e.g + ((DX[k] && DY[k]) ? SQ2 : 1.0); if (ng < g[nn] - 1e-12) { touch(nn); g[nn] = ng; open.push({prio(ng, octile(x + DX[k] - gx, y + DY[k] - gy), w), ng, seq++, nn, k}); st.generated++; } }
    }
    return st;
}

int main(int argc, char** argv) {
    if (argc < 4) { fprintf(stderr, "usage: jpswa_bench <map> <scen> <alg:jps_cell|jps_state|jps_fls|wastar> [--w W] [--prio wa|xdp|xup] [--tie hig|log|fifo|lifo] [--every K] [--maxinst N]\n"); return 1; }
    std::string mapfn = argv[1], scenfn = argv[2], alg = argv[3]; double w = 1.0; Tie tie = HIG; int every = 1, maxinst = 1 << 30;
    for (int i = 4; i + 1 < argc; i += 2) { std::string k = argv[i]; std::string v = argv[i + 1];
        if (k == "--w") w = atof(v.c_str()); else if (k == "--prio") PRIO = v == "xdp" ? PXDP : v == "xup" ? PXUP : PWA; else if (k == "--tie") tie = v == "log" ? LOG : v == "fifo" ? FIFO : v == "lifo" ? LIFO : HIG; else if (k == "--every") every = atoi(v.c_str()); else if (k == "--maxinst") maxinst = atoi(v.c_str()); }
    Map m; if (!load_map(mapfn, m)) { fprintf(stderr, "cannot load map\n"); return 1; }
    std::vector<Inst> insts; std::string mn; if (!load_scen(scenfn, insts, mn)) { fprintf(stderr, "cannot load scen\n"); return 1; }
    printf("id,alg,w,tie,cost,opt,ratio,bound_ok,found,expanded,generated,scanned,maxexp_cell,micros,prio\n");
    JPSWA J(m, 0, 0);
    int mode = alg == "jps_cell" ? 0 : alg == "jps_state" ? 1 : alg == "jps_fls" ? 2 : -1; int done = 0;
    for (size_t i = 0; i < insts.size() && done < maxinst; i += every) {
        const Inst& in = insts[i]; if (in.sx == in.gx && in.sy == in.gy) continue; done++;
        auto t0 = std::chrono::steady_clock::now(); Stats st;
        if (mode >= 0) { J.gx = in.gx; J.gy = in.gy; st = J.search(in.sx, in.sy, w, tie, mode); } else st = wastar_grid(m, in.sx, in.sy, in.gx, in.gy, w, tie);
        long us = std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now() - t0).count();
        // exact optimum computed here (scenario files store 4 decimals); cross-checked against the scenario value
        double opt = wastar_grid(m, in.sx, in.sy, in.gx, in.gy, 1.0, HIG).cost;
        if (std::fabs(opt - in.opt) > 1e-2) { fprintf(stderr, "warning: instance %zu scen opt %.4f vs computed %.6f\n", i, in.opt, opt); }
        bool found = st.cost < INF; bool ok = found && st.cost <= w * opt + 1e-9;
        printf("%zu,%s,%g,%d,%s,%.6f,%s,%d,%d,%ld,%ld,%ld,%d,%ld,%s\n", i, alg.c_str(), w, (int)tie, found ? std::to_string(st.cost).c_str() : "inf", opt,
               found ? std::to_string(st.cost / opt).c_str() : "inf", ok ? 1 : 0, found ? 1 : 0, st.expanded, st.generated, st.scanned, st.maxexp, us, PRIO == PXDP ? "xdp" : PRIO == PXUP ? "xup" : "wa");
    }
    return 0;
}
