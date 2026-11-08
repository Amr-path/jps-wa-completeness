#!/bin/bash
# v2 semantics (rays stop at t; failure = t never returned by a top-level scan).  One solver process at a time.
cd /path/to/jps-wa/verification/sat
while pgrep -f validate3.py > /dev/null; do sleep 30; done
# (1) 7x7 centre: any-order (expected SAT), then WA* for all weights
python3 run_lazy.py 7 1 1 7200 0 3 3 >> logs/queue_v2.stdout 2>&1
for w in "1 1" "3 2" "2 1" "3 1" "5 1" "10 1" "1000 1"; do set -- $w; python3 run_lazy.py 7 $1 $2 10800 1 3 3 >> logs/queue_v2.stdout 2>&1; done
# (2) 6x6 any-order, all target representatives
python3 run_lazy.py 6 1 1 7200 0 >> logs/queue_v2.stdout 2>&1
# (3) other 7x7 targets: any-order first
for t in "2 2" "2 3" "3 2" "0 0" "1 0" "2 0" "3 0" "0 1" "1 1" "2 1" "3 1" "0 2" "1 2" "0 3" "1 3"; do set -- $t; python3 run_lazy.py 7 1 1 7200 0 $1 $2 >> logs/queue_v2.stdout 2>&1; done
echo QUEUE_V2_PART1_DONE >> logs/queue_v2.stdout
