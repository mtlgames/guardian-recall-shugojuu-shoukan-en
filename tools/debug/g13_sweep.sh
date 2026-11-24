#!/bin/sh
# Text coverage: every UNN g13 entry through the indexed draw (tools/lua/g13_sweep.lua) -> work/qa/cover/g13/eNN.
# Use: sh tools/debug/g13_sweep.sh [ENTRY..]   (default 0-18; 3 runs at a time)
cd "$(dirname "$0")/../.."
run() {
  python -X utf8 tools/debug/regen.py --only tac_think --outdir "work/qa/cover/g13/e$1" --cover \
    --lua tools/lua/g13_sweep.lua --var "G13=$1" --var FROM=2900 --timeout 1400 | tail -1 | sed "s/^/g13 e$1 /"
}
set -- ${@:-0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18}
while [ $# -gt 0 ]; do
  for e in $1 $2 $3; do run "$e" & done
  wait
  shift 3 2>/dev/null || shift $#
done
