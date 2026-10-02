#!/bin/bash
# $1 = рядок клітинки W|N|T|EXTRA ; EXTRA = ІМ'Я=значення через пробіл
IFS='|' read -r W N T X <<< "$1"
D=/tmp/rz/runs/${W}_${N}; mkdir -p $D
cd /home/user/kod-shi-data
export ZHYVA=sonnet FOTO=1 ZNIMKY=$D/знімки ZVIT_OUT=$D/вердикти.txt VIDPOVIDI=$D/VIDPOVIDI ZHINKA=/home/user/kod-shi-data/аудит/проби/жінки/$W.json CHAT_TEXT="$T"
for kv in $X; do
  k=${kv%%=*}; v=${kv#*=}
  [ "$k" = ROZMOVA ] && v=/home/user/kod-shi-data/аудит/перевірки/rozbir_0210/$v
  export "$k=$v"
done
S=$(date +%s)
CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node22/lib/node_modules timeout 3000 node аудит/проби/рв6_стенд.js http://127.0.0.1:8765 /tmp/стенд /tmp/pyodide 3 > $D/лог.txt 2>&1
RC=$?
[ $RC -ne 0 ] && [ -s $D/знімки/картки.txt ] && { echo "rc=0 (стенд rc=$RC, картки є) $W $N $(( $(date +%s) - S ))с $(date +%T)" >> /tmp/rz/done.txt; exit 0; }
echo "rc=$RC $W $N $(( $(date +%s) - S ))с $(date +%T)" >> /tmp/rz/done.txt
