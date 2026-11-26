#!/bin/bash
# Стенд перевірки Н5 за зразком н4-стенд/сцена.sh: $1 = тека, $2 = сцена (с3|с5|с8).
OUT=$1; SC=$2; STOR=${STOR:-/tmp/n5/stor}; ZH=/tmp/n5/жінки/с4_марина.json; EXTRA=()
case $SC in
  с3) TXT='на роботу пішки, увесь день дощ, взуття — замшеві чоботи';;
  с5) TXT='я гостя на весіллі сестри в серпні, церемонія надворі о 16:00, потім ресторан'; ZH=/tmp/n5/жінки/с5_оксана.json;;
  с8) TXT='на вулиці мінус десять і сніг, йду на роботу пішки 20 хвилин'; EXTRA=(TAP_POLE='сц-місце=офіс');;
  *) echo "невідома сцена $SC"; exit 2;;
esac
rm -rf $OUT; mkdir -p $OUT/знімки; cd /tmp/h5
echo "старт $(date -u +%FT%TZ)" > $OUT/час.txt
env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy N2_CLI_PROXY="$HTTPS_PROXY" OTSINKA=0 FOTO=0 "${EXTRA[@]}" \
  CHAT_TEXT="$TXT" ZHINKA=$ZH MIST_WORKER=1 YADRO=${YADRO-1} ZHYVA=sonnet \
  N2_DUMP=$OUT/обміни.jsonl N2_VHID=$OUT/вхід-v1.json N2_STAN=$OUT/стан.json N2_SYNTH=/tmp/n5/синт.png MEREZHA_LOG=$OUT/мережа.log \
  ZNIMKY=$OUT/знімки ZVIT_OUT=$OUT/вердикти.txt CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node-tools/node_modules \
  timeout 3000 node аудит/проби/${SCRIPT:-рв6_н3_п.js} http://127.0.0.1:8765 $STOR /tmp/pyodide ${SID:-3} > $OUT/лог.txt 2>&1
echo "rc=$? кінець $(date -u +%FT%TZ)" >> $OUT/час.txt
