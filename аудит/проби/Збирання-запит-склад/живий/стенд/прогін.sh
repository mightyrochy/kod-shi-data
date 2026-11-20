#!/bin/bash
# ПІСЛЯ наряду `Збирання-запит-склад`: стенд за підпискою (міст_claude.py з живий-як-людина-4), с8 і с5 по черзі,
# скрипт-жінка — той самий, що ДО (живий-як-людина-4/стенд/повтор.js). Вихід — ця тека. Запуск з кореня репозиторію.
cd "$(dirname "$0")/.."
S=../../живий-як-людина-4/стенд
export STOR=${STOR:-/tmp/стенд} PYODIDE=${PYODIDE:-/tmp/pyodide} PRODUCT_MODEL=${PRODUCT_MODEL:-claude-sonnet-5-5} NODE_PATH=/opt/node-tools/node_modules
python3 -c "import socket;socket.create_connection(('127.0.0.1',8791),1)" 2>/dev/null || { nohup python3 $S/міст_claude.py 8791 стенд/журнал_моделі_продукту.jsonl 150 >> стенд/міст.лог 2>&1 & sleep 2; }
for t in с8_мінус_десять_сніг с5_весілля_сестри; do
  echo "$(date -u +%H:%M:%S) старт $t"
  node $S/повтор.js "$t" . 8791 > "стенд/$t.лог" 2>&1; echo "$(date -u +%H:%M:%S) кінець $t rc=$?"
done
pkill -f "міст_claude.py 8791" || true
