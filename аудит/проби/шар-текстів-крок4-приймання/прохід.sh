#!/bin/bash
# Один прохід рецепту повтор.sh (#4848): той самий виклик стенда. Арг.: <до|після> <с3|с5|с8> <сід>
SIDE=$1; SCENA=$2; SID=$3; OUT=/tmp/крок4
case $SCENA in
 с3) ZH=с3_оксана.json; CHAT="на роботу пішки, увесь день дощ, взуття — замшеві чоботи";;
 с5) ZH=с5_оксана.json; CHAT="я гостя на весіллі сестри в серпні, церемонія надворі о 16:00, потім ресторан";;
 с8) ZH=с8_юлія.json; CHAT="на вулиці мінус десять і сніг, йду на роботу пішки 20 хвилин";;
esac
cd "$OUT/код-$SIDE"; RUN="$OUT/$SIDE/$SCENA-$SID"; mkdir -p "$RUN/знімки"
export NODE_PATH=/home/user/kod-shi-data/джерела/node_modules CHROMIUM=/opt/pw-browsers/chromium
ZHYVA=sonnet MIST_WORKER=1 YADRO=1 OTSINKA=0 FOTO=1 \
  ZHINKA="$PWD/аудит/проби/приймання-н2-782c/стенд/жінки/$ZH" CHAT_TEXT="$CHAT" \
  N2_DUMP="$RUN/обміни.jsonl" N2_VHID="$RUN/вхід-v1.json" N2_STAN="$RUN/стан.json" \
  ZNIMKY="$RUN/знімки" ZVIT_OUT="$RUN/вердикти.txt" \
  node аудит/проби/рв6_крок4.js http://127.0.0.1:8765 "$OUT/стенд-$SIDE" "$OUT/pyodide" "$SID" > "$RUN/лог.txt" 2>&1
echo "$SIDE $SCENA $SID rc=$?"
