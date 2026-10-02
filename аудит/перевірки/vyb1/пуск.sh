#!/bin/bash
# $1 тека, $2 CHAT_TEXT
D=/tmp/ран_виб1/$1; mkdir -p "$D"
cd /home/user/kod-shi-data
VIDPOVIDI="$D/вікл" ZHYVA=sonnet FOTO=1 ZNIMKY="$D/знімки" ZVIT_OUT="$D/вердикти.txt" CHAT_TEXT="$2" CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node22/lib/node_modules \
  node аудит/проби/рв6_стенд.js http://127.0.0.1:8765 /tmp/стенд /tmp/pyodide 3 > "$D/лог.txt" 2>&1
echo rc=$? >> "$D/лог.txt"
