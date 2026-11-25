#!/bin/bash
# $1 = тека результату, $2 = ZBIJ (katalog або порожньо), $3 = STOR
OUT=$1; Z=$2; STOR=${3:-/tmp/n2/stor782}
rm -rf $OUT; mkdir -p $OUT/знімки; cd /tmp/n2/tree782
env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy OTSINKA=0 FOTO=0 ${Z:+ZBIJ=$Z} SCENA=ж7_збій_битої_речі \
  CHAT_TEXT="йду на роботу пішки, на вулиці мінус п'ятнадцять і сніг, відкритого й підборів не хочу" \
  ZHINKA=/tmp/n2/tree782/аудит/проби/жінки/ж7.json MIST_WORKER=1 YADRO=${YADRO-1} N2_DUMP=$OUT/обміни.jsonl N2_STAN=$OUT/стан.json N2_SYNTH=/tmp/n2/синт.png MEREZHA_LOG=$OUT/мережа.log \
  ZNIMKY=$OUT/знімки ZVIT_OUT=$OUT/вердикти.txt CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node-tools/node_modules \
  timeout 900 node аудит/проби/рв6_н2.js http://127.0.0.1:8765 $STOR /tmp/n2/pyodide 3 > $OUT/лог.txt 2>&1
echo rc=$? >> $OUT/лог.txt
