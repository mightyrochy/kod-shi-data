#!/bin/bash
# $1 = файл сцен; $2 = тека збірки (типово C:/tmp/zh17/site); $3 = SHA коду збірки; $4 = ДО|ПІСЛЯ.
# Збірка ПІСЛЯ: db5adb72 (claude/pachka-1010-27, zh17), проксі :1236 (qwen 57344, MamayLM 16384).
export PATH="$PATH:/c/Users/Admin/.lmstudio/.internal/utils:/c/Users/Admin/.lmstudio/bin"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 NODE_PATH=C:/Users/Admin/kod-shi-test-node/node_modules
T=/c/tmp/zh17; R=/c/tmp/zh0810/R; REPO=/c/Users/Admin/kod-shi-data; FOTO_DIR=/c/tmp/zhp34
BR=claude/zhyvi-17
SITE=${2:-$T/site}; SHA=${3:-db5adb72ac5d82a47ac9db3d119572f62f09f606}; ET=${4:-ПІСЛЯ}
PART=$(basename "$1" .txt); PART=${PART#сцени_}
export MODEL_URL=http://127.0.0.1:1236/v1 MODEL=qwen/qwen3.5-9b MODEL_MOVA=mamaylm-gemma-3-12b-it-v2.0 FOTO=1
mkdir -p $T/out/$PART; N=0
while IFS='|' read -r ID WJ TXT X; do
  N=$((N+1)); [ -z "$ID" ] && continue
  K=$(printf '%02d' $N)_$ID
  D=$T/out/$PART/$K; OUT=$REPO/аудит/живі_17/$PART/$K
  X=${X//FOTO_RECHI=її_річ.jpg/FOTO_RECHI=$FOTO_DIR/її_річ.jpg}
  NAMES=$(echo "$X" | grep -oE '(^|[ ])[A-Z_]+=' | tr -d ' =')
  SEED_ARG=3
  for TRY in 1 2; do
    rm -rf $D; mkdir -p $D
    export ZNIMKY=$D/знімки ZVIT_OUT=$D/вердикти.txt VIDPOVIDI=$D/VIDPOVIDI ZHINKA=$R/$WJ.json CHAT_TEXT="$TXT"
    [ -n "$X" ] && eval "export $X"
    S=$(date +%s)
    ( cd $REPO && timeout 2400 node аудит/проби/рв6_стенд.js http://127.0.0.1:8765 $SITE C:/tmp/pyodide ${SEED:-3} > $D/лог.txt 2>&1 )
    RC=$?; SEC=$(( $(date +%s) - S ))
    for n in $NAMES; do unset $n; done
    [ $RC -le 1 ] && break
    cp $D/лог.txt $T/out/$PART/${K}_лог_$TRY.txt
    echo "$PART/$K спроба $TRY rc=$RC ${SEC}с $(date +%T) — збій середовища" >> $T/out/done.txt
  done
  rm -rf $OUT; mkdir -p $OUT; cp -r $D/. $OUT/; cp $T/out/$PART/${K}_лог_1.txt $OUT/лог_1.txt 2>/dev/null
  echo "$SHA $ID $ET $MODEL+$MODEL_MOVA" > $OUT/код.txt
  echo "$PART/$K rc=$RC ${SEC}с $(date +%T)" >> $T/out/done.txt; cp $T/out/done.txt $REPO/аудит/живі_17/done.txt
  ( cd $REPO && git add аудит/живі_17 >/dev/null 2>&1 && git commit -qm "живі-17: $ET $PART/$K rc=$RC ${SEC}с

Co-Authored-By: Claude Code <noreply@anthropic.com>" )
  for i in 1 2 3 4; do ( cd $REPO && GIT_NO_LAZY_FETCH=1 git push --no-thin -q -u origin $BR ) && break; sleep $((2<<i)); done
done < <(tr -d '\r' < $1)
echo "$PART ALLDONE $(date +%T)" >> $T/out/done.txt; cp $T/out/done.txt $REPO/аудит/живі_17/done.txt
