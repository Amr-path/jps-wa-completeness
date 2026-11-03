#!/bin/bash
# Single SAT lane (2-core machine; the other core runs round3/exact_slacks.py).
# 1) N=7 WA* center target, remaining weights. 2) N=7 WA* w=1, all 16 representative targets (skip done 33).
cd /home/claude/jps-wa/agent_math/sat
for w in "10 1" "1000 1"; do set -- $w
  grep -q SUMMARY logs/lazyv2_N7_w$1_$2_t33.log 2>/dev/null || python3 run_lazy.py 7 $1 $2 14400 1 3 3 >> logs/queue_v4.stdout 2>&1
done
for t in "2 2" "2 3" "3 2" "1 1" "1 2" "2 1" "1 3" "3 1" "0 3" "3 0" "0 0" "1 0" "0 1" "2 0" "0 2"; do set -- $t
  grep -q SUMMARY logs/lazyv2_N7_w1_1_t$1$2.log 2>/dev/null || python3 run_lazy.py 7 1 1 14400 1 $1 $2 >> logs/queue_v4.stdout 2>&1
done
echo QUEUE_V4_DONE >> logs/queue_v4.stdout
