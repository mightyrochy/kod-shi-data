#!/bin/bash
# Клітинка ФІГУРА-ОПИС: $1 = ДО|ПІСЛЯ, $2 = рядок cells.txt (W|N|T|EXTRA). Обв'язка rozbir_0210/one.sh + pak.sh;
# ДО — стенд, зібраний із main 37a2c52 (/tmp/стенд_до), ПІСЛЯ — з гілки (/tmp/стенд). До 2 спроб.
M=$1; IFS='|' read -r W N T X <<< "$2"
R0=/home/user/kod-shi-data/аудит/перевірки/rozbir_0210; HERE=$(cd "$(dirname "$0")" && pwd)
ST=/tmp/стенд; [ "$M" = ДО ] && ST=/tmp/стенд_до
for a in 1 2; do
  D=/tmp/fo/$M/${W}_${N}; rm -rf $D; mkdir -p $D
  ( cd /home/user/kod-shi-data
    export ZHYVA=sonnet FOTO=1 ZNIMKY=$D/знімки ZVIT_OUT=$D/вердикти.txt VIDPOVIDI=$D/VIDPOVIDI \
           ZHINKA=/home/user/kod-shi-data/аудит/проби/жінки/$W.json CHAT_TEXT="$T"
    for kv in $X; do k=${kv%%=*}; v=${kv#*=}; [ "$k" = ROZMOVA ] && v=$R0/$v; export "$k=$v"; done
    CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node22/lib/node_modules timeout 3000 \
      node аудит/проби/рв6_стенд.js http://127.0.0.1:8765 $ST /tmp/pyodide 3 > $D/лог.txt 2>&1 )
  [ -s $D/знімки/картки.txt ] && [ -s $D/вердикти.txt ] && ! grep -q "не дав result" $D/лог.txt && break
  echo "$M $W $N: спроба $a без карток" >> /tmp/fo/збої.txt
done
P=$HERE/$M/${W}_${N}; mkdir -p $P
cp $D/знімки/картки.txt $D/знімки/текст_екранів.txt $P/ 2>/dev/null
gzip -c $D/вердикти.txt > $P/вердикти.txt.gz; gzip -c $D/лог.txt > $P/лог.txt.gz
cp $D/знімки/kartka_poz*_ruka1_* $D/знімки/kartka_poz*_ruka2_* $P/ 2>/dev/null
echo "$M ${W}_${N} $(date +%T) $(du -sk $P | cut -f1) КБ" >> /tmp/fo/готово.txt
