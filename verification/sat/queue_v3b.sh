#!/bin/bash
# Lane B: noWA for the border targets (starts after the exact-slack job frees a core)
cd /path/to/jps-wa/verification/sat
while pgrep -f "EXACT_SLACKS" >/dev/null 2>&1 || pgrep -f "min_slack" >/dev/null 2>&1; do sleep 60; done
for t in "0 0" "1 0" "2 0" "3 0" "0 1" "3 1" "0 2" "0 3" "1 3"; do set -- $t; python3 run_lazy.py 7 1 1 14400 0 $1 $2 >> logs/queue_v3b.stdout 2>&1; done
echo LANE_B_DONE >> logs/queue_v3b.stdout
