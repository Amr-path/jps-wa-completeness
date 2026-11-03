#!/bin/bash
cd /home/claude/jps-wa/agent_math/sat
python3 validate3.py 5 16 > logs/validate3_5.log 2>&1
for w in "1 1" "3 2" "2 1" "3 1" "5 1" "10 1" "1000 1"; do set -- $w; python3 run_lazy.py 7 $1 $2 7200 1 2 3 >> logs/queue2.stdout 2>&1; done
for w in "1 1" "3 2" "2 1" "3 1" "5 1" "10 1" "1000 1"; do set -- $w; python3 run_lazy.py 7 $1 $2 7200 1 3 2 >> logs/queue2.stdout 2>&1; done
for t in "0 2" "1 2" "0 3" "1 3" "2 3" "3 2" "2 2"; do set -- $t; python3 run_lazy.py 7 1 1 7200 0 $1 $2 >> logs/queue2.stdout 2>&1; done
echo QUEUE_2_DONE >> logs/queue2.stdout
