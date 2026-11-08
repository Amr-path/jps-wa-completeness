#!/bin/bash
cd /path/to/jps-wa/verification/sat
for w in "3 1" "5 1" "10 1" "1000 1"; do set -- $w; python3 run_lazy.py 7 $1 $2 7200 1 3 3 >> logs/queue1.stdout 2>&1; done
for w in "1 1" "3 2" "2 1" "3 1" "5 1" "10 1" "1000 1"; do set -- $w; python3 run_lazy.py 7 $1 $2 7200 1 2 2 >> logs/queue1.stdout 2>&1; done
for t in "0 0" "1 0" "2 0" "3 0" "0 1" "1 1" "2 1" "3 1"; do set -- $t; python3 run_lazy.py 7 1 1 7200 0 $1 $2 >> logs/queue1.stdout 2>&1; done
echo QUEUE_1_DONE >> logs/queue1.stdout
