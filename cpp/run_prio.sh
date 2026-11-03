#!/bin/bash
# XDP / XUP priority functions (Chen & Sturtevant 2019): cell-closing, state-closing and grid best-first search.
B=/home/claude/jps-wa/ext/grid_benchmarks; OUT=/home/claude/jps-wa/results_prio; BIN=/home/claude/jps-wa/cpp/jpswa_bench_prio
for c in dao da2 bg512 sc1 rooms random mazes; do
  ev=40; [ "$c" = mazes ] && ev=100
  for sc in $B/scenarios/$c/*.scen; do
    name=$(basename $sc .map.scen); map=$B/maps/$c/$name.map
    for pr in xdp xup; do for w in 1.5 2 5 10; do for a in jps_cell jps_state wastar; do
      f=$OUT/$c.$name.$a.$pr.w$w.csv; [ -s "$f" ] && continue
      $BIN $map $sc $a --w $w --prio $pr --every $ev > $f.tmp 2>/dev/null && mv $f.tmp $f
    done; done; done
  done; echo "done $c $(date)"
done; echo ALLDONE
