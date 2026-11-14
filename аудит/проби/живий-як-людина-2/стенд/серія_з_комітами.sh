#!/bin/bash
# Коміт і пуш після кожної завершеної ситуації серії (серія.sh запущено окремо).
cd "$(dirname "$0")/.."; R=$(git rev-parse --show-toplevel)
уже=с4_побачення_19_30
while true; do
  for t in с?_*/; do t=${t%/}
    [ -f "$t/повідомлення.md" ] || continue; case "$уже" in *"$t"*) continue;; esac
    sleep 3; gzip -f "стенд/службове/$t/обміни.jsonl" 2>/dev/null
    (cd "$R" && git add аудит/проби/живий-як-людина-2 && git commit -q -m "Живий-як-людина-2: $t, два проходи

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01FPQuiakbM21KZgeS4BTMCW" && for i in 1 2 3 4; do git push -q origin claude/zhyvyi-yak-liudyna-2 && break; sleep 5; done)
    уже="$уже"$'\n'"$t"; echo "$(date -u +%H:%M:%S) закомічено $t" >> стенд/коміти.лог
  done
  [ "$(wc -l <<<"$уже")" -ge 8 ] && break
  sleep 30
done
echo ГОТОВО >> стенд/коміти.лог
