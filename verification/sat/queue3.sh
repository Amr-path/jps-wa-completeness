#!/bin/bash
# no-WA (any order) runs for the remaining 7x7 targets; an UNSAT settles all weights for that target
cd /path/to/jps-wa/verification/sat
for t in "0 0" "1 0" "2 0" "3 0" "0 1" "1 1" "2 1" "3 1" "0 2" "1 2" "0 3" "1 3"; do set -- $t; python3 run_lazy.py 7 1 1 7200 0 $1 $2 >> logs/queue3.stdout 2>&1; done
echo QUEUE_3_DONE >> logs/queue3.stdout
