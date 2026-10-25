#!/bin/bash
# $1 = тека збірки; $2 = мітка; $3 = файл сцен. Живий 3.2-Е, розмова, проксі :1237, 1 повтор, сід 3.
export PATH="$PATH:/c/Users/Admin/.lmstudio/.internal/utils:/c/Users/Admin/.lmstudio/bin"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 NODE_PATH=C:/Users/Admin/kod-shi-test-node/node_modules
R=/c/tmp/zh0810/R; REPO=/c/tmp/z32e; O=/c/tmp/z32e_out/$2
export MODEL_URL=http://127.0.0.1:1237/v1 MODEL=qwen/qwen3.5-9b MODEL_MOVA=mamaylm-gemma-3-12b-it-v2.0 FOTO=0 DO=rozmova
mkdir -p $O
while IFS='|' read -r ID WJ TXT; do
  D=$O/$ID; rm -rf $D; mkdir -p $D
  export ZNIMKY=$D/знімки ZVIT_OUT=$D/вердикти.txt VIDPOVIDI=$D/VIDPOVIDI ZHINKA=$R/$WJ.json CHAT_TEXT="$TXT"
  S=$(date +%s)
  ( cd $REPO && timeout 900 node аудит/проби/рв6_стенд.js http://127.0.0.1:8765 $1 C:/tmp/pyodide 3 > $D/лог.txt 2>&1 )
  echo "$2 $ID rc=$? $(( $(date +%s) - S ))с $(date +%T)" >> /c/tmp/z32e_out/done.txt
done < <(tr -d '\r' < $3)
