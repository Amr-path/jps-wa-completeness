#!/bin/bash
# Cell-closing canonical JPS under the three other tie rules (log, fifo, lifo), same sample as run_bench.sh.
B=/path/to/jps-wa/ext/grid_benchmarks; OUT=/path/to/jps-wa/results_tie; BIN=/path/to/jps-wa/cpp/jpswa_bench
mkdir -p $OUT
run_c() { c=$1; ev=20; [ "$c" = mazes ] && ev=50
  for sc in $B/scenarios/$c/*.scen; do
    name=$(basename $sc .map.scen); map=$B/maps/$c/$name.map; [ -f "$map" ] || continue
    for tie in log fifo lifo; do for w in 1 1.5 2 3 5 10; do
      f=$OUT/$c.$name.jps_cell.$tie.w$w.csv; [ -s "$f" ] && continue
      $BIN $map $sc jps_cell --w $w --tie $tie --every $ev > $f.tmp 2>>$OUT/warnings.log && mv $f.tmp $f
    done; done
  done; echo "done $c $(date)"; }
(run_c dao; run_c sc1; run_c rooms; run_c bg512) &
(run_c mazes; run_c random; run_c da2) &
wait; echo ALLDONE
