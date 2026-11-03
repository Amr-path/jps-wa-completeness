#!/bin/bash
cd /home/claude/jps-wa/agent_math/sat
for t in "2 1" "0 2" "1 2"; do set -- $t; python3 run_lazy.py 6 1 1 3000 0 $1 $2 >> logs/queueC.stdout 2>&1; done
echo QUEUE_C_DONE >> logs/queueC.stdout
