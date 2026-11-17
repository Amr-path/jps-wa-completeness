#!/bin/bash
# Memory counters and the re-expansion baseline (jpswa_exact2) on the timing sample: every 100th instance, w in {1,2,10},
# algorithms jps_cell, jps_state, jps_fls, jps_reopen. Counts only (peak_open, records, reexp, expanded); no timing. Resumable.
B=/path/to/jps-wa/ext/grid_benchmarks; OUT=/path/to/jps-wa/results_mem; BIN=/path/to/jps-wa/cpp/jpswa_exact2; mkdir -p $OUT
for c in dao da2 bg512 sc1 rooms random mazes; do
  for sc in $B/scenarios/$c/*.scen; do
    name=$(basename $sc .map.scen); map=$B/maps/$c/$name.map; [ -f "$map" ] || continue
    for w in 1 2 10; do for a in jps_cell jps_state jps_fls jps_reopen; do
      f=$OUT/$c.$name.$a.w$w.csv; [ -s "$f" ] && continue
      $BIN $map $sc $a --w $w --every 100 > $f.tmp 2>/dev/null && mv $f.tmp $f
    done; done
  done; echo "done $c $(date)"
done; echo ALLDONE
