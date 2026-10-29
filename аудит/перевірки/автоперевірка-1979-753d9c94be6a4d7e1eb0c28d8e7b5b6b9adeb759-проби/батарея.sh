#!/bin/bash
# Батарея КОД.md на голові + сім'я pal_* на голові й базі; коди виходу в підсумок.
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 NODE_PATH='C:\Users\Admin\kod-shi-test-node\node_modules'
export PATH="$PATH:/c/Users/Admin/.lmstudio/.internal/utils"
O=/tmp/pr1979/батарея; mkdir -p $O
cd /tmp/pr1979/head/джерела
for k in "python стенд_знімок.py --дим" "python тест_живого_шляху.py" "python тест_протоколу.py" "python прилади/розділи_гейтів.py" "python audit_contracts.py" "node тест_показу.js"; do
  n=$(echo "$k" | tr ' /' '__'); $k > "$O/$n.txt" 2>&1; echo "head | $k | rc=$?" >> $O/підсумок.txt
done
for t in head base; do
  cd /tmp/pr1979/$t/джерела
  for f in проби/pal_*.py; do
    case "$f" in *pal_вердикт.py|*pal_вимір.py) continue;; esac
    timeout 900 python "$f" > "$O/${t}_$(basename $f).txt" 2>&1; echo "$t | $f | rc=$?" >> $O/підсумок.txt
  done
done
echo ГОТОВО >> $O/підсумок.txt
