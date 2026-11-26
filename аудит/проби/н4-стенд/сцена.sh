#!/bin/bash
# Стенд Н4 (за зразком `../н3-стенд/сцена.sh`): $1 = тека, $2 = сцена (с3|с5|с6|с8|ж3|с23).
# Жінки — `../н3-стенд/жінки/` (скопійовані в /tmp/n4/жінки); збірка — /tmp/n4/stor; Pyodide — /tmp/n4/pyodide.
OUT=$1; SC=$2; STOR=${STOR:-/tmp/n4/stor}; ZH=/tmp/n4/жінки/с4_марина.json; EXTRA=()
case $SC in
  с3) TXT='на роботу пішки, увесь день дощ, взуття — замшеві чоботи';;
  с5) TXT='я гостя на весіллі сестри в серпні, церемонія надворі о 16:00, потім ресторан'; ZH=/tmp/n4/жінки/с5_оксана.json;;
  с6) TXT='ну короче в суботу ми йдемо до свекрухи на ювілей там буде ресторан і вся родина я не хочу щоб вона знов щось сказала'
      EXTRA=(ROZMOVA_HODY='["хочу виглядати пристойно й доросло, минулого разу вона сказала що я вдягнулась як на дискотеку"]');;
  с8) TXT='на вулиці мінус десять і сніг, йду на роботу пішки 20 хвилин'; EXTRA=(TAP_POLE='сц-місце=офіс');;
  ж3) TXT='кава з подругою в кафе о 20:00';;
  с23) TXT='Зустріч з подругами у старовинній бібліотеці після презентації нашої нової книжки'
      EXTRA=(ROZMOVA=аудит/проби/е2_втрата_слова_розмова.json);;
  *) echo "невідома сцена $SC"; exit 2;;
esac
rm -rf $OUT; mkdir -p $OUT/знімки; cd /home/user/kod-shi-data
echo "старт $(date -u +%FT%TZ)" > $OUT/час.txt
env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy N2_CLI_PROXY="$HTTPS_PROXY" OTSINKA=0 FOTO=0 "${EXTRA[@]}" \
  CHAT_TEXT="$TXT" ZHINKA=$ZH MIST_WORKER=1 YADRO=${YADRO-1} ZHYVA=sonnet \
  N2_DUMP=$OUT/обміни.jsonl N2_VHID=$OUT/вхід-v1.json N2_STAN=$OUT/стан.json N2_SYNTH=/tmp/n4/синт.png MEREZHA_LOG=$OUT/мережа.log \
  ZNIMKY=$OUT/знімки ZVIT_OUT=$OUT/вердикти.txt CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node-tools/node_modules \
  timeout 3000 node аудит/проби/рв6_н3.js http://127.0.0.1:8765 $STOR /tmp/n4/pyodide ${SID:-3} > $OUT/лог.txt 2>&1
echo "rc=$? кінець $(date -u +%FT%TZ)" >> $OUT/час.txt
