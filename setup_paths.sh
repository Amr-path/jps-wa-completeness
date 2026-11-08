#!/bin/bash
# Replaces the placeholder prefix /path/to/jps-wa with this repository's location in every script.
cd "$(dirname "$0")"; ROOT="$(pwd)"
grep -rlI --include='*.py' --include='*.sh' '/path/to/jps-wa' . | while read -r f; do
  sed -i.bak "s#/path/to/jps-wa#${ROOT}#g" "$f" && rm -f "$f.bak"
done
echo "paths set to $ROOT"
