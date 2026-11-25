#!/bin/bash
# Перевірка Р2 #4727 3cebe496: живі сцени, послідовно
B=/tmp/n2/live; S=/tmp/n2/stor; mkdir -p $B
run(){ # $1 тека $2 слова $3 жінка(шлях) ; env: VIKNO_N2, ZBIJ, SCENA
  OUT=$B/$1; rm -rf $OUT; mkdir -p $OUT/знімки
  echo "$(date -u +%FT%TZ) старт $1" >> $B/хід.txt
  echo "старт $(date -u +%FT%TZ)" > $OUT/час.txt
  ( cd /tmp/n2/tree && env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy N2_CLI_PROXY="$HTTPS_PROXY" OTSINKA=0 FOTO=0 \
    CHAT_TEXT="$2" ZHINKA=$3 MIST_WORKER=1 YADRO=1 ZHYVA=sonnet ${VIKNO_N2:+VIKNO_N2=$VIKNO_N2} ${ZBIJ:+ZBIJ=$ZBIJ} ${SCENA:+SCENA=$SCENA} \
    N2_DUMP=$OUT/обміни.jsonl N2_VHID=$OUT/вхід-v1.json N2_STAN=$OUT/стан.json N2_SYNTH=/tmp/n2/синт.png MEREZHA_LOG=$OUT/мережа.log \
    ZNIMKY=$OUT/знімки ZVIT_OUT=$OUT/вердикти.txt CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node-tools/node_modules \
    timeout 3000 node аудит/проби/рв6_н2.js http://127.0.0.1:8765 $S /tmp/n2/pyodide 3 > $OUT/лог.txt 2>&1 )
  echo "rc=$? кінець $(date -u +%FT%TZ)" >> $OUT/час.txt
  echo "$(date -u +%FT%TZ) кінець $1 $(tail -1 $OUT/час.txt)" >> $B/хід.txt
}
ZH=/tmp/n2/жінки
ZH7=/tmp/n2/tree/аудит/проби/жінки/ж7.json
run с3 "на роботу пішки, увесь день дощ, взуття — замшеві чоботи" $ZH/с3_оксана.json
run с5 "я гостя на весіллі сестри в серпні, церемонія надворі о 16:00, потім ресторан" $ZH/с5_оксана.json
run с8 "на вулиці мінус десять і сніг, йду на роботу пішки 20 хвилин" $ZH/с8_юлія.json
ZBIJ=katalog SCENA=ж7_збій_битої_речі run ж7-бита "йду на роботу пішки, на вулиці мінус п'ятнадцять і сніг, відкритого й підборів не хочу" $ZH7
SCENA=ж7_збій_битої_речі run ж7-без "йду на роботу пішки, на вулиці мінус п'ятнадцять і сніг, відкритого й підборів не хочу" $ZH7
VIKNO_N2=40000 run с5-в40к "я гостя на весіллі сестри в серпні, церемонія надворі о 16:00, потім ресторан" $ZH/с5_оксана.json
VIKNO_N2=12000 run с5-в12к "я гостя на весіллі сестри в серпні, церемонія надворі о 16:00, потім ресторан" $ZH/с5_оксана.json
echo "$(date -u +%FT%TZ) УСЕ" >> $B/хід.txt
