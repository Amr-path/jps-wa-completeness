#!/bin/bash
# Exact-arithmetic reruns (jpswa_exact). Stream "main": the four algorithms, tie rule larger g first, six weights,
# sample of run_bench.sh. Stream "tie": cell-closing under the other three tie rules. Resumable (skips finished files).
B=/home/claude/jps-wa/ext/grid_benchmarks; BIN=/home/claude/jps-wa/cpp/jpswa_exact
stream=$1
run_c() { c=$1; ev=20; [ "$c" = mazes ] && ev=50
  for sc in $B/scenarios/$c/*.scen; do
    name=$(basename $sc .map.scen); map=$B/maps/$c/$name.map; [ -f "$map" ] || continue
    for w in 1 1.5 2 3 5 10; do
      if [ "$stream" = main ]; then OUT=/home/claude/jps-wa/results_x; mkdir -p $OUT
        for a in jps_cell jps_state jps_fls wastar; do f=$OUT/$c.$name.$a.w$w.csv; [ -s "$f" ] && continue
          $BIN $map $sc $a --w $w --every $ev > $f.tmp 2>>$OUT/warnings.log && mv $f.tmp $f; done
      else OUT=/home/claude/jps-wa/results_tie_x; mkdir -p $OUT
        for tie in log fifo lifo; do f=$OUT/$c.$name.jps_cell.$tie.w$w.csv; [ -s "$f" ] && continue
          $BIN $map $sc jps_cell --w $w --tie $tie --every $ev > $f.tmp 2>>$OUT/warnings.log && mv $f.tmp $f; done
      fi
    done
  done; echo "done $stream $c $(date)"; }
for c in dao da2 bg512 sc1 rooms random mazes; do run_c $c; done; echo ALLDONE $stream
