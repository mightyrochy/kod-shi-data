#!/bin/bash
SP=/tmp/claude-0/-home-user-kod-shi-data/66b2c79f-d82f-57ad-bcfa-0413f82df806/scratchpad/D
export CHROMIUM=/opt/pw-browsers/chromium-1194/chrome-linux/chrome NODE_PATH=$SP/wt/джерела/node_modules
L=$SP/прогони/драйвер2.log
k(){ echo "== $1 $(date +%T) $(uptime | sed 's/.*load average: //')" >> $L; }
for N in 1 2 3; do k "кеш відвідин $N"; KESH_DIR=$SP/tmp OUT=$SP/прогони/кеш_$N.json node $SP/скрипти/кеш_відвідин.js $SP/pyodide 8790 >> $L 2>&1; done
cd $SP/wt
for N in 1 2 3; do k "стенд typy $N"; uptime > $SP/прогони/typy_$N.uptime; s=$(date +%s)
  ZATRYMKA=typy OTSINKA=0 CHASY=1 CHASY_OUT=$SP/прогони/часи_typy_$N.json VYMIR_OUT=$SP/прогони/вим_typy_$N timeout 1800 node аудит/проби/рв6_стенд_вимір.js http://127.0.0.1:8765 $SP/стенд $SP/pyodide 3 > $SP/прогони/typy_$N.log 2>&1
  echo "rc $? $(( $(date +%s)-s )) s" >> $SP/прогони/typy_$N.uptime; done
k "стенд typy ODNA"; ZATRYMKA=typy ZATRYMKA_ODNA=1 OTSINKA=0 CHASY=1 CHASY_OUT=$SP/прогони/часи_odna_1.json VYMIR_OUT=$SP/прогони/вим_odna_1 timeout 2400 node аудит/проби/рв6_стенд_вимір.js http://127.0.0.1:8765 $SP/стенд $SP/pyodide 3 > $SP/прогони/odna_1.log 2>&1
k "кінець"
