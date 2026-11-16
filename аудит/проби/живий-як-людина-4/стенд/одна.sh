#!/bin/bash
# Одна ситуація (скрипт-жінка із хід.md третього прогону): bash стенд/одна.sh <ситуація>  (з теки живий-як-людина-4).
# Міст — міст_claude.py на :8791, стеля $150 на суму журналу. Змінні: STOR=/tmp/стенд, PYODIDE=/tmp/pyodide, PRODUCT_MODEL.
cd "$(dirname "$0")/.."
export STOR=${STOR:-/tmp/стенд} PYODIDE=${PYODIDE:-/tmp/pyodide} PRODUCT_MODEL=${PRODUCT_MODEL:-claude-sonnet-5-5} NODE_PATH=/opt/node-tools/node_modules
python3 -c "import socket;socket.create_connection(('127.0.0.1',8791),1)" 2>/dev/null || { (cd стенд && nohup python3 міст_claude.py 8791 журнал_моделі_продукту.jsonl 150 >> міст.лог 2>&1 &); sleep 2; }
t=$1; rm -rf "$t" "стенд/службове/$t"
echo "$(date -u +%H:%M:%S) старт $t"
node стенд/повтор.js "$t" . 8791 > "стенд/$t.лог" 2>&1
echo "$(date -u +%H:%M:%S) кінець $t rc=$?"
