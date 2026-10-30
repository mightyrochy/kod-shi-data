#!/bin/bash
# послідовний запуск живих сцен плану; кожна сцена — один раз
R=/c/Users/Admin/claude-run/w/20261030-093615-63bcc8795c63
cd $R/tmp/код-dedf9a11
export NODE_PATH='C:\Users\Admin\kod-shi-test-node\node_modules' PYTHONUTF8=1 PYTHONIOENCODING=utf-8 NODE_USE_SYSTEM_CA=1 LYUSTERKO_CATALOG=повний LYUSTERKO_PYC_PYTHON='C:\Users\Admin\py3121\python.exe'
export PATH="/c/Program Files/nodejs:$PATH"
OUT=$R/repo/аудит/проби/автоживий-f128add252f4df28f994ddb8162af5cd7c6e5fb4
for s in "$@"; do
  if [ -e "$OUT/$s/done.txt" ]; then echo "пропуск $s"; continue; fi
  if [ "$s" = ж2_корпоратив_виділитися ] || [ "$s" = ж6_робота_комплементарна ]; then P=записати_сцену_режим.py; else P=записати_сцену.py; fi
  echo "$(date -u +%FT%TZ) старт $s"
  python -X utf8 аудит/проби/$P 'C:\Users\Admin\claude-run\w\20261030-093615-63bcc8795c63\tmp\стенд' 'C:\Users\Admin\stend-nout\pyodide' "$(cygpath -w "$OUT/$s")" --сцена $s > $OUT/$s.out 2>&1
  rc=$?
  echo "$(date -u +%FT%TZ) $s rc=$rc" | tee -a $OUT/done-ланцюг.txt
  [ -d "$OUT/$s" ] && echo "$(date -u +%FT%TZ) $s rc=$rc" > "$OUT/$s/done.txt"
done
