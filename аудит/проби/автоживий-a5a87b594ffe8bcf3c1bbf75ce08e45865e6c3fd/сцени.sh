#!/bin/sh
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 NODE_PATH='C:\Users\Admin\kod-shi-test-node\node_modules'
B="$TEMP/збірка-6f4b96e6"; D="$1"; K='C:\Users\Admin\stend-nout\pyodide'
cd "$B" || exit 9
run() {
  date -u +%FT%TZ > "$D/час_$1.txt"
  python "$B/аудит/проби/записати_сцену.py" "$B" "$K" "$D/$1" --сцена "$1" > "$D/запис_$1.txt" 2>&1
  echo "$1 rc=$? $(date -u +%FT%TZ)" >> "$D/done.txt"
  sleep 20
}
run ж1_оціни_образ_6б
run ж2_побачення_вечір
run ж3_співбесіда
run ж3_свято_др
run ж1_робота
echo ALL >> "$D/done.txt"
