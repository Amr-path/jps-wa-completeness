# Canonical JPS under Weighted A* without re-expansions — code and data

Supplementary material for *Canonical Jump Point Search under Weighted A\* without re-expansions:
completeness, bounds and the role of the closing discipline* (A. Elshahed and M. K. B. Majahar Ali,
School of Mathematical Sciences, Universiti Sains Malaysia).

The repository contains every program and log behind the numbers in the paper. The paper itself is not included.

## Layout

```
ref/                    Python reference implementation of canonical JPS (jpswa.py), corner-cutting and bounded
                        variants (dijps.py), the exhaustive order adversary (adversary.py) and its drivers
cpp/                    C++17 implementation used for the Moving AI experiments (jpswa_bench.cpp), the random-map
                        test program with four tie-breaking rules (jpswa.cpp), run scripts and table generator
agent_math/             verification scripts for the theory
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
results.tar.xz          per-instance CSV records: results/ (full sweep), results_prio/ (XDP/XUP), results_time/
                        (timing run)
```

## Setup

The scripts were run from `/home/claude/jps-wa`. To run them from another location, execute once

```
./setup_paths.sh
```

which replaces that prefix by the repository's own path in all scripts.

Requirements: Python 3.10 or later, `pip install -r requirements.txt` (z3-solver, python-sat; only the SAT part
needs them), g++ with C++17 (and OpenMP for `jpswa.cpp`).

```
g++ -O2 -std=c++17 -o cpp/jpswa_bench cpp/jpswa_bench.cpp
cp cpp/jpswa_bench cpp/jpswa_bench_prio
g++ -O2 -std=c++17 -fopenmp -o cpp/jpswa cpp/jpswa.cpp
tar xJf results.tar.xz
```

The Moving AI benchmark maps and scenarios (https://movingai.com/benchmarks/grids.html) are not redistributed; place
them under `ext/grid_benchmarks/maps/<collection>/` and `ext/grid_benchmarks/scenarios/<collection>/`.

## Where each result comes from

| Paper | Programs | Logs / data |
|---|---|---|
| Lemma 4.1 (J contains an optimal path), computer check of both halves of the proof | `agent_math/round5/lemma_jpath_test.py` | `agent_math/round5/lemma_jpath_*.log` |
| Thm 4.2, check of the optimal path in J | `cpp/jpswa_bench.cpp` (state-closing, w=1) | `results/*.jps_state.w1.csv` |
| Thm 5.1, Table 1 (pinwheel run) | `agent_math/pinwheel*.py`, `agent_math/verify/replay_pinwheel.py` | script output |
| Lemma 5.3 | `agent_math/verify/lemma_frontier_test.py` | `agent_math/verify/lemma_rand_11.log` |
| Table 2 (exhaustive order adversary) | `ref/run_adv.py`, `ref/adv_struct.py`, `ref/adv_big.py` | `ref/advs_3*.log`, `ref/advst_5*.log`, `ref/advbig_7*.log` |
| Sec. 7, WA* adversary on the families | `agent_math/round3/search_designed.py`, `exhaustive_pin1.py`, `designed_recount.py` | `agent_math/round3/logs_v2/designed_*.log`, `exh_*.log` |
| Sec. 7, rerun at w=1e6 with relative tolerance; counts of instances with a failing order | `agent_math/round3/rerun_tol.py`, `rerun_tol.sh` | `agent_math/round3/logs_v2/rerun_tol_*.log` |
| Sec. 7, exact slacks | `agent_math/round3/slack_threshold.py`, `exact_examples.py`, `resume_slacks*.py`; independent check in `independent_check/` | `logs_v2/exact_examples.log`, `logs_v2/exact_slacks3.log`, `independent_check/*.out` |
| Sec. 7, hill climbs | `agent_math/round3/climb.py`, `parse_climbs.py` | `logs_v2/climb_*.log`, `logs_v2/climb_endpoints.json` |
| Sec. 7, SAT result for maps within 7x7 | `agent_math/sat/run_lazy.py` (CNFs: `cnf_build.py` / `prebuild.py`) | `agent_math/sat/logs/lazyv2_N7_*.log`, `logs/mac_run/` |
| Lemma 7.1 and invariant tests | `agent_math/round4/lemmaA_test.py`, `lemmaB_test.py` | `agent_math/round4/logs/` |
| Sec. 8, Table 3 | `cpp/run_bench.sh`, `cpp/run_prio.sh`, `cpp/run_timing.sh`, `cpp/make_tables.py` | `results.tar.xz` |

Ten of the sixteen SAT runs at w=1 were executed on a second machine with a different z3 version; their CNFs were
built beforehand with the z3 version of the other runs (`agent_math/sat/prebuild.py`, option `JPS_PREBUILT` of
`lazy.py`). The CNF construction is deterministic, and the prebuilt files can be regenerated with `prebuild.py`.

## License

MIT (see LICENSE).
