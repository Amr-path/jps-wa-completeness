#!/bin/bash
# Runs the four algorithms over MovingAI collections; every 20th scenario instance; tie = HIG.
B=/path/to/jps-wa/ext/grid_benchmarks; OUT=/path/to/jps-wa/results; BIN=/path/to/jps-wa/cpp/jpswa_bench
for c in dao da2 bg512 sc1 rooms random mazes; do
  ev=20; [ "$c" = mazes ] && ev=50
  for sc in $B/scenarios/$c/*.scen; do
    name=$(basename $sc .map.scen); map=$B/maps/$c/$name.map
    [ -f "$map" ] || { echo "missing map $map" >&2; continue; }
    for w in 1 1.5 2 3 5 10; do for a in jps_cell jps_state jps_fls wastar; do
      f=$OUT/$c.$name.$a.w$w.csv; [ -s "$f" ] && continue
      $BIN $map $sc $a --w $w --every $ev > $f.tmp 2>>$OUT/warnings.log && mv $f.tmp $f
    done; done
  done
  echo "done $c $(date)"
done
echo ALLDONE
