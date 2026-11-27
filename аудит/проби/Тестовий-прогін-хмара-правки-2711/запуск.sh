#!/bin/bash
# ZHYVA=sonnet, чотири воркери; збірка — /tmp/стенд/index.html (index.html коміту збірки), Pyodide — /tmp/pyodide.
cd "$(dirname "$0")"
for w in 0 1 2 3; do python3 драйвер.py $w 4 "$1" > драйвер_$w.log 2>&1 & done
wait
echo ВСЕ
