#!/bin/bash
# Re-run of the round-3 structured WA*-adversary sweeps with the corrected success criterion (t pushed).
cd /home/claude/jps-wa/agent_math/round3
python3 exhaustive_pin1.py 7 1 > logs_v2/exh_7_1.log 2>&1
python3 exhaustive_pin1.py 9 0 > logs_v2/exh_9_0.log 2>&1
python3 search_designed.py 11 1500 > logs_v2/designed_11.log 2>&1
python3 exhaustive_pin1.py 9 1 > logs_v2/exh_9_1.log 2>&1
python3 exhaustive_pin1.py 8 1 pin2 > logs_v2/exh_8_1_pin2.log 2>&1
echo RERUN_V2_DONE >> logs_v2/exh_8_1_pin2.log
