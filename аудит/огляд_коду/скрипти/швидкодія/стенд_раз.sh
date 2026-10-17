#!/bin/sh
# Запуск: sh стенд_раз.sh <номер>
cd /tmp/claude-0/-home-user-kod-shi-data/66b2c79f-d82f-57ad-bcfa-0413f82df806/scratchpad/D/wt
N=$1
uptime > /tmp/claude-0/-home-user-kod-shi-data/66b2c79f-d82f-57ad-bcfa-0413f82df806/scratchpad/D/прогони/стенд_$N.uptime
s=$(date +%s)
CHROMIUM=/opt/pw-browsers/chromium-1194/chrome-linux/chrome CHASY=1 CHASY_OUT=/tmp/claude-0/-home-user-kod-shi-data/66b2c79f-d82f-57ad-bcfa-0413f82df806/scratchpad/D/прогони/часи_$N.json VYMIR_OUT=/tmp/claude-0/-home-user-kod-shi-data/66b2c79f-d82f-57ad-bcfa-0413f82df806/scratchpad/D/прогони/вим_$N NODE_PATH=джерела/node_modules timeout 1500 node аудит/проби/рв6_стенд_вимір.js http://127.0.0.1:8765 /tmp/claude-0/-home-user-kod-shi-data/66b2c79f-d82f-57ad-bcfa-0413f82df806/scratchpad/D/стенд /tmp/claude-0/-home-user-kod-shi-data/66b2c79f-d82f-57ad-bcfa-0413f82df806/scratchpad/D/pyodide 3 > /tmp/claude-0/-home-user-kod-shi-data/66b2c79f-d82f-57ad-bcfa-0413f82df806/scratchpad/D/прогони/стенд_$N.log 2>&1
echo "rc $? $(( $(date +%s)-s )) s" >> /tmp/claude-0/-home-user-kod-shi-data/66b2c79f-d82f-57ad-bcfa-0413f82df806/scratchpad/D/прогони/стенд_$N.uptime
uptime >> /tmp/claude-0/-home-user-kod-shi-data/66b2c79f-d82f-57ad-bcfa-0413f82df806/scratchpad/D/прогони/стенд_$N.uptime
