#!/bin/bash
# $1 = ДО|ПІСЛЯ  $2 = каталог зі стендом (index.html) $3 = каталог репо зі стендом-скриптом
export PATH="$PATH:/c/Users/Admin/.lmstudio/.internal/utils:/c/Users/Admin/.lmstudio/bin"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
export NODE_PATH=C:/Users/Admin/kod-shi-test-node/node_modules
T=/c/tmp/zhp2; R=/c/tmp/zh0810/R; ET=$1; SITE=$2; REPO=$3
export MODEL_URL=http://127.0.0.1:1235/v1 MODEL=qwen/qwen3.5-9b MODEL_MOVA=mamaylm-gemma-3-12b-it-v2.0 FOTO=1
while IFS='|' read -r ID W TXT X; do
  [ -z "$ID" ] && continue
  D=$T/out/$ET/$ID; rm -rf $D; mkdir -p $D
  export ZNIMKY=$D/знімки ZVIT_OUT=$D/вердикти.txt VIDPOVIDI=$D/VIDPOVIDI ZHINKA=$R/$W.json CHAT_TEXT="$TXT"
  for kv in $X; do k=${kv%%=*}; v=${kv#*=}; case $k in ROZMOVA) v=$R/$v;; FOTO_RECHI) v=$T/$v;; esac; export "$k=$v"; done
  S=$(date +%s)
  ( cd $REPO && timeout 2400 node аудит/проби/рв6_стенд.js http://127.0.0.1:8765 $SITE C:/tmp/pyodide 3 > $D/лог.txt 2>&1 )
  echo "$ID rc=$? $(( $(date +%s) - S ))с $(date +%T)" >> $T/out/$ET/done.txt
  for kv in $X; do unset ${kv%%=*}; done
done < ${4:-$T/сценарії.txt}
echo ALLDONE >> $T/out/$ET/done.txt
