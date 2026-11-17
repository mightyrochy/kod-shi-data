#!/bin/bash
# Чотири воркери драйвера; збірка — /tmp/стенд (main <SHA>), Pyodide — /tmp/pyodide.
cd "$(dirname "$0")"
SHA=$1
for w in 0 1 2 3; do python3 драйвер.py $w 4 "$SHA" > драйвер_$w.log 2>&1 & done
wait
echo ВСЕ
