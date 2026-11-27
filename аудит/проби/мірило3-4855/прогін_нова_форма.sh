#!/bin/bash
# Те саме, що Збирання-запит-склад/межа_пулу/прогін.sh, але кроки жінки — повтор_вимір_нова_форма.js. З кореня: bash <цей> <тека виходу>
P=$(realpath "$(dirname "$0")/../Збирання-запит-склад/межа_пулу"); N=$(realpath "$(dirname "$0")")
OUT=$(realpath -m "${1:?тека виходу}"); mkdir -p "$OUT/стенд"
export STOR=${STOR:-/tmp/стенд-вим} PYODIDE=${PYODIDE:-/tmp/pyodide} PRODUCT_MODEL=claude-sonnet-5-5 NODE_PATH=/opt/node-tools/node_modules
PORT=${PORT:-8792}
(cd "$P" && python3 міст_запис.py $PORT "$OUT/журнал_моста.jsonl" >> "$OUT/стенд/міст.лог" 2>&1) & M=$!
sleep 1
t=${SCENE:-с5_весілля_сестри}
echo "$(date -u +%H:%M:%S) старт $t"
(cd "$N" && node повтор_вимір_нова_форма.js "$t" "$OUT" $PORT > "$OUT/стенд/$t.лог" 2>&1); echo "$(date -u +%H:%M:%S) кінець $t rc=$?"
kill $M
