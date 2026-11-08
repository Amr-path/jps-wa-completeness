#!/bin/bash
# Timing run: every 100th instance, w in {1,2,10}, the four algorithms interleaved per map, machine otherwise idle.
B=/path/to/jps-wa/ext/grid_benchmarks; OUT=/path/to/jps-wa/results_time; BIN=/path/to/jps-wa/cpp/jpswa_bench
mkdir -p $OUT
for c in dao da2 bg512 sc1 rooms random mazes; do
  for sc in $B/scenarios/$c/*.scen; do
    name=$(basename $sc .map.scen); map=$B/maps/$c/$name.map
    for w in 1 2 10; do for a in jps_cell jps_state jps_fls wastar; do
      $BIN $map $sc $a --w $w --every 100 > $OUT/$c.$name.$a.w$w.csv 2>/dev/null
    done; done
  done; echo "done $c $(date)"
done; echo ALLDONE
