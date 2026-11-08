#!/bin/bash
# Robot occupancy grids (robotmaps/): four real SLAM environments and 100 HouseExpo layouts, 200 instances each,
# the four algorithms with exact arithmetic, six weights. Resumable.
R=/path/to/jps-wa/robotmaps/maps; BIN=/path/to/jps-wa/cpp/jpswa_exact; OUT=/path/to/jps-wa/results_robot; mkdir -p $OUT
for set in real houseexpo; do
  for sc in $R/$set/*.map.scen; do
    name=$(basename $sc .map.scen); [ "$name" = wean5300 ] && continue; map=$R/$set/$name.map
    for w in 1 1.5 2 3 5 10; do for a in jps_cell jps_state jps_fls wastar; do
      f=$OUT/$set.$name.$a.w$w.csv; [ -s "$f" ] && continue
      $BIN $map $sc $a --w $w --every 1 > $f.tmp 2>>$OUT/warnings.log && mv $f.tmp $f
    done; done
  done; echo "done $set $(date)"
done; echo ALLDONE
