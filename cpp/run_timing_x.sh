#!/bin/bash
# Exact-arithmetic version (jpswa_exact).
# Timing run for the running-time table (tab:time): every 100th instance, w in {1,2,10}, five repetitions; within a map and weight the
# --timing 1: untimed warm-up search per process, no optimum recomputation between timed searches.
# four algorithms run  in an order rotated by repetition. One process at a time, pinned to one core.
B=/home/claude/jps-wa/ext/grid_benchmarks; OUT=/home/claude/jps-wa/results_time_x; BIN=/home/claude/jps-wa/cpp/jpswa_exact
mkdir -p $OUT; ALGS=(jps_cell jps_state jps_fls wastar)
for c in dao da2 bg512 sc1 rooms random mazes; do
  for sc in $B/scenarios/$c/*.scen; do
    name=$(basename $sc .map.scen); map=$B/maps/$c/$name.map; [ -f "$map" ] || continue
    for w in 1 2 10; do for r in 0 1 2 3 4; do for k in 0 1 2 3; do
      a=${ALGS[$(( (k + r) % 4 ))]}; f=$OUT/$c.$name.$a.w$w.r$r.csv; [ -s "$f" ] && continue
      taskset -c 1 $BIN $map $sc $a --w $w --every 100 --timing 1 > $f.tmp 2>/dev/null && mv $f.tmp $f
    done; done; done
  done; echo "done $c $(date)"
done; echo ALLDONE
