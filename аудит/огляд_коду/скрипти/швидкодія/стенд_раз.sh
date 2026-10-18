#!/bin/sh
# Запуск: SP=<тека вимірів> sh стенд_раз.sh <номер>
# Потрібна копія аудит/проби/рв6_стенд.js → рв6_стенд_вимір.js з 4 вставками (її в репозиторії нема; склад — у швидкодія.md, рядок «стенд + інструмент»).
: "${SP:?задайте SP}"
cd $SP/wt
N=$1
uptime > $SP/прогони/стенд_$N.uptime
s=$(date +%s)
CHROMIUM=/opt/pw-browsers/chromium-1194/chrome-linux/chrome CHASY=1 CHASY_OUT=$SP/прогони/часи_$N.json VYMIR_OUT=$SP/прогони/вим_$N NODE_PATH=джерела/node_modules timeout 1500 node аудит/проби/рв6_стенд_вимір.js http://127.0.0.1:8765 $SP/стенд $SP/pyodide 3 > $SP/прогони/стенд_$N.log 2>&1
echo "rc $? $(( $(date +%s)-s )) s" >> $SP/прогони/стенд_$N.uptime
uptime >> $SP/прогони/стенд_$N.uptime
