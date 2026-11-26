#!/bin/bash
# run.sh <рука: head|base> <мітка> <persha: 1|0> <текст>
R=$1; M=$2; P=$3; T=$4
PAGE=/tmp/r3w/pak; [ "$R" = base ] && PAGE=/tmp/r3w/base-page
O=/tmp/r3w/out/$M; rm -rf $O; mkdir -p $O
if [ "$P" = 1 ]; then export PERSHA=/tmp/r3w/persha5.txt; else unset PERSHA; fi
cd /home/user/kod-shi-data
timeout 1500 node /tmp/r3w/tools/rozmova.cjs $PAGE /tmp/r3w/pyodide $O $M "$T" > $O/лог.txt 2>&1; echo "rc=$?" >> $O/лог.txt
tail -4 $O/лог.txt
