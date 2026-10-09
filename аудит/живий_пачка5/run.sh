#!/bin/bash
# $1 = ДО|ПІСЛЯ  $2 = каталог з index.html  $3 = робоче дерево зі стендом  $4 = файл сцен
export PATH="$PATH:/c/Users/Admin/.lmstudio/.internal/utils:/c/Users/Admin/.lmstudio/bin"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
export NODE_PATH=C:/Users/Admin/kod-shi-test-node/node_modules
T=/c/tmp/zh5; R=/c/tmp/zh0810/R; W=$T/wtr; ET=$1; SITE=$2; REPO=$3
export MODEL_URL=http://127.0.0.1:1236/v1 MODEL=qwen/qwen3.5-9b MODEL_MOVA=mamaylm-gemma-3-12b-it-v2.0 FOTO=1
mkdir -p $T/out/$ET
while IFS='|' read -r ID WJ TXT X; do
  [ -z "$ID" ] && continue
  D=$T/out/$ET/$ID
  for TRY in 1 2; do
    rm -rf $D; mkdir -p $D
    export ZNIMKY=$D/знімки ZVIT_OUT=$D/вердикти.txt VIDPOVIDI=$D/VIDPOVIDI ZHINKA=$R/$WJ.json CHAT_TEXT="$TXT"
    for kv in $X; do export "$kv"; done
    S=$(date +%s)
    ( cd $REPO && timeout 2400 node аудит/проби/рв6_стенд.js http://127.0.0.1:8765 $SITE C:/tmp/pyodide 3 > $D/лог.txt 2>&1 )
    RC=$?; SEC=$(( $(date +%s) - S ))
    for kv in $X; do unset ${kv%%=*}; done
    [ $RC -le 1 ] && break
    cp $D/лог.txt $T/out/$ET/${ID}_спроба${TRY}_rc${RC}.лог.txt 2>/dev/null
    echo "$ID спроба $TRY rc=$RC $SEC с" >> $T/out/$ET/done.txt
  done
  echo "$ID rc=$RC ${SEC}с $(date +%T)" >> $T/out/$ET/done.txt
  OUT=$W/аудит/живий_пачка5/$ET; mkdir -p $OUT; rm -rf $OUT/$ID; cp -r $D $OUT/$ID; cp $T/out/$ET/${ID}_спроба*.лог.txt $OUT/ 2>/dev/null
  cp $T/proksi.log $T/run.sh $W/аудит/живий_пачка5/ 2>/dev/null
  ( cd $W && git add аудит/живий_пачка5 >/dev/null 2>&1 && git commit -qm "живий-пачка5: $ET $ID rc=$RC ${SEC}с

Co-Authored-By: Claude Code <noreply@anthropic.com>" )
  for i in 1 2 3 4; do ( cd $W && GIT_NO_LAZY_FETCH=1 git push --no-thin -q -u origin claude/zhyvyi-pachka-5 ) && break; sleep $((2<<i)); done
done < $4
