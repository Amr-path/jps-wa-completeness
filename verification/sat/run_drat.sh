#!/bin/bash
# Proof-checked UNSAT for the 16 targets of the SAT result (N=7, w=1). Run in the macOS Terminal:
#   cd <this folder> && bash run_drat.sh            (LANES=3 bash run_drat.sh for three parallel lanes)
# First run builds CaDiCaL and drat-trim from GitHub into tools/. Safe to stop and rerun: targets whose log
# contains RESULT are skipped; an interrupted target restarts from the beginning. Each lane needs several GB of
# free disk for a proof file while it is being checked. A progress bar is redrawn every 5 s; Ctrl-C stops all lanes.
cd "$(dirname "$0")"
ROOT=$(pwd); LANES=${LANES:-2}
mkdir -p tools
# Pick a macOS SDK that the installed linker can use (a Command Line Tools update can leave a newer SDK than the
# linker understands, e.g. "unknown architecture arm64e.x1"). Tries the default first, then every installed SDK.
if [ "$(uname)" = Darwin ]; then
  printf 'int main(){return 0;}\n' > tools/hello.cpp
  if ! c++ tools/hello.cpp -o tools/hello 2>/dev/null; then
    ok=""
    for sdk in $(ls -d /Library/Developer/CommandLineTools/SDKs/MacOSX[0-9]*.sdk 2>/dev/null | sort -r); do
      if SDKROOT="$sdk" c++ tools/hello.cpp -o tools/hello 2>/dev/null; then export SDKROOT="$sdk"; ok=1; break; fi
    done
    if [ -z "$ok" ]; then
      echo "No working C++ compiler/SDK found. Update the Command Line Tools (System Settings > General >"
      echo "Software Update, or: softwareupdate --list) and run this script again."; exit 1
    fi
    echo "using SDKROOT=$SDKROOT"
  fi
fi
if [ ! -x tools/cadical/build/cadical ]; then
  [ -d tools/cadical/.git ] || git clone -q https://github.com/arminbiere/cadical.git tools/cadical || exit 1
  (cd tools/cadical && rm -rf build && ./configure && make -j4) || exit 1
fi
if [ ! -x tools/drat-trim/drat-trim ]; then
  [ -d tools/drat-trim/.git ] || git clone -q https://github.com/marijnheule/drat-trim.git tools/drat-trim || exit 1
  (cd tools/drat-trim && make) || exit 1
fi
mkdir -p jps-wa/verification/sat/drat
echo "cadical $(tools/cadical/build/cadical --version) commit $(git -C tools/cadical rev-parse --short HEAD); drat-trim commit $(git -C tools/drat-trim rev-parse --short HEAD)" >> jps-wa/verification/sat/drat/tools.txt
cd jps-wa/verification/sat
# ordered by the earlier solve times, shortest first
T="1 3|3 1|3 3|3 0|2 3|0 3|3 2|2 2|1 2|2 1|0 2|1 0|0 1|1 1|2 0|0 0"
IFS='|' read -ra ALL <<< "$T"
lane() { local k=$1
  for ((i=k; i<${#ALL[@]}; i+=LANES)); do set -- ${ALL[$i]}
    grep -q RESULT drat/drat_t$1$2.log 2>/dev/null && continue
    echo "running $(date +%s)" > drat/state_t$1$2
    echo "[$(date '+%d %H:%M')] start t=($1,$2)" >> drat/events.txt
    python3 drat_run.py $1 $2 > /dev/null 2>&1
    echo "ended $(date +%s)" > drat/state_t$1$2
    echo "[$(date '+%d %H:%M')] end   t=($1,$2): $(grep -h 'drat-trim \[' drat/drat_t$1$2.log | tail -1)" >> drat/events.txt
  done; }
mkdir -p drat; rm -f drat/state_t* drat/.stop
PIDS=""
for ((k=0; k<LANES; k++)); do lane $k & PIDS="$PIDS $!"; done
python3 drat_progress.py "$T" drat/.stop &
MON=$!
trap 'echo; echo "Stopping all lanes ..."; trap "" TERM; kill -TERM 0 2>/dev/null; sleep 1; echo "Stopped. Rerun the same command to continue (finished targets are kept)."; exit 130' INT TERM
wait $PIDS
touch drat/.stop; wait $MON
echo
echo "Verified: $(grep -l 's VERIFIED' drat/drat_t*.log 2>/dev/null | wc -l | tr -d ' ') / 16   (events: jps-wa/verification/sat/drat/events.txt)"
