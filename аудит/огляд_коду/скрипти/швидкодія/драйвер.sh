#!/bin/sh
# Усі виміри послідовно (по одному процесу виміру за раз), uptime до/після кожного.
SP=/tmp/claude-0/-home-user-kod-shi-data/66b2c79f-d82f-57ad-bcfa-0413f82df806/scratchpad/D
export CHROMIUM=/opt/pw-browsers/chromium-1194/chrome-linux/chrome NODE_PATH=$SP/wt/джерела/node_modules
L=$SP/прогони/драйвер.log
крок(){ echo "== $1 $(date +%T) $(uptime | sed 's/.*load average: //')" >> $L; }
for N in 2 3; do крок "стенд $N"; sh $SP/скрипти/стенд_раз.sh $N; done
for N in 1 2 3; do крок "pyo відтворення $N"; node $SP/скрипти/завантаження.js $SP/стенд $SP/pyodide $SP/прогони/pyo_$N.json $SP/прогони/виклики_1.json 0 >> $L 2>&1; done
for N in 1 2 3; do крок "pyo pyc $N"; node $SP/скрипти/завантаження.js $SP/стенд $SP/pyodide $SP/прогони/pyc_$N.json "" 0 1 >> $L 2>&1; done
for N in 1 2 3; do крок "pyo boot $N"; node $SP/скрипти/завантаження.js $SP/стенд $SP/pyodide $SP/прогони/boot_$N.json >> $L 2>&1; done
for N in 1 2 3; do крок "cpy холодний $N"; python3.12 -B $SP/скрипти/cpy_відтворення.py $SP/cpy/показ $SP/прогони/виклики_1.json $SP/прогони/cpy_х_$N.json холодний 2>/dev/null >> $L; done
крок "cpy прогрів pycache"; python3.12 $SP/скрипти/cpy_відтворення.py $SP/cpy/показ $SP/прогони/виклики_1.json $SP/прогони/cpy_т_0.json теплий 2>/dev/null >> $L
for N in 1 2 3; do крок "cpy теплий $N"; python3.12 $SP/скрипти/cpy_відтворення.py $SP/cpy/показ $SP/прогони/виклики_1.json $SP/прогони/cpy_т_$N.json теплий 2>/dev/null >> $L; done
rm -rf $SP/cpy/показ/__pycache__
крок "cpy3.13 холодний"; python3.13 -B $SP/скрипти/cpy_відтворення.py $SP/cpy/показ $SP/прогони/виклики_1.json $SP/прогони/cpy13_х_1.json холодний 2>/dev/null >> $L
крок "pyo профіль"; PSTATS_OUT= node $SP/скрипти/завантаження.js $SP/стенд $SP/pyodide $SP/прогони/pyo_проф.json $SP/прогони/виклики_1.json 1 >> $L 2>&1
крок "кінець"
