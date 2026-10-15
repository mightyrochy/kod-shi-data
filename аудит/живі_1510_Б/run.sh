#!/bin/bash
export PATH="$PATH:/c/Users/Admin/.lmstudio/.internal/utils:/c/Users/Admin/.lmstudio/bin"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 NODE_PATH='C:\Users\Admin\kod-shi-test-node\node_modules' NODE_OPTIONS=--use-system-ca
T=/c/tmp/zh1510b; W=$T/W; BR=claude/zhyvi-1510-b; P=аудит/живі_1510_Б
SHA=${SHA:?}; SITE=${SITE:-$T/site}; ET=ПІСЛЯ
export MODEL_URL=http://127.0.0.1:1236/v1 MODEL=qwen/qwen3.5-9b MODEL_MOVA=mamaylm-gemma-3-12b-it-v2.0 FOTO=1
STEND=${STEND:-аудит/проби/рв6_стенд.js}
ZHIN=$W/аудит/проби/жінки; RZ=$W/аудит/перевірки/rozbir_0210; FOTO_DIR=/c/tmp/zhp34
mkdir -p $T/out $W/$P; N=$(ls $W/$P | grep -cE '^[0-9]{2}_')
while IFS='|' read -r ID WJ TXT X; do
  [ -z "$ID" ] && continue; N=$((N+1)); K=$(printf '%02d' $N)_$ID; D=$T/out/$K; OUT=$W/$P/$K
  X=${X//ROZMOVA=R_/ROZMOVA=$RZ/R_}; X=${X//FOTO_RECHI=її_річ.jpg/FOTO_RECHI=$FOTO_DIR/її_річ.jpg}
  NAMES=$(echo "$X" | grep -oE '(^|[ ])[A-Z0-9_]+=' | tr -d ' =')
  for TRY in 1 2; do
    rm -rf $D; mkdir -p $D
    export ZNIMKY=$D/знімки ZVIT_OUT=$D/вердикти.txt VIDPOVIDI=$D/VIDPOVIDI ZHINKA=$ZHIN/$WJ.json CHAT_TEXT="$TXT"
    [ -n "$X" ] && eval "export $X"
    node $T/transport960.js $D/transport > $D/transport.log 2>&1 & TP=$!; sleep 1
    S=$(date +%s)
    ( cd ${W_STEND:-$W} && timeout 3600 node $STEND http://127.0.0.1:8765 $SITE C:/tmp/pyodide ${SEED:-3} > $D/лог.txt 2>&1 ); RC=$?
    SEC=$(( $(date +%s) - S )); kill $TP 2>/dev/null; wait $TP 2>/dev/null; for n in $NAMES; do unset $n; done
    [ $RC -le 1 ] && break
    cp $D/лог.txt $T/out/${K}_лог_$TRY.txt
    echo "$K спроба $TRY rc=$RC ${SEC}с $(date +%T) — збій середовища" >> $T/out/done.txt
  done
  rm -rf $OUT; mkdir -p $OUT; cp -r $D/. $OUT/; cp $T/out/${K}_лог_1.txt $OUT/лог_1.txt 2>/dev/null
  echo "$SHA $ID $ET $MODEL+$MODEL_MOVA" > $OUT/код.txt
  echo "$K rc=$RC ${SEC}с $(date +%T) HTTP599=$(grep -c 'HTTP 599' $D/лог.txt) length=$(grep -l '"finish_reason": "length"' $D/transport/*.json 2>/dev/null | wc -l)/$(ls $D/transport | wc -l)" >> $T/out/done.txt
  cp $T/out/done.txt $W/$P/done.txt
  ( cd $W && git add $P && git commit -qm "живі-1510 Б: $ET $K rc=$RC ${SEC}с" )
  for i in 1 2 3 4; do ( cd $W && git push --no-thin -q -u origin $BR ) && break; sleep $((2<<i)); done
  if [ ! -f $T/перевірено_пуш ]; then
    [ "$(git -C $W ls-remote origin refs/heads/$BR | cut -f1)" = "$(git -C $W rev-parse HEAD)" ] \
      && touch $T/перевірено_пуш || { echo "ПУШ НЕ ДІЙШОВ після $K" >> $T/out/done.txt; exit 3; }
  fi
done < <(tr -d '\r' < $1)
