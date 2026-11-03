#!/bin/bash
# wait for the N=6 run, then N=7 no-WA for all target representatives except (3,3) (done: SAT)
cd /home/claude/jps-wa/agent_math/sat
while pgrep -f "run_lazy.py 6 1 1 3000 0" > /dev/null; do sleep 30; done
for t in "0 0" "1 0" "2 0" "3 0" "0 1" "1 1" "2 1" "3 1" "0 2" "1 2" "2 2" "3 2" "0 3" "1 3" "2 3"; do
  set -- $t
  python3 run_lazy.py 7 1 1 7200 0 $1 $2 >> logs/queueA.stdout 2>&1
done
echo QUEUE_A_DONE >> logs/queueA.stdout
