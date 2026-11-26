#!/bin/bash
# по одному ланцюгу за раз; мітка — <рука>-<випадок>
W=${W:-/tmp/r3w}
declare -A IN=( [незастосовне]=outputs/candidate/незастосовне [бракує-вимірів]=outputs/candidate/бракує-вимірів [перевірено]=outputs/candidate/перевірено [один-вимір]=evidence/один-вимір/candidate [граничний-розрив]=evidence/граничний-розрив/candidate )
for R in $1; do
  if [ "$R" = кандидат ]; then PAGE=$W/pak; SRC=run-cand; else PAGE=$W/base-page; SRC=run-base; fi
  for C in $2; do
    O=$W/out/$R/$C
    [ -f $O/підсумок.json ] && { echo "є $R/$C"; continue; }
    rm -rf $O; mkdir -p $O
    echo "=== $R/$C $(date -u +%H:%M:%S)"
    timeout 900 node $W/tools/r3.cjs $PAGE $W/pyodide $W/$SRC/${IN[$C]}/вхід.json $O $R-$C > $O/лог.txt 2>&1; echo "rc=$?" >> $O/лог.txt
    tail -8 $O/лог.txt
  done
done
