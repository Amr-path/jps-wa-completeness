#!/bin/bash
# FLS (focal list search, Carlson, Harabor & Stuckey 2024) on the two failing variants of run_var.sh, same sample,
# exact arithmetic, weights 1.2, 2, 4, 8. Usage: run_var_fls.sh <collections...>. Resumable.
B=/path/to/jps-wa/ext/grid_benchmarks; BIN=/path/to/jps-wa/cpp/jpswa_var; OUT=/path/to/jps-wa/results_var; mkdir -p $OUT
for c in "$@"; do ev=20; [ "$c" = mazes ] && ev=50
  for sc in $B/scenarios/$c/*.scen; do
    name=$(basename $sc .map.scen); map=$B/maps/$c/$name.map; [ -f "$map" ] || continue
    for v in bjps8 cc; do opt="--bound 8"; [ $v = cc ] && opt="--cc 1"
      for w in 1.2 2 4 8; do a=jps_fls
        f=$OUT/$c.$name.$v.$a.w$w.csv; [ -s "$f" ] && continue
        $BIN $map $sc $a --w $w --every $ev $opt > $f.tmp 2>>$OUT/warnings.log && mv $f.tmp $f
      done; done
  done; echo "done $c $(date)"
done; echo ALLDONE
