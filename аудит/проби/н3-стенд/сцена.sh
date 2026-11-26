#!/bin/bash
# $1 = тека, $2 = сцена (с4|с5); далі змінні env (VIKNO_N2, MODEL_VYBIR, ZAPYS, CHASTYN, MOVCHYT)
OUT=$1; SC=$2; STOR=${STOR:-/tmp/n3/stor}
case $SC in
  с4) TXT='побачення в ресторані ввечері, о 19:30'; ZH=/tmp/n3/жінки/с4_марина.json;;
  с5) TXT='я гостя на весіллі сестри в серпні, церемонія надворі о 16:00, потім ресторан'; ZH=/tmp/n3/жінки/с5_оксана.json;;
esac
rm -rf $OUT; mkdir -p $OUT/знімки; cd /home/user/kod-shi-data
echo "старт $(date -u +%FT%TZ)" > $OUT/час.txt
env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy N2_CLI_PROXY="$HTTPS_PROXY" OTSINKA=0 FOTO=0 \
  CHAT_TEXT="$TXT" ZHINKA=$ZH MIST_WORKER=1 YADRO=${YADRO-1} ${VIKNO_N2:+VIKNO_N2=$VIKNO_N2} ZHYVA=sonnet \
  N2_DUMP=$OUT/обміни.jsonl N2_VHID=$OUT/вхід-v1.json N2_STAN=$OUT/стан.json N2_SYNTH=/tmp/n3/синт.png MEREZHA_LOG=$OUT/мережа.log \
  ZNIMKY=$OUT/знімки ZVIT_OUT=$OUT/вердикти.txt CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node-tools/node_modules \
  timeout 3000 node аудит/проби/рв6_н3.js http://127.0.0.1:8765 $STOR /tmp/n3/pyodide ${SID:-3} > $OUT/лог.txt 2>&1
echo "rc=$? кінець $(date -u +%FT%TZ)" >> $OUT/час.txt
