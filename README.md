# Canonical JPS under Weighted A* without re-expansions — code and data

Supplementary material for *Canonical Jump Point Search under Weighted A\* without re-expansions:
completeness, bounds and the role of the closing discipline* (A. Elshahed and M. K. B. Majahar Ali,
School of Mathematical Sciences, Universiti Sains Malaysia).

The repository contains every program and log behind the numbers in the paper. The paper itself is not included.

## Layout

```
ref/                    Python reference implementation of canonical JPS (jpswa.py), corner-cutting and bounded
                        variants (dijps.py), the exhaustive order adversary (adversary.py) and its drivers
cpp/                    C++17 implementations: exact-arithmetic program used for all Sec. 8 runs except XDP/XUP
                        (jpswa_exact.cpp), bounded JPS and corner-cutting variants (jpswa_var.cpp), the earlier
                        double-precision program (jpswa_bench.cpp), the random-map test program with four
                        tie-breaking rules (jpswa.cpp), run scripts and analysis scripts
verification/             verification scripts for the theory
  pinwheel*.py            the counterexample of Theorem 5.1 and its replays
  verify/, verify2/       replays of the paper's claims (Fig. 1 / Table 1 run, Lemma 5.3 frontier test, ...)
  round3/                 cell-closing model with live entries (core.py), WA* adversary, exact slack computation
                          (slack_threshold.py, exact_examples.py, resume_slacks*.py), instance families
                          (search_designed.py, exhaustive_pin1.py, designed_recount.py), hill climbs (climb.py)
  round3/independent_check/  second implementation sharing no code with core.py (myjps.py, thr.py) and its outputs
  round5/                 test of the proof of the lemma that J contains an optimal path (lemma_jpath_test.py)
  round4/                 tests of Lemma 7.1 and of the stronger invariant (lemmaA_test.py, lemmaB_test.py)
  sat/                    SAT/CEGAR encoding for 7x7 maps (enc.py, lazy.py, cnf_build.py, run_lazy.py, prebuild.py),
                          validation scripts and all logs (logs/, logs/mac_run/)
bench/                  a small random benchmark map used for smoke tests
robotmaps/               robot occupancy grids (four buildings), scenario files, build scripts (see its README)
results.tar.xz          per-instance CSV records, double precision: results/ (full sweep), results_prio/
                        (XDP/XUP), results_time/ (timing run)
results_x.tar.xz        exact-arithmetic sweep, six weights, four algorithms (Table 4, Fig. 4)
results_tie_x.tar.xz    exact-arithmetic runs of cell-closing under the LOG, FIFO and LIFO tie rules
results_time_x.tar.xz   running times, five repetitions (Table 5)
results_var.tar.xz      bounded JPS and JPS with corner cutting, cell- and state-closing
results_robot.tar.xz    runs on the robot occupancy grids and the HouseExpo floor plans
```

## Setup

To configure the script paths for your environment, execute once:

```
./setup_paths.sh
```

which updates the root prefix to the repository's path across all scripts.

Requirements: Python 3.10 or later, `pip install -r requirements.txt` (z3-solver, python-sat; only the SAT part
needs them), g++ with C++17 (and OpenMP for `jpswa.cpp`).

```
g++ -O2 -std=c++17 -o cpp/jpswa_bench cpp/jpswa_bench.cpp
g++ -O2 -std=c++17 -o cpp/jpswa_exact cpp/jpswa_exact.cpp
g++ -O2 -std=c++17 -o cpp/jpswa_var cpp/jpswa_var.cpp
cp cpp/jpswa_bench cpp/jpswa_bench_prio
g++ -O2 -std=c++17 -fopenmp -o cpp/jpswa cpp/jpswa.cpp
for f in results results_x results_tie_x results_time_x results_var results_robot; do tar xJf $f.tar.xz; done
```

`results_tie.tar.xz` and `results_time3.tar.xz` hold earlier double-precision runs that the paper no longer
reports; they are kept for comparison.

The Moving AI benchmark maps and scenarios (https://movingai.com/benchmarks/grids.html) are not redistributed; place
them under `ext/grid_benchmarks/maps/<collection>/` and `ext/grid_benchmarks/scenarios/<collection>/`.

## Where each result comes from

| Paper | Programs | Logs / data |
|---|---|---|
| Lemma 4.1 (J contains an optimal path), computer check of both halves of the proof | `verification/round5/lemma_jpath_test.py` | `verification/round5/lemma_jpath_*.log` |
| Thm 4.2, check of the optimal path in J | `cpp/jpswa_bench.cpp` (state-closing, w=1) | `results/*.jps_state.w1.csv` |
| Thm 5.1, Table 1 (pinwheel run) | `verification/pinwheel*.py`, `verification/verify/replay_pinwheel.py` | script output |
| Lemma 5.3 | `verification/verify/lemma_frontier_test.py` | `verification/verify/lemma_rand_11.log` |
| Table 2 (exhaustive order adversary) | `ref/adversary.py` (random 4-6), `ref/adv_struct.py`, `ref/adv_big.py` | `ref/advs_3*.log`, `ref/advst_5*.log`, `ref/advbig_7*.log` |
| Sec. 7, WA* adversary on the families | `verification/round3/search_designed.py`, `exhaustive_pin1.py`, `designed_recount.py` | `verification/round3/logs_v2/designed_*.log`, `exh_*.log` |
| Sec. 7, rerun at w=1e6 with relative tolerance; counts of instances with a failing order | `verification/round3/rerun_tol.py`, `rerun_tol.sh` | `verification/round3/logs_v2/rerun_tol_*.log` |
| Sec. 7, exact slacks | `verification/round3/slack_threshold.py`, `exact_examples.py`, `resume_slacks*.py`; independent check in `independent_check/` | `logs_v2/exact_examples.log`, `logs_v2/exact_slacks3.log`, `independent_check/*.out` |
| Sec. 7, hill climbs | `verification/round3/climb.py`, `parse_climbs.py` | `logs_v2/climb_*.log`, `logs_v2/climb_endpoints.json` |
| Sec. 7, SAT result for maps within 7x7 | `verification/sat/run_lazy.py` (CNFs: `cnf_build.py` / `prebuild.py`) | `verification/sat/logs/lazyv2_N7_*.log`, `logs/mac_run/` |
| Sec. 7 / App. A, DRAT certificates for the 16 targets at w=1 | `verification/sat/drat_run.py` (final formula = base CNF + clauses added by the loop; standalone CaDiCaL 3.0.1 with DRAT output; drat-trim), driver `verification/sat/run_drat.sh` (copy it two levels up, next to `jps-wa/`, as in the pack it was run from), progress display `drat_progress.py` | `verification/sat/drat/drat_t*.log` (verdicts, sizes, times, sha256), `final_t*.cnf.gz` (the 16 certified formulas), `tools.txt` (solver and checker commits) |
| Sec. 7, implementation checks of Lemma 7.1, the invariant f_w <= w C*, late improving arrivals (run with PYTHONHASHSEED=0) | `verification/round4/lemmaA_test.py`, `lemmaB_test.py`, `verification/round3/lemma_tests3.py` | `verification/round4/logs/lemmaA_seed0.log`, `lemmaB_seed0.log`, `verification/round3/logs_v2/lemma_tests3_seed0.log` |
| Sec. 8, Table 4, Fig. 4, correctness and cost ratios (exact arithmetic) | `cpp/jpswa_exact.cpp`, `cpp/run_exact.sh` (main stream), `cpp/analyze_exact.py` | `results_x.tar.xz` |
| Sec. 8, correctness of cell-closing under the other three tie rules (exact arithmetic) | `cpp/run_exact.sh` (tie stream), `cpp/analyze_exact.py` | `results_tie_x.tar.xz` |
| Sec. 8, Running time (Table 5) | `cpp/run_timing_x.sh` (`jpswa_exact --timing 1`), `cpp/time_table_x.py` (optima from `results_x`) | `results_time_x.tar.xz` |
| Sec. 8, Variants that fail (bounded JPS, corner cutting) | `cpp/jpswa_var.cpp`, `cpp/run_var.sh`, `cpp/analyze_extra.py var` | `results_var.tar.xz` |
| Sec. 8, Robot occupancy grids | `robotmaps/scripts/`, `cpp/run_robot.sh`, `cpp/analyze_extra.py robot` | `robotmaps/`, `results_robot.tar.xz` |
| Sec. 8, other priority functions (XDP, XUP; double precision) | `cpp/run_prio.sh` (`jpswa_bench_prio`) | `results.tar.xz` (`results_prio/`) |

Ten of the sixteen SAT runs at w=1 were executed on a second machine with a different z3 version; their CNFs were
built beforehand with the z3 version of the other runs (`verification/sat/prebuild.py`, option `JPS_PREBUILT` of
`lazy.py`). The CNF construction is deterministic, and the prebuilt files can be regenerated with `prebuild.py`.

## License

MIT (see LICENSE).
