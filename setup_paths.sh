#!/bin/bash
# Replaces the original absolute prefix /home/claude/jps-wa by this repository's location in every script.
cd "$(dirname "$0")"; ROOT="$(pwd)"
grep -rlI --include='*.py' --include='*.sh' '/home/claude/jps-wa' . | while read -r f; do
  sed -i.bak "s#/home/claude/jps-wa#${ROOT}#g" "$f" && rm -f "$f.bak"
done
echo "paths set to $ROOT"
