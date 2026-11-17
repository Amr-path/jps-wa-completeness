#!/bin/bash
# Running time of JPS with re-expansions against cell-closing (jpswa_exact2 --timing 1), same protocol as
# run_timing_x.sh: every 100th instance, w in {1,2,10}, five repetitions, order rotated, one core. Resumable.
B=/path/to/jps-wa/ext/grid_benchmarks; OUT=/path/to/jps-wa/results_reopen_time; BIN=/path/to/jps-wa/cpp/jpswa_exact2
mkdir -p $OUT; ALGS=(jps_cell jps_reopen)
for c in dao da2 bg512 sc1 rooms random mazes; do
  for sc in $B/scenarios/$c/*.scen; do
    name=$(basename $sc .map.scen); map=$B/maps/$c/$name.map; [ -f "$map" ] || continue
    for w in 1 2 10; do for r in 0 1 2 3 4; do for k in 0 1; do
      a=${ALGS[$(( (k + r) % 2 ))]}; f=$OUT/$c.$name.$a.w$w.r$r.csv; [ -s "$f" ] && continue
      taskset -c 1 $BIN $map $sc $a --w $w --every 100 --timing 1 > $f.tmp 2>/dev/null && mv $f.tmp $f
    done; done; done
  done; echo "done $c $(date)"
done; echo ALLDONE
