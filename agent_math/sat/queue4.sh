#!/bin/bash
# WA* runs for t=(2,3) (remaining weights) and t=(3,2) (all weights); waits for the running (2,3) w=3/2 job
cd /home/claude/jps-wa/agent_math/sat
while pgrep -f "run_lazy.py 7 3 2 7200 1 2 3" > /dev/null; do sleep 30; done
for w in "2 1" "3 1" "5 1" "10 1" "1000 1"; do set -- $w; python3 run_lazy.py 7 $1 $2 7200 1 2 3 >> logs/queue4.stdout 2>&1; done
for w in "1 1" "3 2" "2 1" "3 1" "5 1" "10 1" "1000 1"; do set -- $w; python3 run_lazy.py 7 $1 $2 7200 1 3 2 >> logs/queue4.stdout 2>&1; done
echo QUEUE_4_DONE >> logs/queue4.stdout
