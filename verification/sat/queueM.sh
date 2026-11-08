#!/bin/bash
# Main-session queue (after the restart): remaining 7x7 targets. First no-WA (any order) for all representative
# targets other than (3,3); an UNSAT there settles every weight for that target. Then WA* runs for targets whose
# any-order run is SAT. Two lanes, run in parallel.
cd /path/to/jps-wa/verification/sat
lane() { for t in "$@"; do set -- $t; python3 run_lazy.py 7 1 1 7200 0 $1 $2 >> logs/queueM.stdout 2>&1; done; }
