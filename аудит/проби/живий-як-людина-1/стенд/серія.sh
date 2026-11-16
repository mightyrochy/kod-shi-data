#!/bin/bash
# Усі ситуації, по 3 одночасно, відновлювано: готова (є повідомлення.md) — пропуск; почата й обірвана — з початку
# (стан телефона в обірваному браузері втрачено). Міст — міст_claude.py на :8791, стеля $150 на суму журналу.
# Запуск: setsid nohup bash стенд/серія.sh > стенд/серія.лог 2>&1 &   (з теки живий-як-людина-1)
cd "$(dirname "$0")/.."
python3 -c "import socket;socket.create_connection(('127.0.0.1',8791),1)" 2>/dev/null || { (cd стенд && nohup python3 міст_claude.py 8791 журнал_моделі_продукту.jsonl 150 >> міст.лог 2>&1 &); sleep 2; }
один() {
  t=$1; [ -f "$t/повідомлення.md" ] && { echo "$t уже готова"; return; }
  rm -rf "$t/хід.md" "$t/знімки" "стенд/службове/$t" "$t"/*.json
  echo "$(date -u +%H:%M:%S) старт $t"
  NODE_PATH=/opt/node-tools/node_modules node стенд/людина.js "$t" 8791 320 > "стенд/$t.лог" 2>&1
  echo "$(date -u +%H:%M:%S) кінець $t rc=$?"
}
export -f один
ls -d с*_*/ | tr -d / | xargs -P 3 -I{} bash -c 'один {}'
echo КІНЕЦЬ
