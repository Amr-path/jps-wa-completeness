#!/bin/bash
# Lane C: corrected N=6 noWA for all 9 representative targets (after lanes A and B finish)
cd /home/claude/jps-wa/agent_math/sat
until grep -q LANE_A_DONE logs/queue_v3a.stdout 2>/dev/null; do sleep 120; done
for t in "0 0" "1 0" "2 0" "1 1" "2 1" "2 2" "0 1" "0 2" "1 2"; do set -- $t; python3 run_lazy.py 6 1 1 7200 0 $1 $2 >> logs/queue_v3c.stdout 2>&1; done
echo LANE_C_DONE >> logs/queue_v3c.stdout
