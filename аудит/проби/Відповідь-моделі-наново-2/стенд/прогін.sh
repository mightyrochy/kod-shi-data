#!/bin/bash
# Прогін «було — стало» наряду Відповідь-моделі-наново, крок 2: с8 і с5, по два проходи (скрипт-жінка з хід.md
# третього прогону), стенд четвертого прогону без змін (`аудит/проби/живий-як-людина-4/стенд/`: повтор.js, міст_claude.py).
# Запуск з кореня репозиторію: bash аудит/проби/Відповідь-моделі-наново-2/стенд/прогін.sh <до|після> <тека збірки STOR>
set -u
ROOT=$(pwd); HERE="$ROOT/аудит/проби/Відповідь-моделі-наново-2"; STAND="$ROOT/аудит/проби/живий-як-людина-4/стенд"
OUT="$HERE/$1"; mkdir -p "$OUT/стенд"
export STOR="$2" PYODIDE=${PYODIDE:-/tmp/pyodide} PRODUCT_MODEL=${PRODUCT_MODEL:-claude-sonnet-5-5} NODE_PATH=/opt/node-tools/node_modules
python3 -c "import socket;socket.create_connection(('127.0.0.1',8791),1)" 2>/dev/null || { (cd "$OUT/стенд" && nohup python3 "$STAND/міст_claude.py" 8791 журнал_моделі_продукту.jsonl 60 >> міст.лог 2>&1 &); sleep 2; }
for t in с8_мінус_десять_сніг с5_весілля_сестри; do
  rm -rf "${OUT:?}/$t" "${OUT:?}/стенд/службове/$t"
  echo "$(date -u +%H:%M:%S) старт $t"
  node "$STAND/повтор.js" "$t" "$OUT" 8791 > "$OUT/стенд/$t.лог" 2>&1
  echo "$(date -u +%H:%M:%S) кінець $t rc=$?"
done
pkill -f "_claude.py 8791" || true  # шаблон ASCII: pgrep у локалі C кирилиці не зіставляє
