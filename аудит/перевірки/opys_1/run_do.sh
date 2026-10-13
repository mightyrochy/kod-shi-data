#!/bin/bash
# ОПИС-1: клітинки ДО — та сама обвʼязка (`rozbir_0210/one.sh`), але збірка main 37a2c52 до правки
# (/tmp/стенд_до, worktree /tmp/do_wt) і свої теки; дані — у ДО/
R=/home/user/kod-shi-data/аудит/перевірки/rozbir_0210
O=/home/user/kod-shi-data/аудит/перевірки/opys_1/ДО
for c in "$@"; do
  W=${c%%_*}; N=${c#*_}
  IFS='|' read -r W N T X <<< "$(grep "^$W|$N|" $R/cells.txt)"
  D=/tmp/rz/do_runs/${W}_${N}; rm -rf $D; mkdir -p $D
  (
    cd /tmp/do_wt
    export ZHYVA=sonnet FOTO=1 ZNIMKY=$D/знімки ZVIT_OUT=$D/вердикти.txt VIDPOVIDI=$D/VIDPOVIDI ZHINKA=/tmp/do_wt/аудит/проби/жінки/$W.json CHAT_TEXT="$T"
    for kv in $X; do k=${kv%%=*}; v=${kv#*=}; [ "$k" = ROZMOVA ] && v=$R/$v; export "$k=$v"; done
    CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node22/lib/node_modules timeout 3000 node аудит/проби/рв6_стенд.js http://127.0.0.1:8765 /tmp/стенд_до /tmp/pyodide 3 > $D/лог.txt 2>&1
  )
  S=$D; P=$O/${W}_${N}; mkdir -p $P
  cp $S/знімки/картки.txt $S/знімки/текст_екранів.txt $P/ 2>/dev/null
  gzip -c $S/вердикти.txt > $P/вердикти.txt.gz; gzip -c $S/лог.txt > $P/лог.txt.gz
  gzip -c $S/знімки/модель_виклики.json > $P/модель_виклики.json.gz 2>/dev/null
  tar czf $P/відповіді.tar.gz -C $S VIDPOVIDI
  cp $S/знімки/kartka_poz*_ruka1_* $S/знімки/kartka_poz*_ruka2_* $P/ 2>/dev/null
  echo "ДО ${W}_${N}: картки $( [ -s $P/картки.txt ] && echo є || echo НЕМА ) $(date +%T)" >> $O/../прогони_до.txt
done
