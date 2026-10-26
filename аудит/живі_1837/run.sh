#!/bin/bash
# $1 = файл сцен; $2 = тека збірки; $3 = мітка (ДО|ПІСЛЯ); $4 = режим (повний|розмова); $5 = кількість повторів. Живий пачки 1837, проксі :1238, сід 3.
export PATH="$PATH:/c/Users/Admin/.lmstudio/.internal/utils:/c/Users/Admin/.lmstudio/bin"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 NODE_PATH=C:/Users/Admin/kod-shi-test-node/node_modules
R=/c/tmp/zh0810/R; REPO=/c/tmp/z1837; T=/c/tmp/z1837_out; O=$T/$3
export MODEL_URL=http://127.0.0.1:1238/v1 MODEL=qwen/qwen3.5-9b MODEL_MOVA=mamaylm-gemma-3-12b-it-v2.0 FOTO=0
[ "$4" = розмова ] && export DO=rozmova
mkdir -p $O
for REP in $(seq 1 ${5:-1}); do
while IFS='|' read -r ID WJ TXT X; do
  [ -z "$ID" ] && continue
  D=$O/${ID}_r$REP; rm -rf $D; mkdir -p $D
  export ZNIMKY=$D/знімки ZVIT_OUT=$D/вердикти.txt VIDPOVIDI=$D/VIDPOVIDI ZHINKA=$R/$WJ.json CHAT_TEXT="$TXT"
  NAMES=$(echo "$X" | grep -oE '(^|[ ])[A-Z_]+=' | tr -d ' =')
  [ -n "$X" ] && eval "export $X"
  S=$(date +%s)
  ( cd $REPO && timeout 2400 node аудит/проби/рв6_стенд.js http://127.0.0.1:8765 $2 C:/tmp/pyodide 3 > $D/лог.txt 2>&1 )
  echo "$3 $ID r$REP rc=$? $(( $(date +%s) - S ))с $(date +%T)" >> $T/done.txt
  for n in $NAMES; do unset $n; done
done < <(tr -d '\r' < $1)
done
