#!/bin/bash
# Один запит проби: bash запуск.sh <№ 01–05> ; перед тим піднято сервер_claude.py на :8790 (журнал — журнал_викликів.jsonl)
# Змінні латиницею: bash кириличних імен не має.
set -u
cd "$(dirname "$0")"; ROOT=$(cd ../../.. && pwd)
N=$1
ROW=$(sed -n '/^```$/,/^```$/p' ../б1_доречність.md | grep '^б1_' | sed -n "$((10#$N))p")
ID=${ROW%%|*}; R=${ROW#*|}; W=${R%%|*}; R=${R#*|}; TXT=${R%|*}
D="$PWD/${N}_${ID}"; mkdir -p "$D/знімки" "$D/VIDPOVIDI"
echo "$ID|$W|$TXT" > "$D/вхід.txt"
t0=$(date +%s)
env MODEL=claude-sonnet-5-5 MODEL_MOVA=claude-sonnet-5-5 MODEL_URL=http://127.0.0.1:8790/v1 OTSINKA=0 FOTO=0 \
  CHAT_TEXT="$TXT" ZHINKA="$ROOT/аудит/проби/жінки/$W.json" VIDPOVIDI="$D/VIDPOVIDI" ZNIMKY="$D/знімки" \
  ZVIT_OUT="$D/вердикти.txt" SCENA="$ID" CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node-tools/node_modules \
  node "$ROOT/аудит/проби/рв6_стенд.js" http://127.0.0.1:8765 /tmp/стенд /tmp/pyodide 3 > "$D/лог.txt" 2>&1
rc=$?; t1=$(date +%s)
echo "$rc $((t1-t0))" > "$D/rc_секунд.txt"; echo "$N $ID rc=$rc с=$((t1-t0))"
