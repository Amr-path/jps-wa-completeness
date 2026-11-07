#!/bin/bash
# Positive control: JPS variants of Carlson, Harabor & Stuckey (SoCS 2024), BJPS (b = 8) and JPScc (corner cutting),
# with cell-closing and state-closing, exact arithmetic, at their weights 1.2, 2, 4, 8; sample of run_bench.sh. Resumable.
B=/home/claude/jps-wa/ext/grid_benchmarks; BIN=/home/claude/jps-wa/cpp/jpswa_var; OUT=/home/claude/jps-wa/results_var; mkdir -p $OUT
for c in dao da2 bg512 sc1 rooms random mazes; do ev=20; [ "$c" = mazes ] && ev=50
  for sc in $B/scenarios/$c/*.scen; do
    name=$(basename $sc .map.scen); map=$B/maps/$c/$name.map; [ -f "$map" ] || continue
    for v in bjps8 cc; do opt="--bound 8"; [ $v = cc ] && opt="--cc 1"
      for w in 1.2 2 4 8; do for a in jps_cell jps_state; do
        f=$OUT/$c.$name.$v.$a.w$w.csv; [ -s "$f" ] && continue
        $BIN $map $sc $a --w $w --every $ev $opt > $f.tmp 2>>$OUT/warnings.log && mv $f.tmp $f
      done; done; done
  done; echo "done $c $(date)"
done; echo ALLDONE
