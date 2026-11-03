#!/bin/bash
# Послідовний запис сцен плану на дереві призначеного SHA. Чужу модель не чіпає: чекає звільнення.
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 NODE_PATH='C:\Users\Admin\kod-shi-test-node\node_modules'
B="$TEMP/збірка-6ddccfa5"; OUT="$1"; shift
for s in "$@"; do
  [ -e "$OUT/$s/результат.json" ] && continue
  while [ -n "$(lms ps | grep -E 'IDLE|PROCESSING|GENERATING|LOADING')" ]; do echo "$(date -u +%FT%TZ) чекаю звільнення моделей" >> "$OUT/done.txt"; sleep 30; done
  echo "$(date -u +%FT%TZ) початок $s" >> "$OUT/done.txt"
  if [ "$s" = ж1_робота ]; then export MODEL_VYBIR=assess; else unset MODEL_VYBIR; fi
  python "$B/аудит/проби/записати_сцену.py" "$B" 'C:\Users\Admin\stend-nout\pyodide' "$OUT/$s" --сцена "$s" > "$OUT/запис_$s.txt" 2>&1
  echo "$(date -u +%FT%TZ) кінець $s rc=$?" >> "$OUT/done.txt"
done
echo "$(date -u +%FT%TZ) УСЕ" >> "$OUT/done.txt"
