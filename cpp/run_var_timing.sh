#!/bin/bash
# Running times on the two failing variants (jpswa_var --timing 1): every 100th instance, w in {2, 8}, cell-closing,
# state-closing and FLS, five repetitions in separate processes, algorithm order rotated by repetition, one process at
# a time pinned to one core (as run_timing_x.sh). Resumable.
B=/path/to/jps-wa/ext/grid_benchmarks; OUT=/path/to/jps-wa/results_var_time; BIN=/path/to/jps-wa/cpp/jpswa_var
mkdir -p $OUT; ALGS=(jps_cell jps_state jps_fls)
for c in dao da2 bg512 sc1 rooms random mazes; do
  for sc in $B/scenarios/$c/*.scen; do
    name=$(basename $sc .map.scen); map=$B/maps/$c/$name.map; [ -f "$map" ] || continue
    for v in bjps8 cc; do opt="--bound 8"; [ $v = cc ] && opt="--cc 1"
    for w in 2 8; do for r in 0 1 2 3 4; do for k in 0 1 2; do
      a=${ALGS[$(( (k + r) % 3 ))]}; f=$OUT/$c.$name.$v.$a.w$w.r$r.csv; [ -s "$f" ] && continue
      taskset -c 1 $BIN $map $sc $a --w $w --every 100 --timing 1 $opt > $f.tmp 2>/dev/null && mv $f.tmp $f
    done; done; done; done
  done; echo "done $c $(date)"
done; echo ALLDONE
