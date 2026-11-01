#!/bin/sh
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 NODE_PATH='C:\Users\Admin\kod-shi-test-node\node_modules'
B="$TEMP/збірка-9814a5ff"; D="$1"; K='C:\Users\Admin\stend-nout\pyodide'
cd "$B" || exit 9
run() {
  date -u +%FT%TZ > "$D/час_$1.txt"
  python "$B/аудит/проби/записати_сцену.py" "$B" "$K" "$D/$1" --сцена "$1" > "$D/запис_$1.txt" 2>&1
  echo "$1 rc=$? $(date -u +%FT%TZ)" >> "$D/done.txt"
  sleep 20
}
for s in ж7_вечеря_сьомій ж7_театр_дата ж3_кафе_13 ж3_кафе_20 ж8_ділова_мороз ж1_робота ж4_робота_стримано ж2_побачення_вечір ж3_співбесіда ж3_свято_др; do run $s; done
echo ALL >> "$D/done.txt"
