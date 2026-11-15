#!/bin/bash
# Три воркери драйвера; фото сцени — /tmp/фото_сцен (головне фото ж-09444, як на ноутбуці), збірка — /tmp/стенд.
cd "$(dirname "$0")"
SHA=$1
for w in 0 1 2; do TEKA_FOTO_SCENY=/tmp/фото_сцен python3 драйвер.py $w 3 "$SHA" > драйвер_$w.log 2>&1 & done
wait
echo ВСЕ
