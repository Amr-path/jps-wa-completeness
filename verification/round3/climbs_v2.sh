#!/bin/bash
cd /path/to/jps-wa/verification/round3
python3 climb.py 1 1 1200 9 pin1 > logs_v2/climb_1.log 2>&1
python3 climb.py 2 2 1200 9 pin1 > logs_v2/climb_2.log 2>&1
python3 climb.py 3 1000000 1200 9 pin1 > logs_v2/climb_3.log 2>&1
python3 climb.py 6 1000000 1200 8 pin2 > logs_v2/climb_6.log 2>&1
python3 climb.py 4 3 1200 8 pin2 > logs_v2/climb_4.log 2>&1
python3 climb.py 7 1.5 1200 9 rand > logs_v2/climb_7.log 2>&1
echo CLIMBS_V2_DONE >> logs_v2/climb_7.log
