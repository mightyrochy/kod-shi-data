#!/bin/bash
# $1 = вихідна тека, далі сцени; $STOR — збірка
OUT=$1; shift; mkdir -p $OUT
cd /tmp/n2/tree782/аудит/проби/Живий-через-міст/стенд
for SC in "$@"; do
  echo "$(date -u +%FT%TZ) старт $SC" >> $OUT/хід_прогону.txt
  CLAUDE_MODEL=claude-sonnet-5-5 python3 /tmp/n2/міст_н2.py 8787 $OUT/міст_$SC.jsonl 20 > $OUT/міст_$SC.stderr 2>&1 &
  МП=$!
  python3 -c "
import socket,time
for i in range(100):
    try: socket.create_connection(('127.0.0.1',8787),1).close(); break
    except OSError: time.sleep(0.2)"
  env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy STOR=${STOR:-/tmp/n2/stor782} PYODIDE=/tmp/n2/pyodide \
    NODE_PATH=/opt/node-tools/node_modules CHROMIUM=/opt/pw-browsers/chromium MIST_LOCAL=http://127.0.0.1:8787 ONE_PASS=1 \
    YADRO=${YADRO-1} VIKNO_N2=${VIKNO_N2-1000000} timeout 3600 node повтор_н2.js $SC $OUT 0 > $OUT/повтор_$SC.log 2>&1
  echo "$(date -u +%FT%TZ) кінець $SC rc=$?" >> $OUT/хід_прогону.txt
  kill $МП; wait $МП 2>/dev/null
done
