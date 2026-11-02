#!/bin/sh
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 NODE_PATH='C:\Users\Admin\kod-shi-test-node\node_modules'
B="$TEMP/збірка-b17e67c1"; D="$1"; K='C:\Users\Admin\stend-nout\pyodide'
cd "$B" || exit 9
for s in ж2_побачення_вечір ж3_співбесіда ж3_свято_др; do
  date -u +%FT%TZ > "$D/час_$s.txt"
  python "$B/аудит/проби/записати_сцену.py" "$B" "$K" "$D/$s" --сцена "$s" > "$D/запис_$s.txt" 2>&1
  echo "$s rc=$? $(date -u +%FT%TZ)" >> "$D/done.txt"
  sleep 15
done
echo ALL2 >> "$D/done.txt"
