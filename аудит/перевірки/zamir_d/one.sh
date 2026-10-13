#!/bin/bash
# $1 = рядок клітинки
IFS='|' read -r W N T R <<< "$1"
D=/tmp/zd/runs/${W}_${N}; mkdir -p $D
cd /home/user/kod-shi-data
export ZHYVA=sonnet FOTO=1 ZNIMKY=$D/знімки ZVIT_OUT=$D/вердикти.txt ZHINKA=/home/user/kod-shi-data/аудит/проби/жінки/$W.json CHAT_TEXT="$T"
[ "$R" = R ] && export ROZMOVA=/tmp/zd/roz.json
CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node22/lib/node_modules node аудит/проби/рв6_стенд.js http://127.0.0.1:8765 /tmp/стенд /tmp/pyodide 3 > $D/лог.txt 2>&1
echo "rc=$? $W $N $(date +%T)" >> /tmp/zd/done.txt
