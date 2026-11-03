#!/bin/bash
cd /home/claude/jps-wa/agent_math/sat
for t in "2 3" "1 3" "0 3" "2 1" "2 0" "1 0" "3 0" "3 1" "3 2"; do set -- $t; python3 run_lazy.py 7 1 1 7200 0 $1 $2 >> logs/queueM2.stdout 2>&1; done
echo LANE2_NOWA_DONE >> logs/queueM2.stdout
