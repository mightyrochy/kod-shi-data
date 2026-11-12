#!/bin/bash
# Усі 30 запитів серії 2 підряд, відновлювано (готові — з rc_секунд.txt — пропускає): bash уся_серія.sh
# сервер_claude.py на :8790, стеля $80 + $15 відкинутого прогону на суму журналу (стоп до $100)
cd "$(dirname "$0")"
python3 сервер_claude.py 8790 журнал_викликів.jsonl 80 > сервер.лог 2>&1 &
SRV=$!; sleep 2
for i in $(seq -w 1 30); do
  ls ${i}_*/rc_секунд.txt >/dev/null 2>&1 && continue
  rm -rf ${i}_*
  bash запуск.sh $i
  S=$(python3 -c "import json;print(sum((json.loads(l).get('usd') or 0) for l in open('журнал_викликів.jsonl') if l.strip()))")
  echo "сума \$$S після $i" >> прогрес.txt
  python3 -c "import sys;sys.exit(0 if float('$S')<80 else 1)" || { echo "СТЕЛЯ $S" >> прогрес.txt; break; }
done
kill $SRV; echo КІНЕЦЬ >> прогрес.txt
