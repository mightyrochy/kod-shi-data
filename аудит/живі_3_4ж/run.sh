#!/bin/bash
# $1 = файл сцен; $2 = мітка; $3 = повторів. Живий 3.4-Ж, збірка main 66edb5b8, стенд з 4bde9ae5, проксі :1235, сід 3.
export PATH="$PATH:/c/Users/Admin/.lmstudio/.internal/utils:/c/Users/Admin/.lmstudio/bin"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 NODE_PATH=C:/Users/Admin/kod-shi-test-node/node_modules
R=/c/tmp/zh0810/R; REPO=/c/tmp/z34zh; SITE=/c/tmp/z1837_site_pi; T=/c/tmp/z34zh_out; O=$T/$2
export MODEL_URL=http://127.0.0.1:1235/v1 MODEL=qwen/qwen3.5-9b MODEL_MOVA=mamaylm-gemma-3-12b-it-v2.0 FOTO=0
mkdir -p $O
for REP in $(seq 1 ${3:-1}); do
while IFS='|' read -r ID WJ TXT X; do
  [ -z "$ID" ] && continue
  D=$O/${ID}_r$REP; rm -rf $D; mkdir -p $D
  export ZNIMKY=$D/знімки ZVIT_OUT=$D/вердикти.txt VIDPOVIDI=$D/VIDPOVIDI ZHINKA=$R/$WJ.json CHAT_TEXT="$TXT"
  NAMES=$(echo "$X" | grep -oE '(^|[ ])[A-Z_]+=' | tr -d ' =')
  [ -n "$X" ] && eval "export $X"
  S=$(date +%s)
  ( cd $REPO && timeout 2400 node аудит/проби/рв6_стенд.js http://127.0.0.1:8765 $SITE C:/tmp/pyodide 3 > $D/лог.txt 2>&1 )
  echo "$2 $ID r$REP rc=$? $(( $(date +%s) - S ))с $(date +%T)" >> $T/done.txt
  for n in $NAMES; do unset $n; done
done < <(tr -d '\r' < $1)
done
