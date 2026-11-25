#!/bin/bash
# $1 = тека, $2 = CHAT_TEXT, $3 = ZHINKA, $4 = STOR (типово 782), далі — змінні env
OUT=$1; TXT=$2; ZH=$3; STOR=${4:-/tmp/n2/stor782}
rm -rf $OUT; mkdir -p $OUT/знімки; cd /tmp/n2/tree782
echo "старт $(date -u +%FT%TZ)" > $OUT/час.txt
env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy N2_CLI_PROXY="$HTTPS_PROXY" OTSINKA=0 FOTO=0 \
  CHAT_TEXT="$TXT" ZHINKA=$ZH MIST_WORKER=1 YADRO=${YADRO-1} ${VIKNO_N2:+VIKNO_N2=$VIKNO_N2} ZHYVA=sonnet \
  N2_DUMP=$OUT/обміни.jsonl N2_VHID=$OUT/вхід-v1.json ${NO_STAN:-N2_STAN=$OUT/стан.json} N2_SYNTH=/tmp/n2/синт.png MEREZHA_LOG=$OUT/мережа.log \
  ZNIMKY=$OUT/знімки ZVIT_OUT=$OUT/вердикти.txt CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node-tools/node_modules \
  timeout 3000 node аудит/проби/рв6_н2.js http://127.0.0.1:8765 $STOR /tmp/n2/pyodide ${SID:-3} > $OUT/лог.txt 2>&1
echo "rc=$? кінець $(date -u +%FT%TZ)" >> $OUT/час.txt
