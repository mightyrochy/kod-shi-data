#!/bin/bash
cd /home/user/kod-shi-data
git fetch -q origin claude/rozbir-osnova claude/rozbir-prohony-2 claude/rozbir-prohony-3 claude/rozbir-prohony-4 2>/dev/null
for b in rozbir-osnova rozbir-prohony-2 rozbir-prohony-3 rozbir-prohony-4; do
  git -c core.quotepath=false ls-tree -d --name-only origin/claude/$b аудит/перевірки/rozbir_0210/ | sed 's|.*/||' | grep '^ж[0-9]_'
done | sort -u > /tmp/a6/have.txt
cut -d'|' -f1,2 аудит/перевірки/rozbir_0210/cells.txt | tr '|' '_' | sort -u > /tmp/a6/want.txt
comm -13 /tmp/a6/have.txt /tmp/a6/want.txt > /tmp/a6/missing.txt
wc -l < /tmp/a6/missing.txt
