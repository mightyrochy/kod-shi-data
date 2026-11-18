#!/bin/bash
# Тестовий прогін наряду: ZHYVA=sonnet (адаптер claude -p самого стенда), три воркери, шість сцен «повне +фото».
cd "$(dirname "$0")"
SHA=$1
for w in 0 1 2; do ZHYVA=sonnet python3 драйвер.py $w 3 "$SHA" > драйвер_$w.log 2>&1 & done
wait
echo ВСЕ
