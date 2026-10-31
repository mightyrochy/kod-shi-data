#!/bin/sh
# Послідовний запис сцен плану на збірці 7f073d17 (поточне дерево).
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 NODE_PATH='C:\Users\Admin\kod-shi-test-node\node_modules'
B="$(pwd)"; D="$1"; K='C:\Users\Admin\stend-nout\pyodide'
run() {
  date -u +%FT%TZ > "$D/час_$1.txt"
  python "$B/аудит/проби/записати_сцену.py" "$B" "$K" "$D/$1" --сцена "$1" > "$D/запис_$1.txt" 2>&1
  echo "$1 rc=$? $(date -u +%FT%TZ)" >> "$D/done.txt"
}
for s in "$@"; do [ "$s" = "$D" ] || run "$s"; done
echo ALL >> "$D/done.txt"
