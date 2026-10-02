#!/bin/bash
# ОПИС-1: клітинки ПІСЛЯ тією самою обв'язкою розбору 02.10 (`rozbir_0210/one.sh`), дані — у ПІСЛЯ/
R=/home/user/kod-shi-data/аудит/перевірки/rozbir_0210
O=/home/user/kod-shi-data/аудит/перевірки/opys_1/ПІСЛЯ
run(){
  W=${1%%_*}; N=${1#*_}
  L=$(grep "^$W|$N|" $R/cells.txt)
  for a in 1 2; do
    rm -rf /tmp/rz/runs/${W}_${N}
    bash $R/one.sh "$L"
    [ -s /tmp/rz/runs/${W}_${N}/знімки/картки.txt ] && [ -s /tmp/rz/runs/${W}_${N}/вердикти.txt ] && break
  done
  rm -rf $O/${W}_${N}; bash $O/../pak.sh ${W}_${N} >/dev/null 2>&1
  echo "${W}_${N}: $(tail -1 /tmp/rz/done.txt) · спроб $a" >> $O/../прогони.txt
}
for c in "$@"; do run "$c"; done
