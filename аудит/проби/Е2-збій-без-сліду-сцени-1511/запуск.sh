#!/bin/bash
# Три воркери драйвера, як у прогоні Корені-нуль-живе-мірило-1511; збірка — /tmp/стенд (main <SHA>).
cd "$(dirname "$0")"
SHA=$1
for w in 0 1 2; do TEKA_FOTO_SCENY=/tmp/фото_сцен python3 драйвер.py $w 3 "$SHA" > драйвер_$w.log 2>&1 & done
wait
echo ВСЕ
