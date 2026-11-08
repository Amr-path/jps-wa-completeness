#!/bin/bash
# usage: probe.sh owner/repo ...   lists map-like files (no blobs downloaded)
export GIT_TERMINAL_PROMPT=0
cd /path/to/jps-wa/robotmaps/raw/probe
for r in "$@"; do d=$(echo $r|tr / _); rm -rf $d
  timeout 60 git -c credential.helper= clone -q --depth 1 --filter=blob:none --no-checkout https://github.com/$r.git $d >/dev/null 2>&1 || { echo "== $r : FAIL"; continue; }
  echo "== $r"; git -C $d ls-tree -r -l HEAD | grep -iE '\.(pgm|png|yaml|ppm|bmp|txt|md)$' | grep -iE 'map|maze|pgm|yaml|readme|license' | awk '{print $4, $5}' | head -${N:-40}
done
