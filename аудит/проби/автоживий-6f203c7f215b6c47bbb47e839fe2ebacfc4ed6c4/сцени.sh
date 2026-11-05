#!/bin/sh
# Послідовний запис сцен плану на тимчасовому дереві збірки (команди — як у цьому файлі).
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 NODE_PATH='C:\Users\Admin\kod-shi-test-node\node_modules'
B="$TEMP/збірка-b17e67c1"; D="$1"; K='C:\Users\Admin\stend-nout\pyodide'
cd "$B" || exit 9
run() { # скрипт сцена
  date -u +%FT%TZ > "$D/час_$2.txt"
  python "$B/аудит/проби/$1" "$B" "$K" "$D/$2" --сцена "$2" > "$D/запис_$2.txt" 2>&1
  echo "$2 rc=$? $(date -u +%FT%TZ)" >> "$D/done.txt"
}
run записати_сцену_ж1_6б.py ж1_оціни_образ_6б
run записати_сцену.py ж2_побачення_вечір
run записати_сцену.py ж3_співбесіда
run записати_сцену.py ж3_свято_др
echo ALL >> "$D/done.txt"
