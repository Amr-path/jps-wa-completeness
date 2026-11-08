#!/bin/bash
cd /path/to/jps-wa/verification/sat
for t in "2 2" "1 2" "0 2" "1 1" "0 1" "0 0"; do set -- $t; python3 run_lazy.py 7 1 1 7200 0 $1 $2 >> logs/queueM1.stdout 2>&1; done
echo LANE1_NOWA_DONE >> logs/queueM1.stdout
