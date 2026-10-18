#!/bin/sh
# Проганяє сцени зі `сцени.txt` під обгорткою виміру. Запуск з кореня репозиторію:
#   sh аудит/огляд_коду/скрипти/показ/прогін.sh <тека стенда з index.html> <тека pyodide> <вихід> [сцена…]
# Зібрати index.html: (cd джерела && LYUSTERKO_CATALOG=повний python3 build_артефакт.py . <тека>/index.html показ-повний)
set -u
STEND="$1"; PYO="$2"; OUT="$3"; shift 3
DIR=$(dirname "$0")
grep -v '^#' "$DIR/сцени.txt" | while IFS='|' read -r NAME VARS; do
  [ -z "$NAME" ] && continue
  if [ $# -gt 0 ] && ! echo " $* " | grep -q " $NAME "; then continue; fi
  rm -rf "$OUT/$NAME"; mkdir -p "$OUT/$NAME"
  T0=$(date +%s)
  env $VARS CHROMIUM="${CHROMIUM:-/opt/pw-browsers/chromium}" NODE_PATH=джерела/node_modules \
    node "$DIR/обгортка_стенда.js" "$OUT/$NAME" http://127.0.0.1:8773 "$STEND" "$PYO" 3 > "$OUT/$NAME.log" 2>&1
  RC=$?
  echo "$NAME rc=$RC $(( $(date +%s) - T0 ))с ✔$(grep -c '^  ✔' "$OUT/$NAME.log") ✗$(grep -c '^  ✗' "$OUT/$NAME.log")"
done
