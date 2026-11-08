#!/bin/bash
# Lane A: finish t=(3,3) weights, then noWA for targets in the upper-left block
cd /path/to/jps-wa/verification/sat
for w in "5 1" "10 1" "1000 1"; do set -- $w; python3 run_lazy.py 7 $1 $2 14400 1 3 3 >> logs/queue_v3a.stdout 2>&1; done
for t in "2 2" "2 3" "3 2" "1 1" "2 1" "1 2"; do set -- $t; python3 run_lazy.py 7 1 1 14400 0 $1 $2 >> logs/queue_v3a.stdout 2>&1; done
echo LANE_A_DONE >> logs/queue_v3a.stdout
