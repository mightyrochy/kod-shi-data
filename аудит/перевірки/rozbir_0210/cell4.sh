#!/bin/bash
# $1 = рядок клітинки: прогін (до 3 спроб при rc≠0 чи «не дав result»), пак, коміт і пуш під замком
IFS='|' read -r W N T X <<< "$1"
R=/home/user/kod-shi-data/аудит/перевірки/rozbir_0210
for a in 1 2 3; do
  rm -rf /tmp/rz/runs/${W}_${N}
  bash $R/one.sh "$1"
  L=/tmp/rz/runs/${W}_${N}/лог.txt
  rc=$(tail -1 /tmp/rz/done.txt | grep -o "rc=[0-9]*")
  grep -q "не дав result" $L && rc=rc=bad
  [ "$rc" = rc=0 ] && break
  echo "спроба $a: $rc $W $N" >> $R/прогони_ж7ж8.txt
  grep -qi "limit\|ліміт" $L && sleep 600
done
(
  flock 9
  cd /home/user/kod-shi-data
  bash $R/pak.sh ${W}_${N}
  echo "${W}_${N}: $(tail -1 /tmp/rz/done.txt) · спроб $a · $(grep -c '✗' /tmp/rz/runs/${W}_${N}/лог.txt) ✗ у звірках" >> $R/прогони_ж7ж8.txt
  git add -A аудит/перевірки/rozbir_0210
  git commit -qm "Розбір 02.10: прогін ${W}_${N}

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_0173TNNK1L1nE3qefMQUMXwB"
  for t in 0 2 4 8 16; do sleep $t; git push -u origin claude/rozbir-prohony-4 -q 2>&1 && break || git pull --rebase -q origin claude/rozbir-prohony-4; done
) 9>/tmp/rz/git.lock
