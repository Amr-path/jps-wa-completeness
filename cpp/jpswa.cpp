// jpswa.cpp -- canonical JPS + Weighted A* without re-expansion: empirical bounded-suboptimality tester.
// Independent implementation from specification. C++17.  Compile: g++ -O2 -std=c++17 -fopenmp -o jpswa jpswa.cpp
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <cstdint>
#include <vector>
#include <string>
#include <algorithm>
#include <chrono>
#include <random>
#include <fstream>
#include <sstream>
#ifdef _OPENMP
#include <omp.h>
#endif

static const double SQ2 = 1.4142135623730951;
static const double INF = 1e100;
static const int DX[8] = {1, -1, 0, 0, 1, 1, -1, -1};
static const int DY[8] = {0, 0, 1, -1, 1, -1, 1, -1};

static inline double octile(int dx, int dy) {
    dx = std::abs(dx); dy = std::abs(dy);
    return (dx > dy) ? dx + (SQ2 - 1) * dy : dy + (SQ2 - 1) * dx;
}

enum Tie { HIG = 0, LOG = 1, FIFO = 2, LIFO = 3 };
static const char* TIENAME[4] = {"HIG", "LOG", "FIFO", "LIFO"};

// ---------------- grid ----------------
struct Grid {
    int W, H;
    std::vector<uint8_t> free_;
    Grid(int w = 1, int h = 1) : W(w), H(h), free_(w * h, 1) {}
    inline int id(int x, int y) const { return y * W + x; }
    inline bool in(int x, int y) const { return x >= 0 && y >= 0 && x < W && y < H; }
    inline bool fr(int x, int y) const { return in(x, y) && free_[id(x, y)]; }
    inline bool legal(int x, int y, int dx, int dy) const {
        if (!fr(x + dx, y + dy)) return false;
        if (dx && dy) return fr(x + dx, y) && fr(x, y + dy);
        return true;
    }
};

// ---------------- open list: binary heap with selectable tie-breaking ----------------
struct Entry { double f, g; long seq; int id; };

struct Heap {
    std::vector<Entry> a;
    Tie tie = HIG;
    long seqc = 0;
    // returns true if x should be popped before y
    inline bool before(const Entry& x, const Entry& y) const {
        if (std::fabs(x.f - y.f) > 1e-9) return x.f < y.f;
        switch (tie) {
            case HIG: if (std::fabs(x.g - y.g) > 1e-9) return x.g > y.g; return x.seq < y.seq;
            case LOG: if (std::fabs(x.g - y.g) > 1e-9) return x.g < y.g; return x.seq < y.seq;
            case FIFO: return x.seq < y.seq;
            case LIFO: return x.seq > y.seq;
        }
        return x.seq < y.seq;
    }
    void clear() { a.clear(); seqc = 0; }
    bool empty() const { return a.empty(); }
    void push(double f, double g, int id) {
        Entry e{f, g, seqc++, id};
        a.push_back(e);
        size_t i = a.size() - 1;
        while (i > 0) {
            size_t p = (i - 1) / 2;
            if (before(a[i], a[p])) { std::swap(a[i], a[p]); i = p; } else break;
        }
    }
    Entry pop() {
        Entry top = a[0];
        a[0] = a.back(); a.pop_back();
        size_t n = a.size(), i = 0;
        while (true) {
            size_t l = 2 * i + 1, r = l + 1, b = i;
            if (l < n && before(a[l], a[b])) b = l;
            if (r < n && before(a[r], a[b])) b = r;
            if (b == i) break;
            std::swap(a[i], a[b]); i = b;
        }
        return top;
    }
};

// ---------------- Dijkstra oracle (all shortest costs from one source) ----------------
struct Dijkstra {
    std::vector<double> dist;
    std::vector<uint8_t> closed;
    Heap open;
    void run(const Grid& g, int sx, int sy) {
        int N = g.W * g.H;
        dist.assign(N, INF); closed.assign(N, 0); open.clear(); open.tie = FIFO;
        int s = g.id(sx, sy); dist[s] = 0; open.push(0, 0, s);
        while (!open.empty()) {
            Entry e = open.pop();
            int n = e.id;
            if (closed[n] || e.g > dist[n]) continue;
            closed[n] = 1;
            int x = n % g.W, y = n / g.W;
            for (int k = 0; k < 8; k++) {
                if (!g.legal(x, y, DX[k], DY[k])) continue;
                int m = g.id(x + DX[k], y + DY[k]);
                double ng = e.g + ((DX[k] && DY[k]) ? SQ2 : 1.0);
                if (ng < dist[m] - 1e-12) { dist[m] = ng; open.push(ng, ng, m); }
            }
        }
    }
};

// ---------------- expansion trace (for `one` mode) ----------------
struct TraceRec { int x, y, dx, dy; double g; };

// ---------------- canonical JPS + WA* without re-expansion ----------------
struct JPSWA {
    const Grid* g = nullptr;
    int gx = 0, gy = 0;
    std::vector<double> gv;
    std::vector<int> par;
    std::vector<uint8_t> closed;
    Heap open;
    long expanded = 0;
    bool trace = false;
    std::vector<TraceRec> tr;

    inline bool blocked(int x, int y) const { return !g->fr(x, y); }
    inline bool has_forced(int x, int y, int dx, int dy) const {
        if (dx) return (blocked(x - dx, y + 1) && g->fr(x, y + 1)) || (blocked(x - dx, y - 1) && g->fr(x, y - 1));
        return (blocked(x + 1, y - dy) && g->fr(x + 1, y)) || (blocked(x - 1, y - dy) && g->fr(x - 1, y));
    }
    bool jump(int x, int y, int dx, int dy, double gg, int& jx, int& jy, double& jg) const {
        while (true) {
            if (!g->legal(x, y, dx, dy)) return false;
            x += dx; y += dy; gg += (dx && dy) ? SQ2 : 1.0;
            if (x == gx && y == gy) { jx = x; jy = y; jg = gg; return true; }
            if (dx && dy) {
                int a, b; double c;
                if (jump(x, y, dx, 0, gg, a, b, c) || jump(x, y, 0, dy, gg, a, b, c)) { jx = x; jy = y; jg = gg; return true; }
            } else {
                if (has_forced(x, y, dx, dy)) { jx = x; jy = y; jg = gg; return true; }
            }
        }
    }
    int dirs(int x, int y, int dx, int dy, int* ox, int* oy) const {
        int n = 0;
        if (!dx && !dy) { for (int k = 0; k < 8; k++) { ox[n] = DX[k]; oy[n] = DY[k]; n++; } return n; }
        if (dx && dy) { ox[n]=dx; oy[n]=dy; n++; ox[n]=dx; oy[n]=0; n++; ox[n]=0; oy[n]=dy; n++; return n; }
        ox[n]=dx; oy[n]=dy; n++;
        if (dx) {
            if (blocked(x - dx, y + 1) && g->fr(x, y + 1)) { ox[n]=0; oy[n]=1; n++; ox[n]=dx; oy[n]=1; n++; }
            if (blocked(x - dx, y - 1) && g->fr(x, y - 1)) { ox[n]=0; oy[n]=-1; n++; ox[n]=dx; oy[n]=-1; n++; }
        } else {
            if (blocked(x + 1, y - dy) && g->fr(x + 1, y)) { ox[n]=1; oy[n]=0; n++; ox[n]=1; oy[n]=dy; n++; }
            if (blocked(x - 1, y - dy) && g->fr(x - 1, y)) { ox[n]=-1; oy[n]=0; n++; ox[n]=-1; oy[n]=dy; n++; }
        }
        return n;
    }
    // Returns cost (INF if open runs empty).
    double search(const Grid& grid, int sx, int sy, int tx, int ty, double w, Tie tie) {
        g = &grid; gx = tx; gy = ty;
        int N = grid.W * grid.H;
        gv.assign(N, INF); par.assign(N, -1); closed.assign(N, 0);
        open.clear(); open.tie = tie; expanded = 0; tr.clear();
        int s = grid.id(sx, sy), t = grid.id(tx, ty);
        gv[s] = 0; open.push(w * octile(sx - tx, sy - ty), 0, s);
        while (!open.empty()) {
            Entry e = open.pop(); int n = e.id; double gn = e.g;
            if (closed[n] || gn > gv[n]) continue;   // stale or already closed
            closed[n] = 1; expanded++;
            int x = n % grid.W, y = n / grid.W;
            int dx = 0, dy = 0;
            if (par[n] >= 0) { int px = par[n] % grid.W, py = par[n] / grid.W; dx = (x > px) - (x < px); dy = (y > py) - (y < py); }
            if (trace) tr.push_back({x, y, dx, dy, gn});
            if (n == t) return gn;
            int ox[8], oy[8]; int nd = dirs(x, y, dx, dy, ox, oy);
            for (int i = 0; i < nd; i++) {
                int jx, jy; double jg;
                if (!jump(x, y, ox[i], oy[i], gn, jx, jy, jg)) continue;
                int jn = grid.id(jx, jy);
                if (closed[jn]) continue;            // no re-expansion: ignore entirely
                if (jg < gv[jn] - 1e-12) { gv[jn] = jg; par[jn] = n; open.push(jg + w * octile(jx - tx, jy - ty), jg, jn); }
            }
        }
        return INF;
    }
};

// ---------------- plain WA* without re-expansion (control) ----------------
struct WA {
    std::vector<double> gv;
    std::vector<uint8_t> closed;
    Heap open;
    long expanded = 0;
    double search(const Grid& grid, int sx, int sy, int tx, int ty, double w, Tie tie) {
        int N = grid.W * grid.H;
        gv.assign(N, INF); closed.assign(N, 0); open.clear(); open.tie = tie; expanded = 0;
        int s = grid.id(sx, sy), t = grid.id(tx, ty);
        gv[s] = 0; open.push(w * octile(sx - tx, sy - ty), 0, s);
        while (!open.empty()) {
            Entry e = open.pop(); int n = e.id; double gn = e.g;
            if (closed[n] || gn > gv[n]) continue;
            closed[n] = 1; expanded++;
            if (n == t) return gn;
            int x = n % grid.W, y = n / grid.W;
            for (int k = 0; k < 8; k++) {
                if (!grid.legal(x, y, DX[k], DY[k])) continue;
                int m = grid.id(x + DX[k], y + DY[k]);
                if (closed[m]) continue;
                double ng = gn + ((DX[k] && DY[k]) ? SQ2 : 1.0);
                if (ng < gv[m] - 1e-12) { gv[m] = ng; open.push(ng + w * octile(x + DX[k] - tx, y + DY[k] - ty), ng, m); }
            }
        }
        return INF;
    }
};

// ---------------- failure recording ----------------
static const double WS[] = {1.2, 1.5, 2, 3, 4, 8, 20};
static const int NW = 7;

struct Failure {
    int W, H; std::vector<uint8_t> free_; int sx, sy, tx, ty; double w; Tie tie; double cost, opt; bool wa_fail;
};

static std::string gridAscii(int W, int H, const std::vector<uint8_t>& fr, int sx, int sy, int tx, int ty) {
    std::string s;
    for (int y = 0; y < H; y++) {
        for (int x = 0; x < W; x++) {
            if (x == sx && y == sy) s += 'S';
            else if (x == tx && y == ty) s += 'T';
            else s += fr[y * W + x] ? '.' : '#';
        }
        s += '\n';
    }
    return s;
}

static std::string failureText(const Failure& f) {
    char buf[256];
    snprintf(buf, sizeof buf, "FAILURE %s: W=%d H=%d s=(%d,%d) t=(%d,%d) w=%g tie=%s cost=%s opt=%.6f bound=%.6f\n",
             f.wa_fail ? "[WA*]" : "[JPS+WA*]", f.W, f.H, f.sx, f.sy, f.tx, f.ty, f.w, TIENAME[f.tie],
             f.cost >= INF ? "inf" : std::to_string(f.cost).c_str(), f.opt, f.w * f.opt);
    return std::string(buf) + gridAscii(f.W, f.H, f.free_, f.sx, f.sy, f.tx, f.ty);
}

struct Stats {
    long long instances = 0;   // (grid, s, t) with finite opt
    long long runs = 0;        // JPS+WA* runs over all (w,tie)
    long long failures = 0;
    long long wa_runs = 0;
    long long wa_failures = 0;
    long long sanity_fail = 0;
    std::vector<Failure> fails;  // all (capped for memory)
    void merge(const Stats& o) {
        instances += o.instances; runs += o.runs; failures += o.failures; wa_runs += o.wa_runs;
        wa_failures += o.wa_failures; sanity_fail += o.sanity_fail;
        for (auto& f : o.fails) if (fails.size() < 200000) fails.push_back(f);
    }
};

// Tests all (s,t) pairs on one grid.  'dij' computed per source.
static void testGrid(const Grid& g, JPSWA& jps, WA& wa, Dijkstra& dij, Stats& st, bool all_pairs,
                     const std::vector<std::pair<int,int>>* pairs = nullptr) {
    int N = g.W * g.H;
    std::vector<std::pair<int,int>> plist;
    if (all_pairs) {
        for (int s = 0; s < N; s++) if (g.free_[s]) for (int t = 0; t < N; t++) if (g.free_[t] && s != t) plist.push_back({s, t});
    } else plist = *pairs;
    int lastSrc = -1;
    for (auto& pr : plist) {
        int s = pr.first, t = pr.second;
        if (s != lastSrc) { dij.run(g, s % g.W, s / g.W); lastSrc = s; }
        double opt = dij.dist[t];
        if (opt >= INF) continue;
        st.instances++;
        int sx = s % g.W, sy = s / g.W, tx = t % g.W, ty = t / g.W;
        // sanity at w=1 HIG
        double c1 = jps.search(g, sx, sy, tx, ty, 1.0, HIG);
        if (std::fabs(c1 - opt) > 1e-6) {
            st.sanity_fail++;
            if (st.fails.size() < 200000) st.fails.push_back({g.W, g.H, g.free_, sx, sy, tx, ty, 1.0, HIG, c1, opt, false});
        }
        for (int wi = 0; wi < NW; wi++) {
            double w = WS[wi];
            for (int ti = 0; ti < 4; ti++) {
                Tie tie = (Tie)ti;
                double c = jps.search(g, sx, sy, tx, ty, w, tie);
                st.runs++;
                if (c >= INF || c > w * opt + 1e-9) {
                    st.failures++;
                    if (st.fails.size() < 200000) st.fails.push_back({g.W, g.H, g.free_, sx, sy, tx, ty, w, tie, c, opt, false});
                }
                double cw = wa.search(g, sx, sy, tx, ty, w, tie);
                st.wa_runs++;
                if (cw >= INF || cw > w * opt + 1e-9) {
                    st.wa_failures++;
                    if (st.fails.size() < 200000) st.fails.push_back({g.W, g.H, g.free_, sx, sy, tx, ty, w, tie, cw, opt, true});
                }
            }
        }
    }
}

static void report(const Stats& st, const char* fname, const char* label) {
    printf("==== %s ====\n", label);
    printf("instances (grid,s,t with finite opt): %lld\n", st.instances);
    printf("JPS+WA* runs: %lld   failures: %lld\n", st.runs, st.failures);
    printf("WA*     runs: %lld   failures: %lld\n", st.wa_runs, st.wa_failures);
    printf("w=1 sanity failures: %lld\n", st.sanity_fail);
    int shown = 0;
    for (auto& f : st.fails) { if (shown >= 10) break; printf("%s\n", failureText(f).c_str()); shown++; }
    if (st.fails.size() > 10) printf("(%zu more failures in %s)\n", st.fails.size() - 10, fname);
    std::ofstream out(fname);
    for (auto& f : st.fails) out << failureText(f) << "\n";
    out.close();
    printf("wrote %zu failure records to %s\n", st.fails.size(), fname);
}

// ---------------- modes ----------------
static int modeExhaustive(int W, int H) {
    int N = W * H;
    if (N > 25) { fprintf(stderr, "W*H must be <= 25\n"); return 1; }
    uint64_t total = 1ULL << N;
    printf("exhaustive %dx%d: %llu patterns\n", W, H, (unsigned long long)total);
    auto t0 = std::chrono::steady_clock::now();
    Stats global;
    int nth = 1;
#ifdef _OPENMP
    nth = omp_get_max_threads();
#endif
    std::vector<Stats> local(nth);
    long long done = 0;
#pragma omp parallel
    {
        int tid = 0;
#ifdef _OPENMP
        tid = omp_get_thread_num();
#endif
        Grid g(W, H); JPSWA jps; WA wa; Dijkstra dij;
#pragma omp for schedule(dynamic, 4096)
        for (long long m = 0; m < (long long)total; m++) {
            for (int i = 0; i < N; i++) g.free_[i] = ((m >> i) & 1) ? 0 : 1;  // bit set = blocked
            testGrid(g, jps, wa, dij, local[tid], true);
            long long d;
#pragma omp atomic capture
            d = ++done;
            if ((d & 0xFFFF) == 0) {
                double el = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
#pragma omp critical
                { printf("progress: %lld / %llu patterns, %.1fs elapsed, est total %.1fs\n", d, (unsigned long long)total, el, el * total / d); fflush(stdout); }
            }
        }
    }
    for (auto& l : local) global.merge(l);
    double el = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    printf("elapsed %.1fs\n", el);
    char fn[64]; snprintf(fn, sizeof fn, "failures_%dx%d.txt", W, H);
    char lab[64]; snprintf(lab, sizeof lab, "exhaustive %dx%d", W, H);
    report(global, fn, lab);
    return 0;
}

static int modeRandom(unsigned seed, long ngrids) {
    std::mt19937_64 rng(seed);
    const int sizes[] = {6, 8, 10, 12, 16};
    const double dens[] = {0.2, 0.3, 0.4};
    Stats st; JPSWA jps; WA wa; Dijkstra dij;
    auto t0 = std::chrono::steady_clock::now();
    for (long gi = 0; gi < ngrids; gi++) {
        int n = sizes[rng() % 5]; double d = dens[rng() % 3];
        Grid g(n, n);
        std::uniform_real_distribution<double> U(0, 1);
        std::vector<int> fr;
        for (int i = 0; i < n * n; i++) { g.free_[i] = U(rng) < d ? 0 : 1; if (g.free_[i]) fr.push_back(i); }
        if (fr.size() < 2) continue;
        std::vector<std::pair<int,int>> pairs;
        for (int k = 0; k < 10; k++) {
            int s = fr[rng() % fr.size()], t = fr[rng() % fr.size()];
            if (s == t) { k--; continue; }
            pairs.push_back({s, t});
        }
        std::sort(pairs.begin(), pairs.end());
        testGrid(g, jps, wa, dij, st, false, &pairs);
        if ((gi + 1) % 2000 == 0) { printf("random: %ld grids done, failures so far %lld\n", gi + 1, st.failures); fflush(stdout); }
    }
    double el = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    printf("elapsed %.1fs\n", el);
    char fn[64]; snprintf(fn, sizeof fn, "failures_random_%u.txt", seed);
    report(st, fn, "random");
    return 0;
}

static int modeOne(const char* path) {
    std::ifstream in(path);
    if (!in) { fprintf(stderr, "cannot open %s\n", path); return 1; }
    std::vector<std::string> rows; std::string line;
    while (std::getline(in, line)) {
        while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();
        if (line.empty()) continue;
        rows.push_back(line);
    }
    int H = rows.size(), W = 0; for (auto& r : rows) W = std::max(W, (int)r.size());
    Grid g(W, H); int sx = -1, sy = -1, tx = -1, ty = -1;
    for (int y = 0; y < H; y++) for (int x = 0; x < W; x++) {
        char c = x < (int)rows[y].size() ? rows[y][x] : '#';
        g.free_[g.id(x, y)] = (c != '#');
        if (c == 'S') { sx = x; sy = y; }
        if (c == 'T') { tx = x; ty = y; }
    }
    if (sx < 0 || tx < 0) { fprintf(stderr, "grid needs S and T\n"); return 1; }
    Dijkstra dij; dij.run(g, sx, sy); double opt = dij.dist[g.id(tx, ty)];
    printf("%s", gridAscii(W, H, g.free_, sx, sy, tx, ty).c_str());
    printf("opt = %s\n\n", opt >= INF ? "inf" : std::to_string(opt).c_str());
    JPSWA jps; jps.trace = true; WA wa;
    printf("%6s %5s %12s %12s %12s %6s %8s %8s\n", "w", "tie", "cost", "opt", "bound", "status", "exp_jps", "exp_wa");
    std::vector<std::pair<int,int>> failRuns;
    std::vector<std::vector<TraceRec>> traces;
    std::vector<double> ws2; ws2.push_back(1.0); for (int i = 0; i < NW; i++) ws2.push_back(WS[i]);
    for (size_t wi = 0; wi < ws2.size(); wi++) for (int ti = 0; ti < 4; ti++) {
        double w = ws2[wi];
        double c = jps.search(g, sx, sy, tx, ty, w, (Tie)ti);
        long ej = jps.expanded;
        double cw = wa.search(g, sx, sy, tx, ty, w, (Tie)ti);
        bool ok = !(opt < INF && (c >= INF || c > w * opt + 1e-9));
        bool okw = !(opt < INF && (cw >= INF || cw > w * opt + 1e-9));
        printf("%6g %5s %12s %12.6f %12.6f %6s %8ld %8ld%s\n", w, TIENAME[ti], c >= INF ? "inf" : std::to_string(c).c_str(),
               opt, w * opt, ok ? "ok" : "FAIL", ej, wa.expanded, okw ? "" : "  (WA* FAIL too)");
        if (!ok) traces.push_back(jps.tr), failRuns.push_back({(int)wi, ti});
    }
    for (size_t k = 0; k < failRuns.size(); k++) {
        printf("\n-- expansion trace for FAIL w=%g tie=%s (x,y) dir g --\n", ws2[failRuns[k].first], TIENAME[failRuns[k].second]);
        for (auto& r : traces[k]) printf("  (%d,%d) dir=(%+d,%+d) g=%.6f\n", r.x, r.y, r.dx, r.dy, r.g);
    }
    return 0;
}

int main(int argc, char** argv) {
    if (argc < 2) { fprintf(stderr, "usage: jpswa exhaustive W H | random seed ngrids | one file\n"); return 1; }
    std::string mode = argv[1];
    if (mode == "exhaustive" && argc >= 4) return modeExhaustive(atoi(argv[2]), atoi(argv[3]));
    if (mode == "random" && argc >= 4) return modeRandom((unsigned)atol(argv[2]), atol(argv[3]));
    if (mode == "one" && argc >= 3) return modeOne(argv[2]);
    fprintf(stderr, "bad arguments\n"); return 1;
}
