#!/bin/bash
cd /path/to/jps-wa/verification/round3
for a in "exh 7 1" "exh 9 1" "designed" "exh 8 1 pin2"; do
  set -- $a; tag=$(echo $a | tr ' ' '_'); grep -q DONE logs_v2/rerun_tol_$tag.log 2>/dev/null && continue
  python3 rerun_tol.py $a
done
