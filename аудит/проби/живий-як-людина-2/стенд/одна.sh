#!/bin/bash
# Одна ситуація (пробна): bash стенд/одна.sh <тека ситуації>  (з теки живий-як-людина-2). Міст — як у серія.sh.
cd "$(dirname "$0")/.."
python3 -c "import socket;socket.create_connection(('127.0.0.1',8791),1)" 2>/dev/null || { (cd стенд && nohup python3 міст_claude.py 8791 журнал_моделі_продукту.jsonl 150 >> міст.лог 2>&1 &); sleep 2; }
t=$1; rm -rf "$t/хід.md" "$t/знімки" "стенд/службове/$t" "$t"/*.json "$t/повідомлення.md"
echo "$(date -u +%H:%M:%S) старт $t"
NODE_PATH=/opt/node-tools/node_modules node стенд/людина.js "$t" 8791 320 > "стенд/$t.лог" 2>&1
echo "$(date -u +%H:%M:%S) кінець $t rc=$?"
