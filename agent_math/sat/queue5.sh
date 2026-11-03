#!/bin/bash
# N=8 exploratory runs after queue4 finishes (keeps at most two solver processes alive)
cd /home/claude/jps-wa/agent_math/sat
until grep -q QUEUE_4_DONE logs/queue4.stdout 2>/dev/null; do sleep 60; done
python3 run_lazy.py 8 1 1 14400 0 3 3 >> logs/queue5.stdout 2>&1
for w in "1 1" "2 1" "10 1" "1000 1" "3 2" "3 1" "5 1"; do set -- $w; python3 run_lazy.py 8 $1 $2 14400 1 3 3 >> logs/queue5.stdout 2>&1; done
echo QUEUE_5_DONE >> logs/queue5.stdout
