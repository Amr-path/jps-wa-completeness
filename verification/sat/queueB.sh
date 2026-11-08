#!/bin/bash
# N=7 WA* runs for the targets that admit order failures (t in {2,3}^2 representatives), all weights
cd /path/to/jps-wa/verification/sat
for t in "3 3" "2 2" "2 3" "3 2"; do
  for w in "1 1" "3 2" "2 1" "3 1" "5 1" "10 1" "100 1"; do
    set -- $w; p=$1; q=$2; set -- $t
    if [ "$t" = "3 3" ] && [ "$p" = "1" ]; then continue; fi
    python3 run_lazy.py 7 $p $q 7200 1 $1 $2 >> logs/queueB.stdout 2>&1
  done
done
echo QUEUE_B_DONE >> logs/queueB.stdout
