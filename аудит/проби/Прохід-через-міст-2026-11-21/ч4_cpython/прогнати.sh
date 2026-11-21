#!/bin/sh
# Ч4 (Q10): повтор с5 і с8 із записів проходу без мережі → входи/виходи воркера → ті самі входи в CPython 3.12 і Pyodide (Node) → --діф.
# Потрібно: кеш Pyodide (`sh аудит/проби/стенд_pyodide_кеш.sh /tmp/pyodide`), Playwright у NODE_PATH, python3.12.
# Запуск з кореня репозиторію: sh аудит/проби/Прохід-через-міст-2026-11-21/ч4_cpython/прогнати.sh /tmp/ч4
set -eu
W=${1:-/tmp/ч4}; R=$(pwd); D=$R/аудит/проби/Прохід-через-міст-2026-11-21; C=$D/ч4_cpython; P=$R/джерела/прилади/знімок_мосту.py
mkdir -p "$W/стор" "$W/вих" "$W/зн"
for f in index.html build.txt збирання.txt; do git show 036e66f8:$f > "$W/стор/$f"; done   # збірка 2c9c872f = опублікована 21.11
unset http_proxy https_proxy; export HTTPS_PROXY=http://127.0.0.1:9 HTTP_PROXY=http://127.0.0.1:9   # мертвий проксі: мережі нема
export NODE_PATH=${NODE_PATH:-/opt/node-tools/node_modules} STOR="$W/стор" PYODIDE=${PYODIDE:-/tmp/pyodide} ONE_PASS=1
for PARA in с5_весілля_сестри:1280x800 с8_мінус_десять_сніг:390x844; do
  S=${PARA%%:*}; V=${PARA#*:}
  rm -rf "$W/вих/$S" "$W/вих/стенд/службове/$S"
  OBMINY=$D/стенд/службове/$S/обміни.jsonl VIEWPORT=$V node "$C/відтворення.js" "$S" "$W/вих" 0
  python3 -I "$C/входи_з_воркера.py" "$W/вих/стенд/службове/$S/воркер.jsonl" "$W/зн/${S}_входи.jsonl" "$W/зн/${S}_pyo_сторінка.jsonl"
  python3.12 -I "$P" cpython --сторінка "$W/стор/index.html" --входи "$W/зн/${S}_входи.jsonl" --вихід "$W/зн/${S}_cpy.jsonl"
  python3 -I "$P" pyodide --сторінка "$W/стор/index.html" --входи "$W/зн/${S}_входи.jsonl" --вихід "$W/зн/${S}_pyo_node.jsonl" --pyodide "$PYODIDE"
  python3 -I "$P" --діф "$W/зн/${S}_pyo_сторінка.jsonl" "$W/зн/${S}_cpy.jsonl"
  python3 -I "$P" --діф "$W/зн/${S}_pyo_node.jsonl" "$W/зн/${S}_cpy.jsonl"
done
