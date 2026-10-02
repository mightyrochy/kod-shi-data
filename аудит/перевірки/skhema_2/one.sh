#!/bin/bash
# $1 = ДО|ПІСЛЯ ; $2 = рядок клітинки W|N|T|PAL
IFS='|' read -r W N T PAL <<< "$2"
D=/tmp/s2/runs/$1/${W}_${N}; mkdir -p $D
[ "$1" = ДО ] && K=/tmp/стенд_до || K=/tmp/стенд_після
cd /home/user/kod-shi-data
export ZHYVA=sonnet FOTO=1 ZNIMKY=$D/знімки ZVIT_OUT=$D/вердикти.txt ZHINKA=/home/user/kod-shi-data/аудит/проби/жінки/$W.json CHAT_TEXT="$T"
[ -n "$PAL" ] && export PAL_SHEMA="$PAL"
CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node22/lib/node_modules timeout 3000 node аудит/проби/рв6_стенд.js http://127.0.0.1:8765 $K /tmp/pyodide 3 > $D/лог.txt 2>&1
echo "rc=$? $1 $W $N $(date +%T)" >> /tmp/s2/done.txt
